// Copyright Amazon.com Inc. or its affiliates.
// 
// SPDX-License-Identifier: MIT No Attribution(MIT-0)
//
// Permission is hereby granted, free of charge, to any person obtaining a copy of
// this software and associated documentation files (the "Software"), to deal in the
// Software without restriction, including without limitation the rights to use, 
// copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
// Software, and to permit persons to whom the Software is furnished to do so.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
// INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
// PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
// HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
// OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
// SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


package main

import (
	"fmt"
	"log"
	"runtime"
	"os"
	"net/http"

	"github.com/gorilla/mux"
)

// our main function
func main() {
	router := mux.NewRouter()
	router.HandleFunc("/", GetHelloWorld).Methods("GET")
	log.Fatal(http.ListenAndServe("0.0.0.0:8080", router))
}

func GetHelloWorld(w http.ResponseWriter, r *http.Request) {
	nodeName := os.Getenv("nodeName")
	cpuArch := runtime.GOARCH

        outputText := "Hello there!!!\nI'm running on {cpuArch: " +  
	             cpuArch + ", nodeName: " + nodeName + "}\n"

	fmt.Fprintf(w, outputText)
}
