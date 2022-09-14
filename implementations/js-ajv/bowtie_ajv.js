const readline = require("readline");

const Ajv = require("ajv");

const stdio = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false,
});

function send(data) {
  console.log(JSON.stringify(data));
}

var started = false;

const cmds = {
  start: (args) => {
    console.assert(args.version === 1, { args });
    started = true;
    return {
      ready: true,
      version: 1,
      implementation: {
        language: "javascript",
        name: "ajv",
        homepage: "https://ajv.js.org/",
        issues: "https://github.com/ajv-validator/ajv/issues",

        dialects: [
          "https://json-schema.org/draft/2020-12/schema",
          "https://json-schema.org/draft/2019-09/schema",
          "http://json-schema.org/draft-07/schema#",
          "http://json-schema.org/draft-06/schema#",
          "http://json-schema.org/draft-04/schema#",
        ],
      },
    };
  },

  run: (args) => {
    console.assert(started, "Not started!");

    const testCase = args.case;
    const validate = ajv.compile(testCase.schema);
    return {
      seq: args.seq,
      results: testCase.tests.map((test) => ({
        valid: validate(test.instance),
      })),
    };
  },

  stop: (_) => {
    console.assert(started, "Not started!");
    process.exit(0);
  },
};

const ajv = new Ajv();

stdio.on("line", (line) => {
  const request = JSON.parse(line);
  const response = cmds[request.cmd](request);
  send(response);
});
