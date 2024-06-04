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

	"github.com/santhosh-tekuri/jsonschema/v6"
)

var drafts = map[string]*jsonschema.Draft{
	"https://json-schema.org/draft/2020-12/schema": jsonschema.Draft2020,
	"https://json-schema.org/draft/2019-09/schema": jsonschema.Draft2019,
	"http://json-schema.org/draft-07/schema#":      jsonschema.Draft7,
	"http://json-schema.org/draft-06/schema#":      jsonschema.Draft6,
	"http://json-schema.org/draft-04/schema#":      jsonschema.Draft4,
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
	var draft *jsonschema.Draft = nil

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
					"name":     "jsonschema",
					"version":  jsonschemaVersion(),
					"homepage": "https://github.com/santhosh-tekuri/jsonschema",
					"issues":   "https://github.com/santhosh-tekuri/jsonschema/issues",
					"source":   "https://github.com/santhosh-tekuri/jsonschema",
					"dialects": []string{
						"https://json-schema.org/draft/2020-12/schema",
						"https://json-schema.org/draft/2019-09/schema",
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
			data := map[string]interface{}{"ok": draft != nil}
			printJSON(data)
		case "run":
			if !started {
				panic("Not started!")
			}
			testCase, ok := request["case"].(map[string]interface{})
			if !ok {
				panic("No case!")
			}

			compiler := jsonschema.NewCompiler()
			if draft != nil {
				compiler.DefaultDraft(draft)
			}
			registry, ok := testCase["registry"]
			if ok {
				loader := registryLoader(registry.(map[string]any))
				compiler.UseLoader(loader)
			}
			var fakeURI = "bowtie.sent.schema.json"
			if err := compiler.AddResource(fakeURI, testCase["schema"]); err != nil {
				printError(request["seq"].(json.Number), err)
				break
			}
			schema, err := compiler.Compile(fakeURI)
			if err != nil {
				printError(request["seq"].(json.Number), err)
				break
			}

			var results []map[string]interface{}
			for _, test := range testCase["tests"].([]interface{}) {
				err := schema.Validate(test.(map[string]interface{})["instance"])
				result := map[string]interface{}{
					"valid": err == nil,
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

type registryLoader map[string]any

func (l registryLoader) Load(url string) (any, error) {
	refSchema, ok := l[url]
	if !ok {
		return nil, fmt.Errorf("%q not found", url)
	}
	return refSchema, nil
}

func jsonschemaVersion() string {
	buildInfo, ok := debug.ReadBuildInfo()
	if !ok {
		panic("Failed to read build info")
	}

	var version = ""
	for _, dep := range buildInfo.Deps {
		if strings.Contains(dep.Path, "github.com/santhosh-tekuri/jsonschema") {
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
