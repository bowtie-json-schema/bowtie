export interface JsonToken {
  text: string;
  /** highlight class, or "" for punctuation / whitespace */
  cls: "" | "j-key" | "j-str" | "j-num" | "j-bool";
}

const TOKEN =
  /("(?:\\.|[^"\\])*"(\s*:)?|\b(?:true|false)\b|\bnull\b|-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)/g;

/**
 * Tokenize a JSON value for highlighting. Returns an array of {text, cls} so
 * the caller renders with plain Svelte markup (Svelte escapes each text node)
 * — no `{@html}`, no manual escaping, no XSS surface.
 *
 * Dependency-free by design so it stays off the initial bundle's critical path;
 * swap for a fuller highlighter (e.g. a lazily-imported shiki) if ever needed.
 */
export function tokenizeJson(value: unknown): JsonToken[] {
  const json = JSON.stringify(value, null, 2) ?? "undefined";
  const tokens: JsonToken[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  TOKEN.lastIndex = 0;
  while ((m = TOKEN.exec(json)) !== null) {
    if (m.index > last) {
      tokens.push({ text: json.slice(last, m.index), cls: "" });
    }
    const t = m[0];
    let cls: JsonToken["cls"] = "j-num";
    if (t[0] === '"') cls = /:\s*$/.test(t) ? "j-key" : "j-str";
    else if (t === "true" || t === "false" || t === "null") cls = "j-bool";
    tokens.push({ text: t, cls });
    last = m.index + t.length;
  }
  if (last < json.length) tokens.push({ text: json.slice(last), cls: "" });
  return tokens;
}
