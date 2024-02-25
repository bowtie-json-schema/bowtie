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

  return (
    <Accordion id="cases">
      <Row>
        <Col md={{ span: 6, offset: 6 }} className="d-flex align-items-center justify-content-end">
          <input
            type="text"
            onChange={handleSearchChange}
            placeholder="Search"
            className="form-control m-4"
          />
          <DropdownButton
            title={filterCriteria ? `Filter: ${filterCriteria}` : "Filter"}
            variant="secondary"
            id="dropdown-basic-button"
          >
            <Dropdown.Item onClick={() => handleFilterChange(null)}>All</Dropdown.Item>
            <Dropdown.Item onClick={() => handleFilterChange("errors")}>Errors</Dropdown.Item>
            <Dropdown.Item onClick={() => handleFilterChange("skipped")}>Skipped</Dropdown.Item>
            <Dropdown.Item onClick={() => handleFilterChange("failed")}>Failed</Dropdown.Item>
          </DropdownButton>
        </Col>
      </Row>
      {Array.from(reportData.cases.entries())
        .filter(([seq, ]) => {
          if (!filterCriteria) return true;
          const caseResults: (CaseResult | undefined)[] = Array.from(reportData.implementations.values())
            .map(impl => impl.cases.get(seq))
            .flat();
          switch (filterCriteria) {
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
        .filter(([, caseData]) => caseData.description.toLowerCase().includes(searchText))
        .map(([seq, caseData], index) => (
          <CaseItem
            key={index}
            seq={seq}
            caseData={caseData}
            implementations={Array.from(reportData.implementations.values())}
          />
        ))}
    </Accordion>
  );
};

export default CasesSection;
