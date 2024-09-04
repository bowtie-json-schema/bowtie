import Accordion from "react-bootstrap/Accordion";
import { BenchmarkGroupResult } from "../../data/parseBenchmarkData";
import ListGroup from "react-bootstrap/ListGroup";
import BenchmarkResult from "./BenchmarkResult";
import Badge from "react-bootstrap/Badge";
import { titleCase } from "title-case";

const BenchmarkTypeResultSection = ({
  benchmarkType,
  benchmarkResults,
}: {
  benchmarkType: string;
  benchmarkResults: BenchmarkGroupResult[];
}) => {
  return (
    <ListGroup.Item
      as="li"
      className="d-flex justify-content-between align-items-start"
    >
      <div className="ms-2 me-auto">
        <div className="fw-bold mb-4 mt-2 ">
          Benchmark Type: {titleCase(benchmarkType)}
        </div>
        <Accordion id="benchmarks" className="mb-4">
          {benchmarkResults.map((benchmarkResult) => (
            <BenchmarkResult
              key={benchmarkResult.name}
              benchmarkResult={benchmarkResult}
            />
          ))}
        </Accordion>
      </div>
      <Badge bg="primary" className="mt-2" pill>
        {benchmarkResults.length}
      </Badge>
    </ListGroup.Item>
  );
};

export default BenchmarkTypeResultSection;
