export interface BadgeFormatOption {
  type: string;
  renderDisplay: (badgeURI: string) => JSX.Element;
  generateCopyText: (badgeURI: string) => string;
}

// Supported format list
export const badgeFormatOptions: BadgeFormatOption[] = [
  {
    type: "URL",
    renderDisplay: (badgeURI: string): JSX.Element => (
      <span>
        <pre className="pt-2 pb-2">{badgeURI}</pre>
      </span>
    ),
    generateCopyText: (badgeURI: string): string => `${badgeURI}`,
  },
  {
    type: "Markdown",
    renderDisplay: (badgeURI: string): JSX.Element => (
      <span>
        <pre className="pt-2 pb-2">![Static Badge]({badgeURI})</pre>
      </span>
    ),
    generateCopyText: (badgeURI: string): string =>
      `![Static Badge](${badgeURI})`,
  },
  {
    type: "rSt",
    renderDisplay: (badgeURI: string): JSX.Element => (
      <span>
        <pre className="pt-2 pb-2">
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
      <span>
        <pre className="pt-2 pb-2">image:{badgeURI}[Static Badge]</pre>
      </span>
    ),
    generateCopyText: (badgeURI: string): string =>
      `image:${badgeURI}[Static Badge]`,
  },
  {
    type: "HTML",
    renderDisplay: (badgeURI: string): JSX.Element => (
      <span>
        <pre className="pt-2 pb-2">
          &lt;img alt=&quot;Static Badge&quot; src=&quot;
          {badgeURI}
          &quot;/&gt;
        </pre>
      </span>
    ),
    generateCopyText: (badgeURI: string): string =>
      `<img alt='Static Badge' src='${badgeURI}'/>`,
  },
];
