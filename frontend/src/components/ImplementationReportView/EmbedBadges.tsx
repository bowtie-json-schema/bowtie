import React, { useContext, useState } from "react";
import Container from "react-bootstrap/Container";
import Image from "react-bootstrap/Image";
import ListGroup from "react-bootstrap/ListGroup";
import Button from "react-bootstrap/Button";
import Modal from "react-bootstrap/Modal";
import CopyToClipboard from "../CopyToClipboard";
import { Implementation } from "../../data/parseReportData";
import { Badge, badgesFor } from "../../data/Badge";
import SyntaxHighlighter from "react-syntax-highlighter/dist/esm/default-highlight";
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
        fullscreen="lg-down"
        contentClassName="p-0 p-md-3 p-lg-5"
        show={show}
        onHide={() => setShow(false)}
      >
        <Modal.Header closeButton className="border-0 ps-4">
          <Modal.Title className="fs-5">Badges</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Container>
            <div>
              <p>
                Bowtie regularly rebuilds a number of badges for{" "}
                {implementation.name}.
              </p>
              <p>
                If you are a maintainer, you may be interested in embedding one
                or more of them in your documentation to show off! Here are
                embeddable snippets for whatever documentation language you are
                likely to be using. The badge will automatically update as
                Bowtie re-runs its report, so no manual updating should be
                necessary.
              </p>
              <hr className="mx-0 mx-sm-3 my-5" />
            </div>
            <div className="d-sm-flex pb-3 gap-4 gap-lg-5 align-items-center">
              <ListGroup variant="flush">
                {Object.entries(allBadges).map(([category, badges]) => (
                  <ListGroup.Item key={category}>
                    <h6>{category}</h6>
                    <ListGroup variant="flush">
                      {badges.map((badge) => (
                        <ListGroup.Item
                          key={badge.name}
                          action
                          active={compareBadges(badge, activeBadge)}
                          onClick={() => setActiveBadge(badge)}
                        >
                          {badge.name}
                        </ListGroup.Item>
                      ))}
                    </ListGroup>
                  </ListGroup.Item>
                ))}
              </ListGroup>

              <hr className="d-sm-none my-5" />

              <div className="overflow-hidden">
                <div className="font-monospace mx-xl-3 p-xl-5 d-flex">
                  <SyntaxHighlighter
                    language={activeFormat.name.toLowerCase()}
                    style={isDarkMode ? oneDark : oneLight}
                  >
                    {badgeEmbed}
                  </SyntaxHighlighter>
                  <span>
                    <CopyToClipboard textToCopy={badgeEmbed} />
                  </span>
                </div>

                <Image
                  alt={activeBadge.name}
                  src={activeBadge.uri.href()}
                  className="d-block mx-auto mt-5 m-b-3"
                />
              </div>

              <div className="d-none d-sm-block vr my-5"></div>

              <hr className="d-sm-none my-5" />

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
