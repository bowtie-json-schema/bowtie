import { useRef, useState } from "react";
import { Col, Container, Overlay, Popover, Row } from "react-bootstrap";
import { InfoCircle } from "react-bootstrap-icons";
import { NavLink } from "react-router-dom";
import { Implementation } from "../data/parseReportData";
import { mapLanguage } from "../data/mapLanguage";
import Dialect from "../data/Dialect";

interface Props {
  otherImplementationsData: Record<string, Implementation>;
}

export const OtherImplementations = ({ otherImplementationsData }: Props) => {
  const [showPopover, setShowPopover] = useState(false);
  const overlayRef = useRef<HTMLDivElement>(null);
  const popoverTimeoutRef = useRef<number | undefined>(undefined);
  const otherImplementationsDataArray = Object.entries(
    otherImplementationsData
  );
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
                    {otherImplementationsDataArray.map(([id, impl]) => {
                      const implementationPath = getImplementationPath(id);
                      const ltsDialect = getLatestSupportedDialect(impl);
                      return (
                        <Col key={id}>
                          <div>
                            <NavLink
                              style={{ fontSize: "1rem", fontWeight: "bold" }}
                              to={`/implementations/${implementationPath}`}
                            >
                              {impl.name}
                            </NavLink>
                            <span className="ps-1 text-body-secondary fw-bold">
                              {mapLanguage(impl.language)}
                            </span>
                          </div>
                          <span className="text-body-secondary text-nowrap">
                            (latest supported dialect:{" "}
                            <NavLink to={`/dialects/${ltsDialect.path}`}>
                              {ltsDialect.prettyName}
                            </NavLink>
                            )
                          </span>
                        </Col>
                      );
                    })}
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
      <div className="text-body-secondary ps-2">
        Other implementations are available which do not support the current
        dialect and filters.
      </div>
    </div>
  );
};

const getImplementationPath = (id: string): string => {
  const pathSegment = id.split("/");
  return pathSegment[pathSegment.length - 1];
};

const getLatestSupportedDialect = (impl: Implementation): Dialect => {
  return impl.dialects
    .map((dialectUri) => Dialect.forURI(dialectUri))
    .reduce((acc, curr) =>
      curr.firstPublicationDate > acc.firstPublicationDate ? curr : acc
    );
};
