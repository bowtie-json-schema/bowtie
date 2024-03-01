import React, { useState } from "react";
import { Implementation } from "../../data/parseReportData";
import CopyToClipboard from "../CopyToClipboard";
import Dialect from "../../data/Dialect";
import { complianceBadgeFor, versionsBadgeFor } from "../../data/Badge";
import { badgeFormatOptions, BadgeFormatOption } from "./BadgeFormats";

const EmbedBadges: React.FC<{
  implementation: Implementation;
}> = ({ implementation }) => {
  const results = Object.entries(implementation.results);
  const [activeTab, setActiveTab] = useState("URL");
  const [activeBadge, setActiveBadge] = useState("Supported Versions");

  const handleSelectBadge = (dialectName: string): void => {
    setActiveBadge(dialectName);
    if (dialectName === "Supported Versions") {
      setBadgeURI(versionsBadgeFor(implementation).href());
    } else {
      const dialect = Dialect.withName(dialectName);
      setBadgeURI(complianceBadgeFor(implementation, dialect).href());
    }
  };

  const [badgeURI, setBadgeURI] = useState(
    versionsBadgeFor(implementation).href()
  );

  const handleSelectTab = (tabKey: string | null) => {
    if (tabKey) {
      setActiveTab(tabKey);
    }
  };

  return (
    <div className="container dropdown mx-auto mb-3 col-12 col-sm-12 col-md-12">
      <button
        className="btn btn-sm btn-success dropdown-toggle"
        type="button"
        data-bs-toggle="dropdown"
        data-bs-auto-close="outside"
        style={{ width: "100px" }}
      >
        Badges
      </button>
      <ul className="dropdown-menu mx-auto mb-3 " style={{ width: "45vw" }}>
        <li>
          <div className="container ">
            <div className="dropdown d-flex justify-content-center align-items-center py-2">
              <button
                className="btn btn-sm btn-primary dropdown-toggle"
                type="button"
                id="dropdownMenuButton"
                data-bs-toggle="dropdown"
                aria-expanded="false"
              >
                {activeBadge === "Supported Versions"
                  ? "Supported Versions"
                  : Dialect.withName(activeBadge).prettyName}
              </button>
              <ul
                className="dropdown-menu"
                aria-labelledby="dropdownMenuButton"
              >
                <li key={"Supported Versions"}>
                  <button
                    className={`dropdown-item btn-sm ${
                      activeBadge === "Supported Versions" ? "active" : ""
                    }`}
                    onClick={() => handleSelectBadge("Supported Versions")}
                  >
                    {"Supported Versions"}
                  </button>
                </li>
                {results.map((result) => (
                  <li key={result[0]}>
                    <button
                      className={`dropdown-item btn-sm ${
                        result[0] === activeBadge ? "active" : ""
                      }`}
                      onClick={() => handleSelectBadge(result[0])}
                    >
                      {Dialect.withName(result[0]).prettyName}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="container d-flex justify-content-center align-items-center flex-column py-3">
            <ul className="nav nav-pills justify-content-center gap-2">
              {badgeFormatOptions.map(
                (formatItem: BadgeFormatOption, index) => {
                  return (
                    <li className="nav-item" key={index}>
                      <button
                        className={`nav-link btn-sm ${
                          activeTab === formatItem.type ? "active" : ""
                        }`}
                        onClick={() => handleSelectTab(formatItem.type)}
                      >
                        {formatItem.type}
                      </button>
                    </li>
                  );
                }
              )}
            </ul>
            <div className="tab-content mt-2 py-2">
              {badgeFormatOptions.map(
                (formatItem: BadgeFormatOption, index) => (
                  <div
                    key={index}
                    className={`tab-pane ${
                      activeTab === formatItem.type ? "active" : ""
                    } border rounded ps-3 pt-3 px-3`}
                    style={{ width: "100%" }}
                  >
                    <div className="d-flex align-items-center justify-content-center">
                      <div className="pe-2">
                        <p
                          className="font-monospace text-body-secondary"
                          style={{
                            wordWrap: "break-word",
                            whiteSpace: "nowrap",
                            textOverflow: "hidden",
                            overflowX: "auto",
                            width: "25vw",
                          }}
                        >
                          {formatItem.renderDisplay(badgeURI)}
                        </p>
                      </div>
                      <div className="d-flex ms-auto pb-3">
                        <CopyToClipboard
                          textToCopy={formatItem.generateCopyText(badgeURI)}
                        />
                      </div>
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        </li>
      </ul>
    </div>
  );
};

export default EmbedBadges;
