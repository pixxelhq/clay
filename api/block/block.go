package block

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"strings"

	"github.com/Masterminds/semver/v3"
	"github.com/example/clay/cmd/common"
	"github.com/example/clay/pkg"
	"github.com/example/clay/pkg/logger"
	"github.com/example/orchestrator/core/block"
	"sigs.k8s.io/yaml"
)

type WorkflowAPIRequest struct {
	Spec block.Block `json:"spec"`
}

type UpdateAPIRequest struct {
	Spec json.RawMessage `json:"spec"`
}

type BlockSpec struct {
	Data []struct {
		Spec block.Block `json:"spec"`
	} `json:"data"`
}

func getToken(email string, password string) (string, error) {
	const tokenUrl = "https://p-platform-gateway.example.com/accounts/api/auth/token/"

	client := &http.Client{}

	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)
	writer.WriteField("email", email)
	writer.WriteField("password", password)
	writer.Close()

	req, err := http.NewRequest("POST", tokenUrl, body)
	if err != nil {
		return "", err
	}

	req.Header.Set("Content-Type", writer.FormDataContentType())

	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}

	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}

	var tokenResp map[string]string
	err = json.Unmarshal(respBody, &tokenResp)
	if err != nil {
		return "", err
	}

	if tokenResp["access"] == "" {
		err := errors.New(string(respBody))
		return "", err
	} else {
		accessToken := tokenResp["access"]
		authHeader := "Bearer " + accessToken
		return authHeader, nil
	}

}

func buildURL(blockUrl string, endpoint string) string {

	var relativeURL string
	if strings.HasSuffix(blockUrl, "/") {
		relativeURL = "blocks/"
	} else {
		relativeURL = "/blocks/"
	}
	return blockUrl + relativeURL + endpoint
}
func sendRequest(email string, password string, method string, blockUrl string, data io.Reader) ([]byte, int, error) {

	bearer, err := getToken(email, password)

	if err != nil {
		return []byte{}, 0, err

	}

	req, err := http.NewRequest(method, blockUrl, data)

	if err != nil {
		return []byte{}, 0, err
	}

	req.Header.Add("Authorization", bearer)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)

	if err != nil {
		return []byte{}, 0, err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return []byte{}, 0, err
	}
	return body, resp.StatusCode, nil
}

func PostNewBlock(ctx context.Context, logger *logger.Logger, specFilePath string, email string, password string, env string) error {

	specBytes, err := os.ReadFile(specFilePath)
	if err != nil {
		logger.Error().Err(err).Msgf("Spec file not found at path %s", specFilePath)
		return err
	}

	var blockStruct block.Block

	err = yaml.Unmarshal(specBytes, &blockStruct)
	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return err
	}

	updatedBlockSpec := WorkflowAPIRequest{Spec: blockStruct}
	blockJSON, err := json.Marshal(updatedBlockSpec)
	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return err
	}
	data := bytes.NewBuffer(blockJSON)

	dexterUrl := common.GetUrl(env)

	if dexterUrl == "" {
		return pkg.ErrInvalidValue("invalid env")
	}

	blockUrl := buildURL(dexterUrl, "")

	body, statuscode, err := sendRequest(email, password, "POST", blockUrl, data)
	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return err
	}

	if statuscode >= 200 && statuscode < 300 {
		logger.Info().Msgf("block is updated successfully: \nstatus code: %d \nrespose:%s", statuscode, string(body))
		return nil
	} else {
		logger.Info().Msgf("could not update block: %s", body)
		err := fmt.Errorf("could not update block: \nstatus code %d %s", statuscode, body)
		return err
	}
}

func ListBlock(ctx context.Context, logger *logger.Logger, email string, password string, env string, status string) (BlockSpec, error) {

	dexterUrl := common.GetUrl(env)
	if dexterUrl == "" {
		return BlockSpec{}, pkg.ErrInvalidValue("invalid env")
	}

	blockUrl := buildURL(dexterUrl, fmt.Sprintf("?status=%s", status))
	body, statuscode, err := sendRequest(email, password, "GET", blockUrl, nil)
	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return BlockSpec{}, err
	}
	if statuscode >= 400 && statuscode < 500 {
		logger.Info().Msgf("cannot complete request: \nstatus code: %d \nrespose:%s", statuscode, string(body))
		return BlockSpec{}, common.NewUnauthorisedError("cannot complete request")
	}
	var tmpVar BlockSpec
	err = json.Unmarshal(body, &tmpVar)
	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return BlockSpec{}, err
	}
	return tmpVar, nil
}

func ListVersion(ctx context.Context, logger *logger.Logger, blockname string, email string, password string, env string, status string) (BlockSpec, error) {

	dexterUrl := common.GetUrl(env)
	if dexterUrl == "" {
		return BlockSpec{}, pkg.ErrInvalidValue("invalid env")
	}

	blockUrl := buildURL(dexterUrl, fmt.Sprintf("%s/versions?status=%s", blockname, status))

	body, statuscode, err := sendRequest(email, password, "GET", blockUrl, nil)
	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return BlockSpec{}, err
	}

	if statuscode >= 400 && statuscode < 500 {
		logger.Info().Msgf("cannot complete request: \nstatus code: %d \nrespose:%s", statuscode, string(body))
		return BlockSpec{}, common.NewUnauthorisedError("cannot complete request")
	}

	var tmpVar BlockSpec
	err = json.Unmarshal([]byte(body), &tmpVar)
	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return BlockSpec{}, err
	}
	return tmpVar, nil
}

func GetBlock(ctx context.Context, logger *logger.Logger, blockname string, version string, email string, password string, env string, status string) ([]byte, error) {

	specc, err := ListVersion(ctx, logger, blockname, email, password, env, status)
	if err != nil {
		return nil, err
	}
	semversion, err := semver.NewVersion(version)

	if err != nil {
		fmt.Println("Error parsing version:", err)
		logger.Error().Err(err).Stack().Msg(err.Error())
		return nil, err
	}

	for _, block := range specc.Data {
		if block.Spec.Version.V.Equal(semversion) {
			jsonData, err := json.Marshal(block)
			if err != nil {
				logger.Error().Err(err).Stack().Msg(err.Error())
				return nil, err
			}
			return jsonData, nil
		}
	}
	return nil, nil
}

func UpdateBlock(ctx context.Context, logger *logger.Logger, blockname string, version string, specFilePath string, email string, password string, env string, status string) error {

	jsonData, err := GetBlock(ctx, logger, blockname, version, email, password, env, status)
	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return err
	}
	if jsonData == nil {
		fmt.Println("No block found for the given details")
		return nil
	}
	var tmpVar WorkflowAPIRequest
	err = json.Unmarshal(jsonData, &tmpVar)
	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return err
	}

	//blockID required to update block in orchestrator
	blockId := tmpVar.Spec.Id
	specBytes, err := os.ReadFile(specFilePath)
	if err != nil {
		logger.Error().Err(err).Msgf("Spec file not found at path %s", specFilePath)
		return err
	}

	blockStruct := json.RawMessage{}

	err = yaml.Unmarshal(specBytes, &blockStruct)
	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return err
	}

	//add spec key before sending POST request

	updatedBlockSpec := UpdateAPIRequest{Spec: blockStruct}

	blockJSON, err := json.Marshal(updatedBlockSpec)
	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return err
	}
	data := bytes.NewBuffer(blockJSON)
	dexterUrl := common.GetUrl(env)

	blockUrl := buildURL(dexterUrl, fmt.Sprintf("%s?status=%s", blockId, status))

	body, statuscode, err := sendRequest(email, password, "PUT", blockUrl, data)
	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return err
	}

	if statuscode >= 200 && statuscode < 300 {
		logger.Info().Msgf("block is updated successfully: \nstatus code: %d \nrespose:%s", statuscode, string(body))
		return nil
	} else {
		logger.Info().Msgf("could not update block: %s", body)
		err := fmt.Errorf("could not update block: \nstatus code %d %s", statuscode, body)
		return err
	}
}
