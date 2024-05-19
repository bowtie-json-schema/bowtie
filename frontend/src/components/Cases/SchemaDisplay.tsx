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
}: {
  instance: unknown;
  schema: Record<string, unknown> | boolean;
}) => {
  const { isDarkMode } = useContext(ThemeContext);
  const schemaFormatted = JSON.stringify(schema, null, 2);
  const instanceFormatted = JSON.stringify(instance, null, 2);

  const cardRef = useRef(null);
  const [isHighlighted, setIsHighlighted] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry.isIntersecting) {
          setIsHighlighted(true);
          observer.unobserve(entry.target);
        }
      },
      { threshold: 0 },
    );

    if (cardRef.current) {
      observer.observe(cardRef.current);
    }

    return () => {
      observer.disconnect();
    };
  }, [cardRef, setIsHighlighted]);

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
    <Card ref={cardRef} className="mb-3 mw-100">
      <Row className="d-flex">
        <Col xs={6} md={8} className="pe-0">
          <div className="d-flex align-items-center highlight-toolbar ps-3 pe-2 py-1 border-0 border-top border-bottom">
            <small className="font-monospace text-body-secondary text-uppercase">
              Schema
            </small>
            <div className="d-flex ms-auto"></div>
          </div>
          <Card.Body className="position-relative">
            <CopyToClipboard
              textToCopy={schemaFormatted}
              style="position-absolute top-0 end-0 mt-4 me-4"
            />
            {isHighlighted ? (
              <>{MemoizedSchemaHighlighter}</>
            ) : (
              <pre>
                <code>{schemaFormatted}</code>
              </pre>
            )}
          </Card.Body>
        </Col>
        <Col xs={6} md={4} className="border-start ps-0">
          <div className="d-flex align-items-center highlight-toolbar ps-3 pe-2 py-1 border-0 border-top border-bottom">
            <small className="font-monospace text-body-secondary text-uppercase pe-4">
              Instance
            </small>
            <div className="d-flex ms-auto"></div>
          </div>
          <Card.Body className="position-relative">
            <CopyToClipboard
              textToCopy={instanceFormatted}
              style="position-absolute top-0 end-0 mt-4 me-4"
            />
            {isHighlighted ? (
              <>{MemoizedInstanceHighlighter}</>
            ) : (
              <pre>
                <code>{instanceFormatted}</code>
              </pre>
            )}
          </Card.Body>
        </Col>
      </Row>
    </Card>
  );
};

export default SchemaDisplay;
