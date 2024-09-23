package main

import (
	"log"
	"registry/api/http"
	"sync"
)

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
