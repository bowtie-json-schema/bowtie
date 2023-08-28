import { useState } from "react";
import { Check, Clipboard } from "react-bootstrap-icons";
import Button from "react-bootstrap/Button";
import OverlayTrigger from "react-bootstrap/OverlayTrigger";
import Tooltip from "react-bootstrap/Tooltip";

function CopyToClipboard({ textToCopy }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => {
      setCopied(false);
    }, 1000);
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
        <Button
          variant="outline-primary"
          className="btn mt-0 me-0"
          onClick={handleCopy}
        >
          {copied ? <Check /> : <Clipboard />}
        </Button>
      </OverlayTrigger>
    </>
  );
}

export default CopyToClipboard;
