import { useRef, useState } from "react";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Overlay from "react-bootstrap/Overlay";
import Popover from "react-bootstrap/Popover";
import Row from "react-bootstrap/Row";
import { InfoCircle } from "react-bootstrap-icons";
import { NavLink } from "react-router";

import { mapLanguage } from "../data/mapLanguage";
import Dialect from "../data/Dialect";
import Implementation from "../data/Implementation";

interface Props {
  otherImplementationsData: Map<string, Implementation>;
}

export const OtherImplementations = ({ otherImplementationsData }: Props) => {
  const [showPopover, setShowPopover] = useState(false);
  const overlayRef = useRef<HTMLDivElement>(null);
  const popoverTimeoutRef = useRef<number | undefined>(undefined);

  return (
    <div
      ref={overlayRef}
      className="d-flex align-items-center"
      onMouseEnter={() => {
        setShowPopover(true);
        clearTimeout(popoverTimeoutRef.current);
      }}
      onMouseLeave={() => {
        popoverTimeoutRef.current = window.setTimeout(() => {
          setShowPopover(false);
        }, 300);
      }}
    >
      <div>
        <Overlay
          placement="left-end"
          show={showPopover}
          target={overlayRef.current}
          transition={false}
        >
          {(props) => (
            <Popover id="popover-basic" {...props}>
              <Popover.Body>
                <Container className="p-0">
                  <Row className="d-grid gap-2">
                    {Array.from(otherImplementationsData.values()).map(
                      (impl) => {
                        const latest = getLatestSupportedDialect(impl);
                        return (
                          <Col key={impl.id}>
                            <div>
                              <NavLink
                                className="fw-bold"
                                style={{ fontSize: "1rem" }}
                                to={impl.routePath}
                              >
                                {impl.name}
                              </NavLink>
                              <span className="ps-1 text-body-secondary fw-bold">
                                {mapLanguage(impl.language)}
                              </span>
                            </div>
                            <span className="text-body-secondary text-nowrap">
                              (latest supported dialect:{" "}
                              <NavLink to={latest.routePath}>
                                {latest.prettyName}
                              </NavLink>
                              )
                            </span>
                          </Col>
                        );
                      },
                    )}
                  </Row>
                </Container>
              </Popover.Body>
            </Popover>
          )}
        </Overlay>
        <div className="d-flex align-items-center text-body-secondary">
          <InfoCircle />
        </div>
      </div>
      <div className="ps-2 text-body-secondary">
        Other implementations are available which do not support the current
        dialect and filters.
      </div>
    </div>
  );
};

const getLatestSupportedDialect = (impl: Implementation): Dialect => {
  return impl.dialects.reduce((acc, curr) =>
    curr.firstPublicationDate > acc.firstPublicationDate ? curr : acc,
  );
};
