import "./ImplementationRow.css";

const ImplementationRow = ({ lines, implementation, counts, index }) => {
  function skipped_tests(implementationImage) {
    // console.log(implementationImage);
    let count = 0;
    // console.log(lines);
    lines.map((element) => {
      const propertyObjectArray = Object.keys(element);
      if (propertyObjectArray[0] == "implementation") {
        if (element.implementation == implementationImage) {
          if (element.results) {
            // console.log(element['results'])
            element["results"].map((each) => {
              if (each.hasOwnProperty("skipped")) {
                count += 1;
              }
            });
          }
        }
      }
    });
    // console.log(count)
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

      <td className="text-center">{}</td>
      <td className="text-center">
        {skipped_tests(implementation.image)}
      </td>
      <td className="text-center details-required">
        {counts.failed_tests + counts.errored_tests}
        <div className="hover-details text-center">
          <p>
            <b>failed</b>:{counts.failed_tests}
          </p>
          <p>
            <b>errored</b>:{counts.errored_tests}
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
