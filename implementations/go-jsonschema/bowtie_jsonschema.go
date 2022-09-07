package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"github.com/santhosh-tekuri/jsonschema/v5"
	"log"
	"os"
)

func main() {

	var started = false

	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		var request map[string]interface{}
		err := json.Unmarshal([]byte(scanner.Text()), &request)
		if err != nil {
			fmt.Printf("could not unmarshal json: %s\n", err)
			return
		}
		encoder := json.NewEncoder(os.Stdout)
		switch request["cmd"] {
		case "start":
			started = true
			rawVersion, ok := request["version"]
			if !ok {
				panic("No version!")
			}
			version := rawVersion.(float64)
			if version != 1 {
				panic("Not version 1!")
			}
			data := map[string]interface{}{
				"ready":   true,
				"version": 1,
			}

			if err := encoder.Encode(&data); err != nil {
				panic("Failed sending a response!")
			}
		case "run":
			if !started {
				panic("Not started!")
			}
			testCase, ok := request["case"].(map[string]interface{})
			if !ok {
				panic("No case!")
			}

			// FIXME: map[string].interface{} -> Schema?
			reserialized, err := json.Marshal(testCase["schema"])
			if err != nil {
				panic("This should never happen.")
			}
			// Base URL?
			schema, err := jsonschema.CompileString("", string(reserialized))
			if err != nil {
				fmt.Fprintf(os.Stderr, "%#v\n", err)
				os.Exit(1)
			}

			var results []map[string]interface{}

			for _, v := range testCase["tests"].([]interface{}) {
				err := schema.Validate(v.(map[string]interface{})["instance"])
				result := map[string]interface{}{
					"valid": err == nil,
				}
				results = append(results, result)
			}
			data := map[string]interface{}{
				"seq":     request["seq"],
				"results": results,
			}
			if err := encoder.Encode(&data); err != nil {
				panic("Failed sending a response!")
			}

		case "stop":
			if !started {
				panic("Not started!")
			}
			os.Exit(0)
		default:
			panic("Unknown command")
		}
	}

	if err := scanner.Err(); err != nil {
		log.Println(err)
	}
}
