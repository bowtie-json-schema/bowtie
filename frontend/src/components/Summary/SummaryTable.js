import { RunInfo } from "../../data/runInfo";
import ImplementationRow from "./ImplementationRow";

const SummaryTable = ({ lines }) => {
  const runInfo = new RunInfo(lines);
  const summary = runInfo.createSummary();
  const implementationArray = lines.filter((element) => element.implementation);
  const caseArray = lines.filter((each) => each.case);

  const totalCases = caseArray.length;
  const totalTests = caseArray.reduce((total, eachCase) => {
    const caseTests = eachCase.case.tests;
    const caseTestCount = caseTests.length;
    return total + caseTestCount;
  }, 0);

  function getTotal() {
    let erroredCases = 0;
    let skippedTests = 0;
    let failedTests = 0;
    let erroredTests = 0;

    implementationArray.forEach((element) => {
      if (element.skipped) {
        let seq = element.seq;
        caseArray.forEach((each) => {
          if (each.seq == seq) {
            skippedTests += each.case.tests.length;
          }
        });
      } else if (element.results) {
        let caseResults = element.results.filter((element) => element.skipped);
        if (caseResults.length > 0) {
          let seq = element.seq;
          caseArray.forEach((each) => {
            if (each.seq === seq) {
              skippedTests += each.case.tests.length;
            }
          });
        }
      }
      if (
        element.results &&
        element.results.every(
          (each) =>
            typeof each === "object" &&
            Object.keys(each).length === 1 &&
            "valid" in each,
        )
      ) {
        failedTests += element.results.reduce((acc, result, index) => {
          if (result.valid !== element.expected[index]) {
            return acc + 1;
          }
          return acc;
        }, 0);
      }
      let seq = element.seq;
      const caseImplementation = caseArray.find((each) => each.seq === seq);
      if (
        element.caught === true ||
        element.caught === false ||
        (element.results &&
          element.results.every(
            (each) =>
              typeof each === "object" && each.hasOwnProperty("errored"),
          ))
      ) {
        if (caseImplementation) {
          erroredTests += caseImplementation.case.tests.length;
        }
      }
      erroredCases = implementationArray.filter(
        (element) => element.caught === true || element.caught === false,
      ).length;
    });

    return { erroredCases, skippedTests, failedTests, erroredTests };
  }

  return (
    <table className="table table-sm table-hover">
      <thead>
        <tr>
          <th
            colSpan={2}
            rowSpan={2}
            scope="col"
            className="text-center align-middle"
          >
            implementation
          </th>
          <th colSpan={1} className="text-center">
            <span className="text-muted">cases ({totalCases})</span>
          </th>
          <th colSpan={3} className="text-center">
            <span className="text-muted">tests ({totalTests})</span>
          </th>
          <th colSpan={1}></th>
        </tr>
        <tr>
          <th scope="col" className="text-center">
            errors
          </th>
          <th scope="col" className="table-bordered text-center">
            skipped
          </th>
          <th
            scope="col"
            className="table-bordered text-center details-required"
          >
            <div className="hover-details details-desc text-center">
              <p>
                failed
                <br />
                <span>
                  implementation worked successfully but got the wrong answer
                </span>
              </p>
              <p>
                errored
                <br />
                <span>
                  implementation crashed when trying to calculate an answer
                </span>
              </p>
            </div>
            unsuccessful
          </th>
          <th scope="col"></th>
        </tr>
      </thead>
      <tbody className="table-group-divider">
        {summary.implementations.map((implementation, index) => (
          <ImplementationRow
            lines={lines}
            implementation={implementation}
            key={index}
            index={index}
          />
        ))}
      </tbody>
      <tfoot>
        <tr>
          <th scope="row" colSpan={2}>
            total
          </th>
          <td className="text-center">{getTotal().erroredCases}</td>
          <td className="text-center">{getTotal().skippedTests}</td>
          <td className="text-center details-required">
            {getTotal().failedTests + getTotal().erroredTests}
            <div className="hover-details text-center">
              <p>
                <b>failed</b>: {getTotal().failedTests}
              </p>
              <p>
                <b>errored</b>: {getTotal().erroredTests}
              </p>
            </div>
          </td>
          <td></td>
        </tr>
      </tfoot>
    </table>
  );
};

export default SummaryTable;
