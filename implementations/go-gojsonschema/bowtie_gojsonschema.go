package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"runtime"
	"runtime/debug"
	"strings"
	"syscall"

	"github.com/xeipuuv/gojsonschema"
)

var drafts = map[string]gojsonschema.Draft{
	"http://json-schema.org/draft-07/schema#": gojsonschema.Draft7,
	"http://json-schema.org/draft-06/schema#": gojsonschema.Draft6,
	"http://json-schema.org/draft-04/schema#": gojsonschema.Draft4,
}

func getOsVersion() string {
	var uname syscall.Utsname
	if err := syscall.Uname(&uname); err != nil {
		return ""
	}
	release := ""
	for _, b := range uname.Release {
		if b == 0 {
			break
		}
		release += string(b)
	}
	return fmt.Sprintf(release)
}

func main() {
	var started = false
	var draft gojsonschema.Draft = gojsonschema.Hybrid

	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		var request map[string]interface{}

		decoder := json.NewDecoder(strings.NewReader(scanner.Text()))
		decoder.UseNumber()
		err := decoder.Decode(&request)
		if err != nil {
			fmt.Printf("could not unmarshal json: %s\n", err)
			return
		}

		switch request["cmd"] {
		case "start":
			started = true
			rawVersion, ok := request["version"]
			if !ok {
				panic("No version!")
			}
			version := rawVersion.(json.Number)
			if v, err := version.Float64(); err != nil || v != 1 {
				panic("Not version 1!")
			}
			data := map[string]interface{}{
				"version": 1,
				"implementation": map[string]interface{}{
					"language": "go",
					"name":     "gojsonschema",
					"version":  gojsonschemaVersion(),
					"homepage": "https://github.com/xeipuuv/gojsonschema",
					"issues":   "https://github.com/xeipuuv/gojsonschema/issues",
					"source":   "https://github.com/xeipuuv/gojsonschema",
					"dialects": []string{
						"http://json-schema.org/draft-07/schema#",
						"http://json-schema.org/draft-06/schema#",
						"http://json-schema.org/draft-04/schema#",
					},
					"os":               runtime.GOOS,
					"os_version":       getOsVersion(),
					"language_version": runtime.Version(),
				},
			}
			printJSON(data)
		case "dialect":
			if !started {
				panic("Not started!")
			}
			rawDialect, ok := request["dialect"]
			if !ok {
				panic("No dialect!")
			}
			dialect := rawDialect.(string)
			draft = drafts[dialect]
			data := map[string]interface{}{"ok": draft != gojsonschema.Hybrid}
			printJSON(data)
		case "run":
			if !started {
				panic("Not started!")
			}
			testCase, ok := request["case"].(map[string]interface{})
			if !ok {
				panic("No case!")
			}

			loader := gojsonschema.NewSchemaLoader()
			if draft != gojsonschema.Hybrid {
				loader.Draft = draft
				loader.AutoDetect = false
			}
			registry, ok := testCase["registry"].(map[string]interface{})
			if ok {
				for uri, remoteSchema := range registry {
					remoteLoader := gojsonschema.NewGoLoader(remoteSchema.(map[string]interface{}))
					loader.AddSchema(uri, remoteLoader)
				}
			}

			schemaLoader := gojsonschema.NewGoLoader(testCase["schema"])
			schema, err := loader.Compile(schemaLoader)
			if err != nil {
				printError(request["seq"].(json.Number), err)
				break
			}

			var results []map[string]interface{}
			for _, test := range testCase["tests"].([]interface{}) {
				var result map[string]interface{}

				instanceLoader := gojsonschema.NewGoLoader(test.(map[string]interface{})["instance"])
				validationResult, err := schema.Validate(instanceLoader)
				if err == nil {
					result = map[string]interface{}{
						"valid": validationResult.Valid(),
					}
				} else {
					result = map[string]interface{}{
						"errored": true,
						"context": map[string]interface{}{
							"message": err.Error(),
						},
					}
				}
				results = append(results, result)
			}

			data := map[string]interface{}{
				"seq":     request["seq"],
				"results": results,
			}
			printJSON(data)
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

func gojsonschemaVersion() string {
	buildInfo, ok := debug.ReadBuildInfo()
	if !ok {
		panic("Failed to read build info")
	}

	var version = ""
	for _, dep := range buildInfo.Deps {
		if strings.Contains(dep.Path, "github.com/xeipuuv/gojsonschema") {
			version = dep.Version
			break
		}
	}
	return version
}

func printJSON(v interface{}) {
	encoder := json.NewEncoder(os.Stdout)
	if err := encoder.Encode(v); err != nil {
		panic("Failed sending a response!")
	}
}

func printError(seq json.Number, err error) {
	data := map[string]interface{}{
		"seq":     seq,
		"errored": true,
		"context": map[string]interface{}{
			"message": err.Error(),
		},
	}
	printJSON(data)
}
