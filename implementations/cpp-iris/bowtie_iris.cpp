// =============================================================================
// bench/bowtie_iris.cpp
//
// Bowtie (https://docs.bowtie.report) IHOP stdio harness for IRIS.
//
// IHOP = input -> harness -> output protocol. Bowtie writes one JSON command
// object per line on stdin; the harness writes one JSON response object per
// line on stdout. Commands:
//
//   {"cmd":"start","version":1}
//     -> {"version":1,"implementation":{...}}
//
//   {"cmd":"dialect","dialect":"https://json-schema.org/draft/2020-12/schema"}
//     -> {"ok":true}            (we configured ourselves for that implicit
//     dialect)
//
//   {"cmd":"run","seq":N,"case":{
//        "description":"...",
//        "schema":{...},
//        "registry":{ "<uri>":{...}, ... },   // extra docs for $ref resolution
//        "tests":[{"instance":...}, ...]
//   }}
//     -> {"seq":N,"results":[{"valid":bool} | {"errored":true,...}, ...]}
//
//   {"cmd":"stop"} -> exit 0
//
// CRITICAL DESIGN NOTES (why this harness reproduces IRIS's 100% conformance):
//
//   1. Entry point is Validator::from_schema_json, NOT
//   compile_schema_from_json.
//      from_schema_json auto-routes fast<->slow: it tries the SoA fast path and
//      falls back to the recursive draft-2020-12 slow interpreter for anything
//      the fast path rejects. The fast-path-only entry point would report most
//      cases as unsupported and show a misleadingly poor score on
//      bowtie.report.
//
//   2. $ref resolution uses case.registry. Bowtie ships every remote document a
//      case may reference inline in `case.registry` (uri -> schema). We
//      register each one via add_remote_document so the slow path can resolve
//      them. A harness that ignores the registry fails every $ref/remote test.
//
//   3. One Validator is built per case and reused (read-only) across that
//   case's
//      tests -- no recompile per instance.
// =============================================================================
#include <cstdio>
#include <iostream>
#include <string>

#include "iris/json_reader.hpp"
#include "iris/validator.hpp"

namespace {

constexpr const char *kDialect2020 =
    "https://json-schema.org/draft/2020-12/schema";

// Serialize a JsonValue back to compact JSON text. Used to feed schemas,
// instances and registry documents into IRIS (which parses from text), and to
// echo the opaque `seq` value verbatim.
void serialize(const iris::JsonValue &v, std::string &out);

void serialize_string(std::string_view s, std::string &out) {
  out.push_back('"');
  for (unsigned char c : s) {
    switch (c) {
    case '"':
      out += "\\\"";
      break;
    case '\\':
      out += "\\\\";
      break;
    case '\n':
      out += "\\n";
      break;
    case '\r':
      out += "\\r";
      break;
    case '\t':
      out += "\\t";
      break;
    case '\b':
      out += "\\b";
      break;
    case '\f':
      out += "\\f";
      break;
    default:
      if (c < 0x20) {
        char buf[8];
        std::snprintf(buf, sizeof(buf), "\\u%04x", c);
        out += buf;
      } else {
        out.push_back(static_cast<char>(c));
      }
    }
  }
  out.push_back('"');
}

void serialize(const iris::JsonValue &v, std::string &out) {
  using T = iris::JsonValue::Type;
  switch (v.type()) {
  case T::kNull:
    out += "null";
    return;
  case T::kBool:
    out += v.as_bool() ? "true" : "false";
    return;
  case T::kInt: {
    char buf[32];
    std::snprintf(buf, sizeof(buf), "%lld", static_cast<long long>(v.as_int()));
    out += buf;
    return;
  }
  case T::kDouble: {
    char buf[32];
    std::snprintf(buf, sizeof(buf), "%.17g", v.as_double());
    out += buf;
    return;
  }
  case T::kString:
    serialize_string(v.as_string(), out);
    return;
  case T::kArray: {
    out.push_back('[');
    bool first = true;
    for (auto &e : v.as_array()) {
      if (!first)
        out.push_back(',');
      first = false;
      serialize(e, out);
    }
    out.push_back(']');
    return;
  }
  case T::kObject: {
    out.push_back('{');
    bool first = true;
    for (auto &[k, val] : v.as_object()) {
      if (!first)
        out.push_back(',');
      first = false;
      serialize_string(k, out);
      out.push_back(':');
      serialize(val, out);
    }
    out.push_back('}');
    return;
  }
  }
}

void write_line(const std::string &s) {
  std::fwrite(s.data(), 1, s.size(), stdout);
  std::fputc('\n', stdout);
  std::fflush(stdout);
}

void on_start(const iris::JsonValue &cmd) {
  // version must be the protocol version we speak (1). Bowtie may bump this;
  // we still answer so the operator sees the mismatch rather than a silent
  // hang, but a future-incompatible version is the operator's call.
  (void)cmd;
  write_line(
      R"({"version":1,"implementation":{)"
      R"("language":"cpp",)"
      R"("name":"iris",)"
      R"("version":"0.1.0",)"
      R"("homepage":"https://github.com/Cobra007-star-source/IRIS",)"
      R"("issues":"https://github.com/Cobra007-star-source/IRIS/issues",)"
      R"("source":"https://github.com/Cobra007-star-source/IRIS",)"
      R"("documentation":"https://github.com/Cobra007-star-source/IRIS",)"
      R"("dialects":["https://json-schema.org/draft/2020-12/schema"],)"
      R"("links":[{"description":"license","url":"https://www.gnu.org/licenses/agpl-3.0.html"}])"
      "}}");
}

// The dialect command sets the IMPLICIT dialect (how to treat schemas with no
// $schema). IRIS's slow path defaults to draft-2020-12, which is the only
// dialect we advertise, so we acknowledge it. Anything else: ok:false.
void on_dialect(const iris::JsonValue &cmd) {
  const auto *d = cmd.find("dialect");
  const bool ok = d && d->is_string() && d->as_string() == kDialect2020;
  write_line(ok ? R"({"ok":true})" : R"({"ok":false})");
}

// Emit a results array whose every entry is a caught "errored" item carrying a
// short message. Used when a case's schema cannot be compiled at all -- honest
// signal to Bowtie (preferred over silently skipping).
void emit_errored_results(std::string &out, std::size_t n,
                          std::string_view msg) {
  out += "\"results\":[";
  for (std::size_t i = 0; i < n; ++i) {
    if (i)
      out.push_back(',');
    out += R"({"errored":true,"context":{"message":)";
    std::string m(msg);
    if (m.size() > 200)
      m.resize(200);
    serialize_string(m, out);
    out += "}}";
  }
  out += "]}";
}

void on_run(const iris::JsonValue &cmd) {
  std::string out = "{";
  if (const auto *seq = cmd.find("seq")) {
    out += "\"seq\":";
    serialize(*seq, out);
    out += ",";
  }

  const auto *case_v = cmd.find("case");
  if (!case_v || !case_v->is_object()) {
    out += "\"results\":[],\"error\":\"case missing\"}";
    write_line(out);
    return;
  }
  const auto *schema_v = case_v->find("schema");
  const auto *tests_v = case_v->find("tests");
  if (!schema_v || !tests_v || !tests_v->is_array()) {
    out += "\"results\":[],\"error\":\"schema/tests missing\"}";
    write_line(out);
    return;
  }
  const std::size_t n_tests = tests_v->as_array().size();

  // Build the validator once for this case (auto fast<->slow routing).
  std::string schema_str;
  serialize(*schema_v, schema_str);
  iris::ValidatorBuild vb;
  iris::Validator validator = iris::Validator::from_schema_json(schema_str, vb);
  if (!vb.ok) {
    emit_errored_results(out, n_tests, vb.diagnostic);
    write_line(out);
    return;
  }

  // Feed the inline registry to the slow path so $ref can resolve. Only the
  // slow path owns a document store; if the case is pure fast path there are
  // no $refs to resolve, so a missing registry is harmless.
  if (const auto *reg = case_v->find("registry");
      reg && reg->is_object() && validator.has_slow_path()) {
    for (const auto &[uri, doc] : reg->as_object()) {
      std::string doc_str;
      serialize(doc, doc_str);
      validator.add_remote_document(uri, doc_str);
    }
  }

  out += "\"results\":[";
  bool first = true;
  for (const auto &t : tests_v->as_array()) {
    if (!first)
      out.push_back(',');
    first = false;
    const auto *inst = t.find("instance");
    if (!inst) {
      out += R"({"errored":true,"context":{"message":"instance missing"}})";
      continue;
    }
    std::string inst_str;
    serialize(*inst, inst_str);
    const auto r = validator.validate(inst_str);
    out += r.ok() ? R"({"valid":true})" : R"({"valid":false})";
  }
  out += "]}";
  write_line(out);
}

} // namespace

int main() {
  std::ios::sync_with_stdio(false);
  std::string line;
  line.reserve(1 << 16);

  while (std::getline(std::cin, line)) {
    if (line.empty())
      continue;
    auto p = iris::parse_json(line);
    if (!p.ok || !p.value.is_object()) {
      write_line(R"({"error":"bad command line"})");
      continue;
    }
    const auto *cmd_v = p.value.find("cmd");
    if (!cmd_v || !cmd_v->is_string()) {
      write_line(R"({"error":"cmd missing"})");
      continue;
    }
    const std::string &cmd = cmd_v->as_string();
    if (cmd == "start") {
      on_start(p.value);
    } else if (cmd == "dialect") {
      on_dialect(p.value);
    } else if (cmd == "run") {
      on_run(p.value);
    } else if (cmd == "stop") {
      return 0;
    } else {
      write_line(R"({"error":"unknown cmd"})");
    }
  }
  return 0;
}
