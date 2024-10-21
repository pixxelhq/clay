package main

import (
	"log"
	"registry/api/http"
	"sync"
)

// @title				Clay Registry
// @version				1.0.0
// @host				localhost:8080
// @contact.name		MLOps team
// @contact.email		mlops@pixxel.co.in
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
