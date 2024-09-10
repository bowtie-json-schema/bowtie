import Table from "react-bootstrap/Table";

import { BenchmarkRunMetadata } from "../../data/parseBenchmarkData";

const BenchmarkRunInfoSection = ({
  benchmarkRunMetadata,
}: {
  benchmarkRunMetadata: BenchmarkRunMetadata;
}) => {
  return (
    <div className="card mx-auto mb-3" id="run-info">
      <div className="card-header">Benchmark Run Info</div>

      <div className="card-body table-responsive-sm">
        <Table size="sm" hover>
          <caption className="caption-top">Run Info</caption>
          <thead>
            <tr>
              <td className="align-top col-md-2">Dialect</td>
              <td>{benchmarkRunMetadata.dialect.uri}</td>
            </tr>
            <tr>
              <td className="align-top col-md-2">Ran</td>
              <td>{benchmarkRunMetadata.ago()}</td>
            </tr>
          </thead>
        </Table>
        <Table size="sm" hover>
          <caption className="caption-top">Benchmarking System Info</caption>
          <thead>
            {benchmarkRunMetadata.systemMetadata.cpuCount && (
              <tr>
                <td className="align-top col-md-2">CPU Count</td>
                <td>
                  {benchmarkRunMetadata.systemMetadata.cpuCount.toString()}
                </td>
              </tr>
            )}
            {benchmarkRunMetadata.systemMetadata.cpuFreq && (
              <tr>
                <td className="align-top col-md-2">CPU Frequency</td>
                <td>
                  {benchmarkRunMetadata.systemMetadata.cpuFreq.toString()}
                </td>
              </tr>
            )}
            {benchmarkRunMetadata.systemMetadata.cpuModel && (
              <tr>
                <td className="align-top col-md-2">CPU Model</td>
                <td>
                  {benchmarkRunMetadata.systemMetadata.cpuModel.toString()}
                </td>
              </tr>
            )}
            <tr>
              <td className="align-top col-md-2">Hostname</td>
              <td>{benchmarkRunMetadata.systemMetadata.hostname}</td>
            </tr>
            <tr>
              <td className="align-top col-md-2">Platform</td>
              <td>{benchmarkRunMetadata.systemMetadata.platform}</td>
            </tr>
            <tr>
              <td className="align-top col-md-2">pyperf Version</td>
              <td>{benchmarkRunMetadata.systemMetadata.perfVersion}</td>
            </tr>
          </thead>
        </Table>
      </div>
    </div>
  );
};

export default BenchmarkRunInfoSection;
