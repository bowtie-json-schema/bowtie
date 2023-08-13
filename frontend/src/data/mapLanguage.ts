const langMap: Record<string, string> = {
  clojure: "Clojure",
  "c++": "C++",
  dotnet: ".NET",
  go: "Go",
  java: "Java",
  javascript: "JavaScript",
  kotlin: "Kotlin",
  lua: "Lua",
  python: "Python",
  ruby: "Ruby",
  rust: "Rust",
  typescript: "TypeScript",
};

export const mapLanguage = (lang: string) => langMap[lang] ?? lang;
