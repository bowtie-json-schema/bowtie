import { useContext, useEffect, useMemo, useRef, useState } from "react";
import CopyToClipboard from "../CopyToClipboard";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import {
  oneLight,
  oneDark,
} from "react-syntax-highlighter/dist/esm/styles/prism";
import { ThemeContext } from "../../context/ThemeContext";
import Card from "react-bootstrap/Card";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";

const SchemaDisplay = ({
  schema,
  instance,
  modalBodyId,
}: {
  instance: unknown;
  schema: Record<string, unknown> | boolean;
  modalBodyId?: string;
}) => {
  const { isDarkMode } = useContext(ThemeContext);
  const schemaFormatted = JSON.stringify(schema, null, 2);
  const instanceFormatted = JSON.stringify(instance, null, 2);

  const cardRef = useRef<HTMLDivElement | null>(null);
  const [isHighlighted, setIsHighlighted] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      if (cardRef.current) {
        const rect = cardRef.current.getBoundingClientRect();

        const toHighlight =
          rect.top - 1500 <=
            (window.innerHeight || document.documentElement.clientHeight) &&
          rect.right <=
            (window.innerWidth || document.documentElement.clientWidth);

        if (!isHighlighted && toHighlight) {
          setIsHighlighted(toHighlight);
        }
      }
    };

    const modal = document.getElementById(modalBodyId as string);

    if (modal) {
      modal.addEventListener("scroll", handleScroll);
    } else {
      window.addEventListener("scroll", handleScroll);
    }

    handleScroll();

    return () => {
      if (modal) {
        modal.removeEventListener("scroll", handleScroll);
      } else {
        window.removeEventListener("scroll", handleScroll);
      }
    };
  }, [modalBodyId]);

  const MemoizedSchemaHighlighter = useMemo(() => {
    return (
      <SyntaxHighlighter
        language="json"
        style={isDarkMode ? oneDark : oneLight}
      >
        {schemaFormatted}
      </SyntaxHighlighter>
    );
  }, [isDarkMode, schemaFormatted]);

  const MemoizedInstanceHighlighter = useMemo(() => {
    return (
      <SyntaxHighlighter
        language="json"
        style={isDarkMode ? oneDark : oneLight}
      >
        {instanceFormatted}
      </SyntaxHighlighter>
    );
  }, [isDarkMode, instanceFormatted]);

  return (
    <Card className="mb-3 mw-100">
      <Row className="d-flex">
        <Col md={8} className="pe-0">
          <div className="d-flex align-items-center highlight-toolbar ps-3 pe-2 py-1 border-0 border-top border-bottom">
            <small className="font-monospace text-body-secondary text-uppercase">
              Schema
            </small>
            <div className="d-flex ms-auto"></div>
          </div>
          <Card.Body ref={cardRef} className="position-relative">
            <CopyToClipboard
              textToCopy={schemaFormatted}
              style="position-absolute top-0 end-0 mt-4 me-4"
            />
            {isHighlighted ? (
              <>{MemoizedSchemaHighlighter}</>
            ) : (
              <pre>{schemaFormatted}</pre>
            )}
          </Card.Body>
        </Col>
        <Col md={4} className="border-start px-0">
          <div className="d-flex align-items-center highlight-toolbar ps-3 pe-2 py-1 border-0 border-top border-bottom">
            <small className="font-monospace text-body-secondary text-uppercase pe-4">
              Instance
            </small>
            <div className="d-flex ms-auto"></div>
          </div>
          <Card.Body id="instance-info" className="position-relative">
            <CopyToClipboard
              textToCopy={instanceFormatted}
              style="position-absolute top-0 end-0 mt-4 me-4"
            />
            {isHighlighted ? (
              <>{MemoizedInstanceHighlighter}</>
            ) : (
              <pre>{schemaFormatted}</pre>
            )}
          </Card.Body>
        </Col>
      </Row>
    </Card>
  );
};

export default SchemaDisplay;
