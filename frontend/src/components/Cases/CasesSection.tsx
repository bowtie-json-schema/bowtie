import { useEffect, useMemo, useState } from "react";
import { ReportData } from "../../data/parseReportData";
import CaseItem from "./CaseItem";
import { Accordion } from "react-bootstrap";
import { useLocation } from "react-router-dom";

const CasesSection = ({ reportData }: { reportData: ReportData }) => {
  const location = useLocation();
  const implementations = useMemo(
    () => Array.from(reportData.implementations.values()),
    [reportData.implementations],
  );
  const reportCases = useMemo(
    () => Array.from(reportData.cases.entries()),
    [reportData.cases],
  );
  const [activeKey, setActiveKey] = useState<
    string | string[] | null | undefined
  >(null);

  useEffect(() => {
    const handleHashChange = () => {
      const hash = location.hash;
      const hashSplit = hash.split("#");
      const fragment = hashSplit[1];
      setActiveKey(fragment === "" ? null : fragment);
      setTimeout(() => {
        if (fragment) {
          const seq = document.getElementById(fragment);
          const elementRect = seq!.getBoundingClientRect();
          const offsetTop = window.scrollY + elementRect.top;
          window.scrollTo({
            top: offsetTop,
            behavior: "smooth",
          });
        }
      }, 500);
    };
    handleHashChange();
  }, [location.hash]);

  const caseItems = useMemo(() => {
    return reportCases.map(([seq, caseData]) => (
      <CaseItem
        key={seq}
        seq={seq}
        caseData={caseData}
        implementations={implementations}
      />
    ));
  }, [reportCases, implementations]);

  return (
    <Accordion
      id="cases"
      activeKey={activeKey}
      onSelect={(eventKey) => {
        setActiveKey(eventKey);
      }}
    >
      {caseItems}
    </Accordion>
  );
};

export default CasesSection;
