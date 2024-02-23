import { Accordion } from "react-bootstrap";
import { Implementation } from "../data/parseReportData";
import { NavLink, useParams } from "react-router-dom";
import { mapLanguage } from "../data/mapLanguage";

interface Props {
  otherImplementationsData: Record<string, Implementation>;
}

export const OtherImplementations = ({ otherImplementationsData }: Props) => {
  const { draftName } = useParams();

  return (
    <Accordion className="mx-auto mb-3 w-75">
      <Accordion.Item eventKey="0">
        <Accordion.Header>Other Implementations</Accordion.Header>
        <Accordion.Body>
          <table className="table table-sm table-hover">
            <tbody>
              {Object.entries(otherImplementationsData).map(
                ([id, impl], index) => {
                  const implementationPath = getImplementationPath(id);
                  return (
                    <tr key={index}>
                      <th scope="row">
                        <NavLink to={`/implementations/${implementationPath}`}>
                          {impl.name}
                        </NavLink>
                        <small className="text-muted ps-1">
                          {mapLanguage(impl.language)}
                        </small>
                      </th>
                      <td>
                        <small className="font-monospace text-muted">
                          {impl.version ?? ""}
                        </small>
                      </td>
                      <td>
                        <small>{`Does not support ${draftName}`}</small>
                      </td>
                    </tr>
                  );
                },
              )}
            </tbody>
          </table>
        </Accordion.Body>
      </Accordion.Item>
    </Accordion>
  );
};

const getImplementationPath = (id: string): string => {
  const pathSegment = id.split("/");
  return pathSegment[pathSegment.length - 1];
};
