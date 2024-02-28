import { ChangeEvent, useState } from "react";
import { ReportData, CaseResult } from "../../data/parseReportData";
import CaseItem from "./CaseItem";
import { Accordion, Row, Col, DropdownButton, Dropdown } from "react-bootstrap";

const CasesSection = ({ reportData }: { reportData: ReportData }) => {
  const [searchText, setSearchText] = useState<string>('');
  const [filterCriteria, setFilterCriteria] = useState<string | null>(null);

  const handleSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value.toLowerCase());
  };

  const handleFilterChange = (criteria: string | null) => {
    setFilterCriteria(criteria);
  };

  const filteredCases = Array.from(reportData.cases.entries())
    .filter(([seq,]) => {
      if (!filterCriteria) return true;
      const caseResults: (CaseResult | undefined)[] = Array.from(reportData.implementations.values())
        .map(impl => impl.cases.get(seq))
        .flat();
      switch (filterCriteria) {
        case "successful":
          return caseResults.some(result => result?.state === "successful");
        case "errors":
          return caseResults.some(result => result?.state === "errored");
        case "skipped":
          return caseResults.some(result => result?.state === "skipped");
        case "failed":
          return caseResults.some(result => result?.state === "failed");
        default:
          return true;
      }
    })
    .filter(([, caseData]) => caseData.description.toLowerCase().includes(searchText));

  // Function to highlight search text in description
  const highlightDescription = (description: string): JSX.Element => {
    if (!searchText) {
      return <>{description}</>;
    }

    const regex = new RegExp(`(${searchText})`, "gi");
    const parts = description.split(regex);
    return (
      <>
        {parts.map((part, index) =>
          regex.test(part) ? (
            <mark key={index} className="bg-primary text-dark">
              {part}
            </mark>
          ) : (
            <span key={index}>{part}</span>
          )
        )}
      </>
    );
  };

  return (
    <div>
      <Row className="mt-3">
        <Col md={{ span: 6, offset: 6 }} className="d-flex align-items-center justify-content-end">
          <input
            type="text"
            onChange={handleSearchChange}
            placeholder="Search"
            className="form-control me-2"
          />
          <DropdownButton
            title={filterCriteria ? `Filter: ${filterCriteria}` : "Filter"}
            variant="secondary"
            id="dropdown-basic-button"
          >
            <Dropdown.Item onClick={() => handleFilterChange(null)}>All</Dropdown.Item>
            <Dropdown.Item onClick={() => handleFilterChange("successful")}>Successful</Dropdown.Item>
            <Dropdown.Item onClick={() => handleFilterChange("errors")}>Errors</Dropdown.Item>
            <Dropdown.Item onClick={() => handleFilterChange("skipped")}>Skipped</Dropdown.Item>
            <Dropdown.Item onClick={() => handleFilterChange("failed")}>Unsuccessful</Dropdown.Item>
          </DropdownButton>
        </Col>
      </Row>
      <div className="overflow-auto mt-3 mb-3 border rounded relative" style={{ maxHeight: "70vh", height: "70vh"}}>
        {filteredCases.length === 0 && (
          <div className="position-absolute top-50 start-50 translate-middle">No matches found</div>
        )}
        {filteredCases.length > 0 && (
          <Accordion id="cases">
            {filteredCases.map(([seq, caseData], index) => (
              <CaseItem
                key={index}
                seq={seq}
                caseData={{
                  ...caseData,
                  description: highlightDescription(caseData.description)
                }}
                implementations={Array.from(reportData.implementations.values())}
              />
            ))}
          </Accordion>
        )}
      </div>
    </div>
  );
};

export default CasesSection;
