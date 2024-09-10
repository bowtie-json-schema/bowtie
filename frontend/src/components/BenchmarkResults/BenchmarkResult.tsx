import { useEffect, useState, useTransition, useRef } from "react";
import Accordion from "react-bootstrap/Accordion";

import { BenchmarkGroupResult } from "../../data/parseBenchmarkData";
import BenchmarkSummarySection from "./BenchmarkSummarySection";
import DetailedBenchmarkResult from "./DetailedBenchmarkResult";

const BenchmarkResult = ({
  benchmarkResult,
}: {
  benchmarkResult: BenchmarkGroupResult;
}) => {
  const [content, setContent] = useState(<></>);
  const [, startTransition] = useTransition();
  const schemaDisplayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    startTransition(() =>
      setContent(
        <>
          <BenchmarkSummarySection benchmarkResults={[benchmarkResult]} />
          <DetailedBenchmarkResult benchmarkGroupResult={benchmarkResult} />
        </>,
      ),
    );
  }, [benchmarkResult]);
  return (
    <Accordion.Item ref={schemaDisplayRef} eventKey={benchmarkResult.name}>
      <Accordion.Header>
        <div className="container-fluid">
          <div className="row">
            <div className="col-12 fw-bold mb-2">{benchmarkResult.name}</div>
            <div className="col-12">{benchmarkResult.description}</div>
          </div>
        </div>
      </Accordion.Header>
      <Accordion.Body>{content}</Accordion.Body>
    </Accordion.Item>
  );
};

export default BenchmarkResult;
