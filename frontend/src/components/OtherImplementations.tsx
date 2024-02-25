import { useRef, useState } from "react";
import { Overlay, Popover } from "react-bootstrap";
import { InfoCircle } from "react-bootstrap-icons";
import { NavLink } from "react-router-dom";
import { Implementation } from "../data/parseReportData";
import { mapLanguage } from "../data/mapLanguage";

interface Props {
  otherImplementationsData: Record<string, Implementation>;
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
        }, 400);
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
                {Object.entries(otherImplementationsData).map(
                  ([id, impl], index) => {
                    const implementationPath = getImplementationPath(id);
                    return (
                      <p key={index}>
                        <NavLink
                          style={{ fontSize: "1rem", fontWeight: "bold" }}
                          to={`/implementations/${implementationPath}`}
                        >
                          {impl.name}
                        </NavLink>
                        <span className="ps-1 text-body-secondary fw-bold">
                          {mapLanguage(impl.language)}
                        </span>
                      </p>
                    );
                  },
                )}
              </Popover.Body>
            </Popover>
          )}
        </Overlay>
        <div className="d-flex align-items-center text-body-secondary">
          <InfoCircle />
        </div>
      </div>
      <div className="text-body-secondary ps-2">
        {
          "Other implementations are available which do not support the current dialect and filters."
        }
      </div>
    </div>
  );
};

const getImplementationPath = (id: string): string => {
  const pathSegment = id.split("/");
  return pathSegment[pathSegment.length - 1];
};
