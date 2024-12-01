import { useContext, useState } from "react";
import { useOutletContext, useNavigate } from "react-router";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import {
  oneDark,
  oneLight,
} from "react-syntax-highlighter/dist/esm/styles/prism";
import Container from "react-bootstrap/Container";
import Image from "react-bootstrap/Image";
import ListGroup from "react-bootstrap/ListGroup";
import Modal from "react-bootstrap/Modal";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";

import styles from "./EmbedBadges.module.css";
import CopyToClipboard from "../CopyToClipboard";
import Implementation from "../../data/Implementation";
import { Badge } from "../../data/Badge";
import { ThemeContext } from "../../context/ThemeContext";

export type EmbedBadgesContextType = Implementation;

const EmbedBadges = () => {
  const navigate = useNavigate();
  const implementation = useOutletContext<EmbedBadgesContextType>();
  const allBadges = implementation.badges();
  const { isDarkMode } = useContext(ThemeContext);

  const [activeFormat, setActiveFormat] = useState(supportedFormats[1]);
  const [activeBadge, setActiveBadge] = useState(allBadges.Metadata[0]);
  const [show, setShow] = useState(true);
  const badgeEmbed = activeFormat.generateEmbed(activeBadge);

  return (
    <Modal
      fullscreen="xl-down"
      contentClassName="px-4"
      dialogClassName={styles["modal-width"]}
      show={show}
      onHide={() => setShow(false)}
      onExited={() => navigate(implementation.routePath)}
    >
      <Modal.Header closeButton className="border-0 mt-4">
        <Modal.Title className="fs-5 ms-3">Badges</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Container className="px-5">
          <Row className="pb-3 gap-5 align-items-center">
            <Col sm={5} md={3} lg={2} className="order-2 order-md-1">
              <div>
                {Object.entries(allBadges).map(([category, badges]) => (
                  <div key={category}>
                    <h6>{category}</h6>
                    <ListGroup variant="flush" className="pb-2">
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
                  </div>
                ))}
              </div>
            </Col>

            <Col
              sm={12}
              md={8}
              lg={6}
              xl
              className="overflow-auto order-1 order-md-2"
            >
              <div className="pb-3">
                <p>
                  Bowtie regularly rebuilds a number of badges for
                  <code> {implementation.name}</code>.
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
              <div className="font-monospace d-flex position-relative rounded mx-5">
                <span className="m-2 position-absolute top-0 end-0">
                  <CopyToClipboard textToCopy={badgeEmbed} />
                </span>
                <SyntaxHighlighter
                  language={activeFormat.name.toLowerCase()}
                  style={isDarkMode ? oneDark : oneLight}
                  className={styles["code-block"]}
                  wrapLongLines
                >
                  {badgeEmbed}
                </SyntaxHighlighter>
              </div>

              <Image
                alt={activeBadge.name}
                src={activeBadge.uri.href()}
                className="d-block mx-auto my-5"
              />
              <hr className="mx-5 d-lg-none" />
            </Col>

            <div className="vr my-lg-5 px-0 order-3 d-none d-sm-block d-md-none d-lg-block"></div>
            <Col sm={4} md={5} lg xl={2} className="order-4 px-lg-0 pb-1">
              <hr className="hr d-block d-sm-none order-3 m-5 mt-0"></hr>
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
            </Col>
          </Row>
        </Container>
      </Modal.Body>
    </Modal>
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
