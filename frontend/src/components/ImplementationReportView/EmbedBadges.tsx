import React, { useState } from "react";
import Container from "react-bootstrap/Container";
import DropdownButton from "react-bootstrap/DropdownButton";
import Image from "react-bootstrap/Image";
import ListGroup from "react-bootstrap/ListGroup";
import Stack from "react-bootstrap/Stack";

import CopyToClipboard from "../CopyToClipboard";
import { Implementation } from "../../data/parseReportData";
import { Badge, badgesFor } from "../../data/Badge";

const EmbedBadges: React.FC<{
  implementation: Implementation;
}> = ({ implementation }) => {
  const allBadges = badgesFor(implementation);

  const [activeFormat, setActiveFormat] = useState(supportedFormats[1]);
  const [activeBadge, setActiveBadge] = useState(allBadges.Metadata[0]);

  const badgeEmbed = activeFormat.generateEmbed(activeBadge);

  return (
    <DropdownButton title="Badges" size="sm" align="end" variant="info">
      <Container className="p-5">
        <h5 className="pb-1">Badges</h5>

        <Stack className="pb-3" direction="horizontal" gap={5}>
          <div>
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
          </div>

          <div className="overflow-scroll">
            <div className="pb-3">
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
            </div>

            <hr className="mx-5 py-3" />

            <div className="font-monospace text-bg-dark mx-5 p-5 d-flex">
              <pre className="py-5">{badgeEmbed}</pre>
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
    </DropdownButton>
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
