import React, { useState } from "react";
import { Badge, Dropdown, Nav, Tab } from "react-bootstrap";
import { Implementation } from "../../data/parseReportData";
import CopyToClipboard from "../CopyToClipboard";
import Dialect from "../../data/Dialect";
import { complianceBadgeFor } from "../../data/Badge";

const EmbedBadges: React.FC<{
  implementation: Implementation;
}> = ({ implementation }) => {
  const results = Object.entries(implementation.results);
  const [activeTab, setActiveTab] = useState("URL");
  const [activeDialect, setActiveDialect] = useState(results[0][0]);

  const handleSelectDialect = (dialectName: string): void => {
    setActiveDialect(dialectName);
    const dialect = Dialect.withName(dialectName);
    setBadgeURI(complianceBadgeFor(implementation, dialect).href());
  };

  const [badgeURI, setBadgeURI] = useState(
    complianceBadgeFor(implementation, Dialect.withName(activeDialect)).href()
  );

  const handleSelect = (tabKey: string | null) => {
    if (tabKey) {
      setActiveTab(tabKey);
    }
  };

  return (
    <Dropdown
      className="mx-auto mb-3 col-12 col-sm-12 col-md-12"
      autoClose="outside"
    >
      <Dropdown.Toggle variant="success" size="sm">
        Badges
      </Dropdown.Toggle>
      <Dropdown.Menu className="mx-auto mb-3 col-12 col-sm-7 col-md-12">
        <Dropdown.Item eventKey="0">
          <div className="container d-flex justify-content-center flex-row flex-wrap">
            {results.map((result) => (
              <Badge
                pill
                bg={result[0] === activeDialect ? `filter-active` : `filter`}
                key={result[0]}
                className="mx-1 mb-2"
                onClick={() => handleSelectDialect(result[0])}
                role="button"
              >
                <div className="px-2">{result[0]}</div>
              </Badge>
            ))}
          </div>

          <div className="container d-flex justify-content-center align-items-center flex-column">
            <Tab.Container defaultActiveKey="URL">
              <Nav
                className="justify-content-center gap-2"
                variant="pills"
                activeKey={activeTab}
                onSelect={handleSelect}
              >
                <Nav.Item>
                  <Nav.Link eventKey="URL">URL</Nav.Link>
                </Nav.Item>
                <Nav.Item>
                  <Nav.Link eventKey="Markdown">Markdown</Nav.Link>
                </Nav.Item>
                <Nav.Item>
                  <Nav.Link eventKey="rSt">rSt</Nav.Link>
                </Nav.Item>
                <Nav.Item>
                  <Nav.Link eventKey="AsciiDoc">AsciiDoc</Nav.Link>
                </Nav.Item>
                <Nav.Item>
                  <Nav.Link eventKey="HTML">HTML</Nav.Link>
                </Nav.Item>
              </Nav>

              <Tab.Content className="col-6 col-sm-6 col-md-11 mt-2">
                <Tab.Pane eventKey="URL">
                  <div className="d-flex align-items-center justify-content-center border rounded ps-3 pt-3 px-3">
                    <div className="overflow-auto">
                      <p
                        className="font-monospace text-body-secondary"
                        style={{
                          wordWrap: "break-word",
                          textOverflow: "hidden",
                        }}
                      >
                        {badgeURI}
                      </p>
                    </div>
                    <div className="d-flex ms-auto pb-3">
                      <CopyToClipboard textToCopy={badgeURI} />
                    </div>
                  </div>
                </Tab.Pane>
                <Tab.Pane eventKey="Markdown">
                  <div className="d-flex align-items-center justify-content-center border rounded ps-3 pt-3 px-3">
                    <div className="overflow-auto">
                      <p
                        className="font-monospace text-body-secondary"
                        style={{
                          wordWrap: "break-word",
                          textOverflow: "hidden",
                        }}
                      >
                        ![Static Badge]({badgeURI})
                      </p>
                    </div>
                    <div className="d-flex ms-auto pb-3">
                      <CopyToClipboard
                        textToCopy={`![Static Badge](${badgeURI})`}
                      />
                    </div>
                  </div>
                </Tab.Pane>
                <Tab.Pane eventKey="rSt">
                  <div className="d-flex align-items-center justify-content-center border rounded ps-3 pt-3 px-3">
                    <div className="overflow-auto">
                      <p
                        className="font-monospace text-body-secondary"
                        style={{
                          wordWrap: "break-word",
                          textOverflow: "hidden",
                        }}
                      >
                        .. image:: ${badgeURI}
                        <br />
                        :alt: Static Badge
                      </p>
                    </div>
                    <div className="d-flex ms-auto pb-3">
                      <CopyToClipboard
                        textToCopy={`.. image:: ${badgeURI}
                      :alt: Static Badge
                   `}
                      />
                    </div>
                  </div>
                </Tab.Pane>
                <Tab.Pane eventKey="AsciiDoc">
                  <div className="d-flex align-items-center justify-content-center border rounded ps-3 pt-3 px-3">
                    <div className="overflow-auto">
                      <p
                        className="font-monospace text-body-secondary"
                        style={{
                          wordWrap: "break-word",
                          textOverflow: "hidden",
                        }}
                      >
                        image:${badgeURI}[Static Badge]
                      </p>
                    </div>
                    <div className="d-flex ms-auto pb-3">
                      <CopyToClipboard
                        textToCopy={`image:${badgeURI}[Static Badge]
                      `}
                      />
                    </div>
                  </div>
                </Tab.Pane>
                <Tab.Pane eventKey="HTML">
                  <div className="d-flex align-items-center justify-content-center border rounded ps-3 pt-3 px-3">
                    <div className="overflow-auto">
                      <p
                        className="font-monospace text-body-secondary"
                        style={{
                          wordWrap: "break-word",
                          textOverflow: "hidden",
                        }}
                      >
                        &lt;img alt=&quot;Static Badge&quot; src=&quot;
                        {badgeURI}
                        &quot;/&gt;
                      </p>
                    </div>
                    <div className="d-flex ms-auto pb-3">
                      <CopyToClipboard
                        textToCopy={`<img alt="Static Badge" src="${badgeURI}"/>
                      `}
                      />
                    </div>
                  </div>
                </Tab.Pane>
              </Tab.Content>
            </Tab.Container>
          </div>
        </Dropdown.Item>
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default EmbedBadges;
