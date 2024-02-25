import { Button, OverlayTrigger, Popover } from "react-bootstrap";
import { NavLink } from "react-router-dom";
import { Implementation } from "../data/parseReportData";
import { mapLanguage } from "../data/mapLanguage";

interface Props {
  otherImplementationsData: Record<string, Implementation>;
}

export const OtherImplementations = ({ otherImplementationsData }: Props) => {
  return (
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
                    <small className="ps-1">{mapLanguage(impl.language)}</small>
                  </p>
                );
              }
            )}
          </Popover.Body>
        </Popover>
      }
    >
      <Button variant="link" style={{ padding: 0 }}>
        {"There are other implementations besides the above"}
      </Button>
    </OverlayTrigger>
  );
};

const getImplementationPath = (id: string): string => {
  const pathSegment = id.split("/");
  return pathSegment[pathSegment.length - 1];
};
