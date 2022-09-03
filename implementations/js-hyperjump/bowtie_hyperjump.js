const readline = require('readline/promises');

const JsonSchema = require("@hyperjump/json-schema");

const stdio = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

function send(data) {
  console.log(JSON.stringify(data));
}

var started = false;

const cmds = {
  start: async (args) => {
    console.assert(args.version === 1, { args });
    started = true;
    return {ready: true, version: 1}
  },

  run: async (args) => {
    console.assert(started, "Not started!");

    const testCase = args.case;

    const schemaId = 'http://example.com/schema/' + args.seq.toString();
    JsonSchema.add(testCase.schema, schemaId, "https://json-schema.org/draft/2020-12/schema");
    const schema = JsonSchema.get(schemaId);

    const validate = await JsonSchema.validate(schema);
    const promises = testCase.tests.map(
      (test) => ({ valid: validate(test.instance).valid })
    );
    const tests = await Promise.all(promises);
    return { seq: args.seq, tests: tests }
  },

  stop: async (_) => {
      console.assert(started, "Not started!");
      process.exit(0);
  }
}

async function main() {
  for await (const line of stdio) {
    const request = JSON.parse(line);
    const response = await cmds[request.cmd](request);
    send(response);
  }
}

main();
