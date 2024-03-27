import { useState } from "react";
import { Check, Copy } from "react-bootstrap-icons";
import Button from "react-bootstrap/Button";
import OverlayTrigger from "react-bootstrap/OverlayTrigger";
import Tooltip from "react-bootstrap/Tooltip";

interface CopyProps {
  textToCopy: string;
  style?: string;
}

function CopyToClipboard({ textToCopy, style }: CopyProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard
      .writeText(textToCopy)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      })
      .catch((error) => {
        console.error("Error copying text to clipboard:", error);
      });
  };

  return (
    <>
      <OverlayTrigger
        placement="top"
        overlay={
          <Tooltip id="tooltip-top">
            {copied ? "Copied!" : "Copy to clipboard"}
          </Tooltip>
        }
      >
        <Button variant="secondary" className={style} onClick={handleCopy}>
          {copied ? <Check /> : <Copy />}
        </Button>
      </OverlayTrigger>
    </>
  );
}

export default CopyToClipboard;
