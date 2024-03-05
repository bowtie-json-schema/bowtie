import { ChangeEvent, useState } from "react";
import { ReportData, CaseResult } from "../../data/parseReportData";
import CaseItem from "./CaseItem";
import {
  Accordion,
  Row,
  Col,
  Form,
  Dropdown,
  ButtonGroup,
} from "react-bootstrap";

const CasesSection = ({ reportData }: { reportData: ReportData }) => {
  const [searchText, setSearchText] = useState<string>("");
  const [filterCriteria, setFilterCriteria] = useState<string[]>([]);

  const handleSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value.toLowerCase());
  };

  const handleCheckboxChange = (criteria: string) => {
    if (filterCriteria.includes(criteria)) {
      setFilterCriteria(filterCriteria.filter((item) => item !== criteria));
    } else {
      setFilterCriteria([...filterCriteria, criteria]);
    }
  };

  const filteredCases = Array.from(reportData.cases.entries())
    .filter(([seq]) => {
      if (filterCriteria.length === 0) return true;
      const caseResults: (CaseResult | undefined)[] = Array.from(
        reportData.implementations.values(),
      )
        .map((impl) => impl.cases.get(seq))
        .flat();
      return caseResults.some((result) =>
        filterCriteria.includes(result?.state ?? ""),
      );
    })
    .filter(([, caseData]) => {
      if (typeof caseData.description !== "string") return false;
      const regex = new RegExp(searchText, "i");
      return regex.test(caseData.description);
    });

  return (
    <div>
      <Row className="mt-3">
        <Col
          md={{ span: 6, offset: 6 }}
          className="d-flex align-items-center justify-content-end"
        >
          <input
            type="text"
            onChange={handleSearchChange}
            placeholder="Search"
            className="form-control me-2"
          />
          <Dropdown as={ButtonGroup}>
            <Dropdown.Toggle variant="secondary" id="dropdown-basic">
              {filterCriteria.length > 0
                ? `Filter (${filterCriteria.length} selected)`
                : "Filter by Outcome"}
            </Dropdown.Toggle>

            <Dropdown.Menu>
              {["successful", "errored", "skipped", "failed"].map(
                (criteria, index) => (
                  <Form.Check
                    key={index}
                    type="checkbox"
                    label={criteria.charAt(0).toUpperCase() + criteria.slice(1)}
                    checked={filterCriteria.includes(criteria)}
                    onChange={() => handleCheckboxChange(criteria)}
                    className="ms-2"
                  />
                ),
              )}
            </Dropdown.Menu>
          </Dropdown>
        </Col>
      </Row>
      <div
        className="overflow-auto mt-3 mb-3 border rounded relative"
        style={{ maxHeight: "70vh", height: "70vh" }}
      >
        {filteredCases.length === 0 && (
          <div
            className="d-flex justify-content-center align-items-center"
            style={{ height: "100%" }}
          >
            <div>No matches found</div>
          </div>
        )}

        {filteredCases.length > 0 && (
          <Accordion id="cases">
            {filteredCases.map(([seq, caseData], index) => (
              <CaseItem
                key={index}
                seq={seq}
                caseData={{
                  ...caseData,
                  description: caseData.description,
                }}
                implementations={Array.from(
                  reportData.implementations.values(),
                )}
                searchText={searchText}
              />
            ))}
          </Accordion>
        )}
      </div>
    </div>
  );
};

export default CasesSection;
