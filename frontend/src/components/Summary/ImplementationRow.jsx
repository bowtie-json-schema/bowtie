import "./ImplementationRow.css";
import { InfoCircleFill } from "react-bootstrap-icons";

const ImplementationRow = ({ lines, implementation, index }) => {
  const implementationArray = lines.filter((element) => element.implementation);
  const caseArray = lines.filter((element) => element.case);

  function skippedTests(implementationImage) {
    let count = 0;

    implementationArray.forEach((element) => {
      if (element.implementation === implementationImage) {
        if (element.skipped) {
          let seq = element.seq;
          caseArray.forEach((each) => {
            if (each.seq == seq) {
              count += each.case.tests.length;
            }
          });
        } else if (element.results) {
          let caseResults = element.results.filter(
            (element) => element.skipped,
          );
          if (caseResults.length > 0) {
            let seq = element.seq;
            caseArray.forEach((each) => {
              if (each.seq === seq) {
                count += each.case.tests.length;
              }
            });
          }
        }
      }
    });
    return count;
  }

  function failedTests(implementationImage) {
    let count = 0;

    implementationArray.forEach(({ implementation, results, expected }) => {
      if (implementation === implementationImage && results && expected) {
        if (
          results.every(
            (element) =>
              typeof element === "object" &&
              Object.keys(element).length === 1 &&
              "valid" in element,
          )
        ) {
          count += results.reduce((acc, result, index) => {
            if (result.valid !== expected[index]) {
              return acc + 1;
            }
            return acc;
          }, 0);
        }
      }
    });
    return count;
  }

  function erroredTests(implementationImage) {
    let count = 0;

    implementationArray.forEach((element) => {
      if (element.implementation === implementationImage) {
        const seq = element.seq;
        const caseImplementation = caseArray.find((each) => each.seq === seq);
        if (
          element.caught !== undefined ||
          (element.results && element.results.every((each) => each.errored))
        ) {
          if (caseImplementation) {
            count += caseImplementation.case.tests.length;
          }
        }
      }
    });
    return count;
  }

  function erroredCases(implementationImage) {
    let count = 0;
    lines.forEach((element) => {
      if (element.implementation == implementationImage) {
        if (element.caught !== undefined) {
          let seq = element.seq;
          caseArray.forEach((each) => {
            if (each.seq == seq) {
              count += 1;
            }
          });
        }
      }
    });
    return count;
  }

  return (
    <tr>
      <th scope="row">
        <a href={implementation.homepage || implementation.issues}>
          {implementation.name}
        </a>
        <small className="text-muted">{" " + implementation.language}</small>
      </th>
      <td>
        <small className="font-monospace text-muted">
          {implementation.version || ""}
        </small>
        <button
          className="btn border-0"
          data-bs-toggle="modal"
          data-bs-target={`#implementation-${index}-runtime-info`}
        >
          <InfoCircleFill />
        </button>
      </td>

      <td className="text-center">{erroredCases(implementation.image)}</td>
      <td className="text-center">{skippedTests(implementation.image)}</td>
      <td className="text-center details-required">
        {failedTests(implementation.image) + erroredTests(implementation.image)}
        <div className="hover-details text-center">
          <p>
            <b>failed</b>:{failedTests(implementation.image)}
          </p>
          <p>
            <b>errored</b>:{erroredTests(implementation.image)}
          </p>
        </div>
      </td>

      <td>
        <button
          type="button"
          className="btn btn-sm btn-primary"
          data-bs-toggle="modal"
          data-bs-target={`#implementation-${index}-details`}
        >
          Details
        </button>
      </td>
    </tr>
  );
};

export default ImplementationRow;
