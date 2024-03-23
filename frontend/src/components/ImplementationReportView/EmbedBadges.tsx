import React, { useState } from "react";

import CopyToClipboard from "../CopyToClipboard";
import { Implementation } from "../../data/parseReportData";
import { Badge, badgesFor } from "../../data/Badge";

const EmbedBadges: React.FC<{
  implementation: Implementation;
}> = ({ implementation }) => {
  const allBadges = badgesFor(implementation);

  const [activeTab, setActiveTab] = useState(supportedFormats[1]);
  const [activeBadge, setActiveBadge] = useState(allBadges.Metadata[0]);

  return (
    <div className="dropdown container d-flex align-items-center justify-content-end">
      <button
        className="btn btn-sm btn-info dropdown-toggle"
        type="button"
        data-bs-toggle="dropdown"
        data-bs-auto-close="outside"
      >
        Badges
      </button>
      <div className="dropdown-menu vw-75">
        <div className="container">
          <h4>Embed a Badge</h4>
          <div className="dropdown">
            <button
              className="btn btn-sm btn-info dropdown-toggle mw-100 overflow-hidden"
              type="button"
              id="dropdownMenuButton"
              data-bs-toggle="dropdown"
              aria-expanded="false"
            >
              {activeBadge.name}
            </button>
            <ul
              className="dropdown-menu dropdown-menu-end"
              aria-labelledby="dropdownMenuButton"
            >
              {Object.entries(allBadges).map(([category, badges]) => (
                <span key={category}>
                  <h6 className="dropdown-header">{category}</h6>
                  {badges.map((badge) => (
                    <li key={badge.name}>
                      <button
                        // FIXME: wut? badge === activeBadge is false, at
                        //        least because badge.uri !== activeBadge.uri
                        //        URI.js has a .equal method
                        className={`dropdown-item btn btn-sm ${
                          badge.name === activeBadge.name ? "active" : ""
                        }`}
                        onClick={() => setActiveBadge(badge)}
                      >
                        {badge.name}
                      </button>
                    </li>
                  ))}
                </span>
              ))}
            </ul>
          </div>
        </div>
        <div className="container">
          <ul className="nav nav-pills justify-content-center">
            {supportedFormats.map((formatItem, index) => {
              return (
                <li className="nav-item" key={index}>
                  <button
                    className={`nav-link btn btn-sm ${
                      activeTab === formatItem ? "active" : ""
                    }`}
                    onClick={() => setActiveTab(formatItem)}
                  >
                    {formatItem.name}
                  </button>
                </li>
              );
            })}
          </ul>
          <div className="tab-content">
            {supportedFormats.map((formatItem, index) => {
              const badgeEmbed = formatItem.generateEmbed(activeBadge);
              return (
                <div
                  key={index}
                  className={`tab-pane ${
                    activeTab === formatItem ? "active" : ""
                  } border rounded`}
                >
                  <div className="d-flex align-items-center justify-content-center">
                    <span className="font-monospace text-body-secondary fs-6 ps-2 d-block">
                      <pre className="py-2">
                        <code>{badgeEmbed}</code>
                      </pre>
                    </span>
                    <CopyToClipboard textToCopy={badgeEmbed} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

interface BadgeFormat {
  name: string;
  generateEmbed: (badge: Badge) => string;
}

const supportedFormats: BadgeFormat[] = [
  {
    name: "URL",
    generateEmbed: (badge) => `${badge.uri.href()}`,
  },
  {
    name: "Markdown",
    generateEmbed: (badge) => `![${badge.altText}](${badge.uri.href()})`,
  },
  {
    name: "reST",
    generateEmbed: (badge) =>
      `.. image:: ${badge.uri.href()}\n    :alt: ${badge.altText}`,
  },
  {
    name: "AsciiDoc",
    generateEmbed: (badge) => `image:${badge.uri.href()}[${badge.altText}]`,
  },
  {
    name: "HTML",
    generateEmbed: (badge) =>
      `<img alt="${badge.altText}" src="${badge.uri.href()}"/>`,
  },
];

export default EmbedBadges;
