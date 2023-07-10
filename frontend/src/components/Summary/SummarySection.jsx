import SummaryTable from "./SummaryTable";

const SummarySection = ({ reportData }) => {
  return (
    <div className="card mx-auto mb-3 w-75" id="summary">
      <div className="card-header">Summary</div>
      <div className="card-body">
        <SummaryTable reportData={reportData} />
        {reportData.didFailFast && (
          <div className="alert alert-warning" role="alert">
            This run failed fast, so some input cases may not have been run.
          </div>
        )}
      </div>
    </div>
  );
};

export default SummarySection;
