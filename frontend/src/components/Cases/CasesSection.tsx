import { ChangeEvent, useMemo, useState } from "react";
import { ReportData, CaseResult } from "../../data/parseReportData";
import CaseItem from "./CaseItem";
import Accordion from "react-bootstrap/Accordion";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import ButtonGroup from "react-bootstrap/ButtonGroup";
import Dropdown from "react-bootstrap/Dropdown";
import Form from "react-bootstrap/Form";

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

  const filteredCases = useMemo(() => {
    const trimmedSearchText = searchText.trim();

    return Array.from(reportData.cases.entries())
      .filter(([seq]) => {
        if (filterCriteria.length === 0) return true;

        const caseResults: CaseResult[] = Array.from(
          reportData.implementationsResults.values(),
        )
          .map((implResult) => implResult.caseResults.get(seq))
          .filter((result) => result !== undefined)
          .map((result) => result![0]);

        return caseResults.some((result) =>
          filterCriteria.includes(result?.state ?? ""),
        );
      })
      .filter(([, caseData]) => {
        return caseData.description.toLowerCase().includes(trimmedSearchText);
      });
  }, [reportData, filterCriteria, searchText]);

  const implementationsResults = Array.from(
    reportData.implementationsResults.values(),
  );
  const implementations = Array.from(
    reportData.runMetadata.implementations.values(),
  );

  return (
    <div>
      <Row className="mt-3">
        <Col md={6}>
          <div className="input-group">
            <span className="input-group-text">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                fill="currentColor"
                className="bi bi-search"
                viewBox="0 0 16 16"
              >
                <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001q.044.06.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1 1 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0" />
              </svg>
            </span>
            <input
              type="text"
              onChange={handleSearchChange}
              placeholder="Search"
              className="form-control me-2"
            />
          </div>
        </Col>
        <Col md={3} className="d-flex align-items-center justify-content-end">
          {filteredCases.length} result(s)
        </Col>
        <Col md={3} className="d-flex align-items-center justify-content-end">
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
                caseData={caseData}
                implementations={implementations}
                implementationsResults={implementationsResults}
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
