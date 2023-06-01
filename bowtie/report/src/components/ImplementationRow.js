import { useContext } from "react";
import { CountsDataContext } from "../data/CountsDataContext";
import "./ImplementationRow.css";
import { Count } from "../data/report";

const ImplementationRow = ({ lines, implementation, counts, index }) => {
  //   const {
  //     updateTotalErroredCases,
  //     updateTotalErroredTests,
  //     updateTotalFailedTests,
  //     updateTotalSkippedTests,
  //   } = useContext(CountsDataContext);

  // updateTotalErroredCases(10)
  const countss = new Count();

  function skipped_tests(implementationImage) {
    let count = 0;
    // console.log(lines);
    lines.map((element) => {
      const propertyObjectArray = Object.keys(element);
      if (propertyObjectArray[0] == "implementation") {
        if (element.implementation == implementationImage) {
          if (element.skipped) {
            // console.log(element['results'])
            var seq = element.seq;
            lines.map((each) => {
              if (each.case && each.seq == seq) {
                count += each.case.tests.length;
              }
            });
          }
        }
      }
    });
    // updateTotalSkippedTests(count);
    return count;
  }

  function failed_tests(implementationImage) {
    var count = 0;
    lines.map((element) => {
      const propertyObjectArray = Object.keys(element);
      if (propertyObjectArray[0] == "implementation") {
        if (element.implementation == implementationImage) {
          if (element.results && element.expected) {
            for (let i = 0; i < element.results.length; i++) {
              if (element.results[i].valid !== element.expected[i]) {
                count += 1;
              }
            }
          }
        }
      }
    });
    // updateTotalFailedTests(count);
    return count;
  }

  function errored_tests(implementationImage) {
    var count = 0;
    lines.map((element) => {
      if (element.implementation == implementationImage) {
        // console.log(cases);
        if (element.caught) {
          var seq = element.seq;
          // console.log(seq)
          lines.map((each) => {
            if (each.case && each.seq == seq) {
              count += each.case.tests.length;
            }
          });
        }
      }
    });
    // updateTotalErroredTests(count);
    return count;
  }

  function errored_cases(implementationImage) {
    var count = 0;
    lines.map((element) => {
      if (element.implementation == implementationImage) {
        if (element.caught) {
          var seq = element.seq;
          // console.log(seq)
          lines.map((each) => {
            if (each.case && each.seq == seq) {
              count += 1;
            }
          });
        }
      }
    });
    // updateTotalErroredCases(count);
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
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            fill="currentColor"
            className="bi bi-info-circle-fill"
            viewBox="0 0 16 16"
          >
            <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm.93-9.412-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381 2.29-.287zM8 5.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2z" />
          </svg>
        </button>
      </td>

      <td className="text-center">{errored_cases(implementation.image)}</td>
      <td className="text-center">{skipped_tests(implementation.image)}</td>
      <td className="text-center details-required">
        {failed_tests(implementation.image) +
          errored_tests(implementation.image)}
        <div className="hover-details text-center">
          <p>
            <b>failed</b>:{failed_tests(implementation.image)}
          </p>
          <p>
            <b>errored</b>:{errored_tests(implementation.image)}
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
