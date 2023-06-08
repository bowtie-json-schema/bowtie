
import React, { useState } from 'react';
import { Check, Clipboard } from 'react-bootstrap-icons';

function CopyToClipboard({ id, textToCopy }) {
  const [copied, setCopied] = useState(false);

  const handleClick = () => {
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => {
      setCopied(false);
    }, 1000);
  };

  return (
    <button
      type="button"
      id={`schema${id}`}
      className="btn mt-0 me-0"
      onClick={handleClick}
      aria-label="Copy to clipboard"
      data-bs-toggle="tooltip"
      data-bs-placement="top"
      data-bs-custom-class="custom-tooltip"
      data-bs-title="Copy to clipboard"
    >
      {copied ? <Check /> : <Clipboard />}
    </button>
  );
}

export default CopyToClipboard;
