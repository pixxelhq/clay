package block

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"mime/multipart"
	"net/http"

	"github.com/example/clay/pkg/logger"
	"github.com/example/orchestrator/core/block"
	"sigs.k8s.io/yaml"
)

type WorkflowAPIRequest struct {
	Spec block.Block `json:"spec"`
}

func getToken(email string, password string) (string, error) {
	url := "https://accounts.example.com/api/auth/token/"

	client := &http.Client{}

	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)
	writer.WriteField("email", email)
	writer.WriteField("password", password)
	writer.Close()

	req, err := http.NewRequest("POST", url, body)
	if err != nil {
		return "", err
	}

	req.Header.Set("Content-Type", writer.FormDataContentType())

	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}

	defer resp.Body.Close()

	respBody, err := ioutil.ReadAll(resp.Body)
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

func PostNewBlock(ctx context.Context, logger *logger.Logger, specFilePath string, email string, password string) error {

	specBytes, err := ioutil.ReadFile(specFilePath)
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

	//add spec key before sending POST request

	updatedBlockSpec := WorkflowAPIRequest{Spec: blockStruct}
	blockJSON, err := json.Marshal(updatedBlockSpec)
	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return err
	}
	data := bytes.NewBuffer(blockJSON)

	url := "https://orchestrator.dev.example.com/blocks/"
	bearer, err := getToken(email, password)

	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return err
	}

	req, err := http.NewRequest("POST", url, data)

	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return err
	}

	req.Header.Add("Authorization", bearer)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)

	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return err
	}

	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		logger.Error().Err(err).Stack().Msg(err.Error())
		return err
	}
	statuscode := int(resp.StatusCode)
	if statuscode >= 200 && statuscode < 300 {
		logger.Info().Msgf("block is updated successfully: \nstatus code: %d \nrespose:%s", statuscode, string(body))
		return nil
	} else {
		logger.Info().Msgf("could not update block: %s", body)
		err := fmt.Errorf("could not update block: \nstatus code %d %s", statuscode, body)
		return err
	}

}
