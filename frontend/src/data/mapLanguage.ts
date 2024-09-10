import { titleCase } from "title-case";

const langMap: Record<string, string> = {
  dotnet: ".NET",
  javascript: "JavaScript",
  php: "PHP",
  typescript: "TypeScript",
};

export const mapLanguage = (lang: string) => langMap[lang] ?? titleCase(lang);
