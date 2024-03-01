export interface BadgeFormatOption {
  type: string;
  renderDisplay: (badgeURI: string) => JSX.Element;
  generateCopyText: (badgeURI: string) => string;
}
// updating available badge formats
export const badgeFormatOptions: BadgeFormatOption[] = [
  {
    type: "URL",
    renderDisplay: (badgeURI: string): JSX.Element => <span>{badgeURI}</span>,
    generateCopyText: (badgeURI: string): string => `${badgeURI}`,
  },
  {
    type: "Markdown",
    renderDisplay: (badgeURI: string): JSX.Element => (
      <span>![Static Badge]({badgeURI})</span>
    ),
    generateCopyText: (badgeURI: string): string =>
      `![Static Badge](${badgeURI})`,
  },
  {
    type: "rSt",
    renderDisplay: (badgeURI: string): JSX.Element => (
      <span>
        <pre>
          .. image:: {badgeURI}
          {"\n"} :alt: Static Badge
        </pre>
      </span>
    ),
    generateCopyText: (badgeURI: string): string =>
      `.. image:: ${badgeURI}\n :alt: Static Badge`,
  },
  {
    type: "AsciiDoc",
    renderDisplay: (badgeURI: string): JSX.Element => (
      <span>image:{badgeURI}[Static Badge]</span>
    ),
    generateCopyText: (badgeURI: string): string =>
      `image:${badgeURI}[Static Badge]`,
  },
  {
    type: "HTML",
    renderDisplay: (badgeURI: string): JSX.Element => (
      <span>
        &lt;img alt=&quot;Static Badge&quot; src=&quot;
        {badgeURI}
        &quot;/&gt;
      </span>
    ),
    generateCopyText: (badgeURI: string): string =>
      `<img alt='Static Badge' src='${badgeURI}'/>`,
  },
];
