export interface BadgeFormatOption {
  type: string;
  generateCopyText: (badgeURI: string, prettyName: string) => string;
}

// Supported format list
export const badgeFormatOptions: BadgeFormatOption[] = [
  {
    type: "URL",
    // eslint-disable-next-line
    generateCopyText: (badgeURI, prettyName) => `${badgeURI}`,
  },
  {
    type: "Markdown",
    generateCopyText: (badgeURI, prettyName) => `![${prettyName}](${badgeURI})`,
  },
  {
    type: "rSt",
    generateCopyText: (badgeURI, prettyName) =>
      `.. image:: ${badgeURI}\n :alt: ${prettyName}`,
  },
  {
    type: "AsciiDoc",
    generateCopyText: (badgeURI, prettyName) =>
      `image:${badgeURI}[${prettyName}]`,
  },
  {
    type: "HTML",
    generateCopyText: (badgeURI, prettyName) =>
      `<img alt='${prettyName}' src='${badgeURI}'/>`,
  },
];
