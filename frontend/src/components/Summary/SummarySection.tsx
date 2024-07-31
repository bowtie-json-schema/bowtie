import Alert from "react-bootstrap/Alert";
import Card from "react-bootstrap/Card";

import SummaryTable from "./SummaryTable";
import Implementation from "../../data/Implementation.ts";
import { ReportData } from "../../data/parseReportData.ts";
import { OtherImplementations } from "../OtherImplementations.tsx";

const SummarySection = ({
  reportData,
  otherImplementationsData,
}: {
  reportData: ReportData;
  otherImplementationsData: Map<string, Implementation>;
}) => {
  return (
    <Card className="mx-auto mb-3" id="summary">
      <Card.Header>Summary</Card.Header>
      <Card.Body>
        <SummaryTable reportData={reportData} />
        {reportData.didFailFast && (
          <Alert variant="warning">
            This run failed fast, so some input cases may not have been run.
          </Alert>
        )}
        {otherImplementationsData.size > 0 && (
          <OtherImplementations
            otherImplementationsData={otherImplementationsData}
          />
        )}
      </Card.Body>
    </Card>
  );
};

export default SummarySection;
