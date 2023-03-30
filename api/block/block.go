package block

import (
	"bytes"
	"context"
	"encoding/json"
	"io/ioutil"
	"net/http"
	"os"
	"strings"

	"github.com/example/orchestrator/core/block"
	"github.com/example/ramen/pkg/logger"
	"sigs.k8s.io/yaml"
)

type WorkflowAPIRequest struct {
	Spec block.Block `json:"spec"`
}

func getUrl() string {
	url := os.Getenv("DEXTER_BLOCK_URL")
	var blockURL string
	if strings.HasSuffix(url, "/") {
		blockURL = url + "blocks"
	} else {
		blockURL = url + "/blocks"
	}
	return blockURL

}

func CreateNewBlock(ctx context.Context, logger *logger.Logger, specFilePath string) error {

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
	url := getUrl()
	resp, err := http.Post(url, "application/json", data)

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
	logger.Info().Msgf("Block is updated successfully with response as: %s", string(body))
	return nil
}
