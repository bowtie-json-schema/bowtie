import { createInterface } from "node:readline";
import { readFileSync } from "node:fs";
import { JetValidator } from "@jetio/validator";
import { loadAllMetaSchemas } from "./meta-schemas/loader.mjs";

const pkg = JSON.parse(
  readFileSync(
    new URL("./node_modules/@jetio/validator/package.json", import.meta.url),
  ),
);

let started = false;
let implicitDialect = null;

function draftOptionFor(dialect) {
  if (!dialect) return {};
  if (dialect.includes("draft-06")) return { draft: "draft6" };
  if (dialect.includes("draft-07")) return { draft: "draft7" };
  if (dialect.includes("2019-09")) return { draft: "draft2019-09" };
  return { draft: "draft2020-12" };
}

const handlers = {
  start(req) {
    if (req.version !== 1)
      throw new Error(`unsupported IHOP version ${req.version}`);
    started = true;
    return {
      version: 1,
      implementation: {
        language: "javascript",
        name: "jetio-validator",
        version: pkg.version,
        homepage: "https://github.com/official-jetio/validator",
        issues: "https://github.com/official-jetio/validator/issues",
        source: "https://github.com/official-jetio/validator",
        dialects: [
          "https://json-schema.org/draft/2020-12/schema",
          "https://json-schema.org/draft/2019-09/schema",
          "http://json-schema.org/draft-07/schema#",
          "http://json-schema.org/draft-06/schema#",
        ],
      },
    };
  },

  dialect(req) {
    if (!started) throw new Error("not started");
    implicitDialect = req.dialect;
    return { ok: true };
  },

  run(req) {
    if (!started) throw new Error("not started");
    const { seq, case: kase } = req;
    try {
      const schema = kase.schema;
      const isBool = typeof schema === "boolean";
      const hasSchema =
        !isBool && schema && typeof schema === "object" && "$schema" in schema;

      const base = { strict: false, validateFormats: false };
      const jet = new JetValidator(
        hasSchema ? base : { ...base, ...draftOptionFor(implicitDialect) },
      );
      loadAllMetaSchemas(jet);

      for (const [uri, s] of Object.entries(kase.registry ?? {}))
        if (typeof s !== "boolean") jet.addSchema(s, uri);

      if (!isBool) {
        const rootId = schema.$id || schema.id;
        if (rootId) jet.addSchema(schema, rootId);
      }

      const validate = jet.compile(schema);
      const results = kase.tests.map((t) => ({
        valid: Boolean(validate(t.instance)),
      }));
      return { seq, results };
    } catch (err) {
      console.error(
        `[jet] ${kase.schema?.$id ?? kase.schema?.$schema ?? "?"} :: ${err?.stack ?? err}`,
      );
      return {
        seq,
        errored: true,
        context: {
          message: String(err?.message ?? err),
          traceback: err?.stack,
        },
      };
    }
  },

  stop() {
    if (!started) throw new Error("not started");
    process.exit(0);
  },
};

const rl = createInterface({ input: process.stdin });
rl.on("line", (line) => {
  if (!line.trim()) return;
  const req = JSON.parse(line);
  const res = handlers[req.cmd](req);
  if (res) process.stdout.write(JSON.stringify(res) + "\n");
});
