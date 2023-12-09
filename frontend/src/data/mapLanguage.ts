const langMap: Record<string, string> = {
  dotnet: ".NET",
  javascript: "JavaScript",
  php: "PHP",
  typescript: "TypeScript",
};

export const mapLanguage = (lang: string) =>
  langMap[lang] ?? lang.charAt(0).toUpperCase().concat(lang.substring(1));
