package main

import (
	"log"
	"sync"

	"github.com/pixxelhq/clay-framework/registry/api/http"

	_ "github.com/pixxelhq/clay-framework/registry/api_docs" // Swagger docs
)

// @title				Clay Registry
// @version				1.0
// @description			HTTP API for the Clay block registry.
// @license.name		Apache 2.0
// @license.url			https://www.apache.org/licenses/LICENSE-2.0.html
// @host				localhost:8080
func main() {
	errCh := make(chan error, 1)
	wg := sync.WaitGroup{}

	httpSvr := http.NewServer()
	httpSvr.Init()

	go func() {
		err := httpSvr.Start()
		errCh <- err
		wg.Done()
	}()

	err := <-errCh
	if err != nil {
		log.Fatal(err)
	}
}
