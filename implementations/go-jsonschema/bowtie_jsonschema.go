package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"github.com/santhosh-tekuri/jsonschema/v5"
	"io"
	"log"
	"os"
	"strings"
)

var drafts = map[string]*jsonschema.Draft{
	"https://json-schema.org/draft/2020-12/schema": jsonschema.Draft2020,
	"https://json-schema.org/draft/2019-09/schema": jsonschema.Draft2019,
	"http://json-schema.org/draft-07/schema#":      jsonschema.Draft7,
	"http://json-schema.org/draft-06/schema#":      jsonschema.Draft6,
	"http://json-schema.org/draft-04/schema#":      jsonschema.Draft4,
}

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
		compiler := jsonschema.NewCompiler()
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
				"implementation": map[string]interface{}{
					"language": "go",
					"name":     "jsonschema",
					"homepage": "https://github.com/santhosh-tekuri/jsonschema",
					"issues":   "https://github.com/santhosh-tekuri/jsonschema/issues",

					"dialects": []string{
						"https://json-schema.org/draft/2020-12/schema",
						"https://json-schema.org/draft/2019-09/schema",
						"http://json-schema.org/draft-07/schema#",
						"http://json-schema.org/draft-06/schema#",
						"http://json-schema.org/draft-04/schema#",
					},
				},
			}

			if err := encoder.Encode(&data); err != nil {
				panic("Failed sending a response!")
			}
		case "dialect":
			if !started {
				panic("Not started!")
			}
			rawDialect, ok := request["dialect"]
			if !ok {
				panic("No dialect!")
			}
			dialect := rawDialect.(string)
			compiler.Draft = drafts[dialect]
			data := map[string]interface{}{"ok": true}
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

			jsonschema.LoadURL = func(s string) (io.ReadCloser, error) {
				refSchema, ok := testCase["registry"].(map[string]interface{})[s]

				if !ok {
					return nil, fmt.Errorf("%q not found", s)
				}

				// FIXME: map[string].interface{} -> Schema?
				reserializedRef, err := json.Marshal(refSchema)
				if err != nil {
					panic("This should never happen.")
				}
				return io.NopCloser(strings.NewReader(string(reserializedRef))), nil
			}

			// FIXME: map[string].interface{} -> Schema?
			reserialized, err := json.Marshal(testCase["schema"])
			if err != nil {
				panic("This should never happen.")
			}
			var fakeURI = "bowtie.sent.schema.json"
			if err := compiler.AddResource(fakeURI, strings.NewReader(string(reserialized))); err != nil {
				panic("Bad schema!")
			}
			schema, err := compiler.Compile(fakeURI)
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
