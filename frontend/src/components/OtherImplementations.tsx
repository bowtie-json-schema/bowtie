import { Button, OverlayTrigger, Popover } from "react-bootstrap";
import { InfoCircleFill } from "react-bootstrap-icons";
import { NavLink } from "react-router-dom";
import { Implementation } from "../data/parseReportData";
import { mapLanguage } from "../data/mapLanguage";

interface Props {
  otherImplementationsData: Record<string, Implementation>;
}

export const OtherImplementations = ({ otherImplementationsData }: Props) => {
  return (
    <div className="d-flex align-items-center">
      <div className="text-body-secondary">
        {"There are other implementations besides the above"}
      </div>
      <div>
        <OverlayTrigger
          trigger="focus"
          placement="left-end"
          overlay={
            <Popover id="popover-basic">
              <Popover.Body>
                {Object.entries(otherImplementationsData).map(
                  ([id, impl], index) => {
                    const implementationPath = getImplementationPath(id);
                    return (
                      <p key={index}>
                        <NavLink to={`/implementations/${implementationPath}`}>
                          {impl.name}
                        </NavLink>
                        <small className="ps-1">
                          {mapLanguage(impl.language)}
                        </small>
                      </p>
                    );
                  },
                )}
              </Popover.Body>
            </Popover>
          }
        >
          <Button variant="none" style={{ border: "none" }}>
            <InfoCircleFill />
          </Button>
        </OverlayTrigger>
      </div>
    </div>
  );
};

const getImplementationPath = (id: string): string => {
  const pathSegment = id.split("/");
  return pathSegment[pathSegment.length - 1];
};
