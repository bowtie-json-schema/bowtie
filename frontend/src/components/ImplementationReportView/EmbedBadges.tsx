import React, { useContext, useState } from "react";
import Container from "react-bootstrap/Container";
import Image from "react-bootstrap/Image";
import ListGroup from "react-bootstrap/ListGroup";
import Button from "react-bootstrap/Button";
import Modal from "react-bootstrap/Modal";
import CopyToClipboard from "../CopyToClipboard";
import { Implementation } from "../../data/parseReportData";
import { Badge, badgesFor } from "../../data/Badge";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { ThemeContext } from "../../context/ThemeContext";
import {
  oneDark,
  oneLight,
} from "react-syntax-highlighter/dist/esm/styles/prism";

const EmbedBadges: React.FC<{
  implementation: Implementation;
}> = ({ implementation }) => {
  const allBadges = badgesFor(implementation);
  const { isDarkMode } = useContext(ThemeContext);

  const [activeFormat, setActiveFormat] = useState(supportedFormats[1]);
  const [activeBadge, setActiveBadge] = useState(allBadges.Metadata[0]);
  const [show, setShow] = useState(false);
  const badgeEmbed = activeFormat.generateEmbed(activeBadge);

  const compareBadges = (a: Badge, b: Badge) => {
    return a.name === b.name && a.uri.equals(b.uri);
  };

  return (
    <>
      <Button variant="info" size="sm" onClick={() => setShow(true)}>
        Badges
      </Button>
      <Modal
        size="xl"
        fullscreen="xl-down"
        contentClassName="px-3 px-lg-4"
        show={show}
        scrollable
        onHide={() => setShow(false)}
      >
        <Modal.Header closeButton className="border-0">
          <Modal.Title className="fs-5 ms-3 mt-4">Badges</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Container className="p-5">
            <div className="pb-3 d-flex flex-row gap-5 align-items-center">
              <ListGroup variant="flush">
                {Object.entries(allBadges).map(([category, badges]) => (
                  <ListGroup.Item key={category}>
                    <h6>{category}</h6>
                    <ListGroup variant="flush">
                      {badges.map((badge) => (
                        <ListGroup.Item
                          key={badge.name}
                          action
                          active={compareBadges(activeBadge, badge)}
                          onClick={() => setActiveBadge(badge)}
                        >
                          {badge.name}
                        </ListGroup.Item>
                      ))}
                    </ListGroup>
                  </ListGroup.Item>
                ))}
              </ListGroup>

              <div className="overflow-auto">
                <div className="pb-3">
                  <p>
                    Bowtie regularly rebuilds a number of badges for
                    {implementation.name}.
                  </p>
                  <p>
                    If you are a maintainer, you may be interested in embedding
                    one or more of them in your documentation to show off! Here
                    are embeddable snippets for whatever documentation language
                    you are likely to be using. The badge will automatically
                    update as Bowtie re-runs its report, so no manual updating
                    should be necessary.
                  </p>
                </div>

                <hr className="mx-5 py-3" />
                <div
                  className={`font-monospace d-flex position-relative p-5 mx-5`}
                  style={{
                    backgroundColor: isDarkMode ? "#282c34" : "#fafafa",
                  }}
                >
                  <span className="m-2 position-absolute top-0 end-0">
                    <CopyToClipboard textToCopy={badgeEmbed} />
                  </span>
                  <SyntaxHighlighter
                    language={activeFormat.name.toLowerCase()}
                    style={isDarkMode ? oneDark : oneLight}
                    className="py-5"
                  >
                    {badgeEmbed}
                  </SyntaxHighlighter>
                </div>

                <Image
                  alt={activeBadge.name}
                  src={activeBadge.uri.href()}
                  className="d-block mx-auto my-5"
                />
              </div>

              <div className="vr my-5"></div>

              <div>
                <h5 className="ps-1">Format</h5>
                <ListGroup variant="flush">
                  {supportedFormats.map((format) => (
                    <ListGroup.Item
                      action
                      active={activeFormat === format}
                      onClick={() => setActiveFormat(format)}
                      key={format.name}
                    >
                      {format.name}
                    </ListGroup.Item>
                  ))}
                </ListGroup>
              </div>
            </div>
          </Container>
        </Modal.Body>
      </Modal>
    </>
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
