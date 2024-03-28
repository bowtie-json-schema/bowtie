import React, { useState } from "react";
import Container from "react-bootstrap/Container";
import Image from "react-bootstrap/Image";
import ListGroup from "react-bootstrap/ListGroup";
import Stack from "react-bootstrap/Stack";
import Button from "react-bootstrap/Button";
import Modal from "react-bootstrap/Modal";

import CopyToClipboard from "../CopyToClipboard";
import { Implementation } from "../../data/parseReportData";
import { Badge, badgesFor } from "../../data/Badge";

const EmbedBadges: React.FC<{
  implementation: Implementation;
}> = ({ implementation }) => {
  const allBadges = badgesFor(implementation);

  const [activeFormat, setActiveFormat] = useState(supportedFormats[1]);
  const [activeBadge, setActiveBadge] = useState(allBadges.Metadata[0]);
  const [show, setShow] = useState(false);
  const badgeEmbed = activeFormat.generateEmbed(activeBadge);

  return (
    <>
      <Button variant="info" size="sm" onClick={() => setShow(true)}>
        Badges
      </Button>
      <Modal
        size="xl"
        fullscreen="lg-down"
        show={show}
        onHide={() => setShow(false)}
      >
        <Modal.Header closeButton className="border-0 p-0 px-4 px-md-5 pt-5">
          <Modal.Title className="fs-5">Badges</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Container className="d-none d-sm-block p-2 pb-1 p-lg-5 pt-lg-0">
            <Stack className="pb-3 gap-2 gap-lg-5" direction="horizontal">
              <ListGroup variant="flush">
                {Object.entries(allBadges).map(([category, badges]) => (
                  <ListGroup.Item key={category}>
                    <h6>{category}</h6>
                    <ListGroup variant="flush">
                      {badges.map((badge) => (
                        <ListGroup.Item
                          key={badge.name}
                          action
                          // FIXME: wut? badge === activeBadge is false, at
                          //        least because badge.uri !== activeBadge.uri
                          //        URI.js has a .equal method
                          active={badge.name === activeBadge.name}
                          onClick={() => setActiveBadge(badge)}
                        >
                          {badge.name}
                        </ListGroup.Item>
                      ))}
                    </ListGroup>
                  </ListGroup.Item>
                ))}
              </ListGroup>

              <div className="overflow-hidden">
                <div className="pb-3">
                  <p>
                    Bowtie regularly rebuilds a number of badges for{" "}
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

                <hr className="mx-3 py-3" />

                <div className="font-monospace text-bg-dark mx-xl-5 p-xl-5 d-flex">
                  <pre className="py-5 px-4">{badgeEmbed}</pre>
                  <span>
                    <CopyToClipboard textToCopy={badgeEmbed} />
                  </span>
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
            </Stack>
          </Container>

          <Container className="d-block d-sm-none p-0 pb-1">
            <div>
              <div className="pb-3 mx-2">
                <p>
                  Bowtie regularly rebuilds a number of badges for{" "}
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
              <hr className="mx-3 py-3" />
            </div>

            <Stack
              className="pb-3 gap-3 d-flex align-items-start"
              direction="horizontal"
            >
              <ListGroup variant="flush">
                {Object.entries(allBadges).map(([category, badges]) => (
                  <ListGroup.Item key={category}>
                    <h6>{category}</h6>
                    <ListGroup variant="flush">
                      {badges.map((badge) => (
                        <ListGroup.Item
                          key={badge.name}
                          action
                          active={badge.name === activeBadge.name}
                          onClick={() => setActiveBadge(badge)}
                        >
                          {badge.name}
                        </ListGroup.Item>
                      ))}
                    </ListGroup>
                  </ListGroup.Item>
                ))}
              </ListGroup>

              <div className="vr"></div>

              <div className="p-2">
                <h6>Format</h6>
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
            </Stack>
            <div className="mx-3 mt-5">
              <div className="font-monospace text-bg-dark d-flex">
                <pre className="py-5 px-3">{badgeEmbed}</pre>
                <span>
                  <CopyToClipboard textToCopy={badgeEmbed} />
                </span>
              </div>

              <Image
                alt={activeBadge.name}
                src={activeBadge.uri.href()}
                className="d-block mx-auto my-5"
              />
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
