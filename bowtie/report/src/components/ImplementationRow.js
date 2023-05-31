import infoCircle from "../assets/svg/infoCircle.svg";
import './ImplementationRow.css';

const ImplementationRow = ({ implementation, counts, index }) => {
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
          {/* {implementation.get("version", "")} */}
        </small>
        <button
          className="btn border-0"
          data-bs-toggle="modal"
          data-bs-target={`#implementation-${index}-runtime-info`}
        >
          <img src={infoCircle} />
        </button>
      </td>

      <td className="text-center">
      {/*counts.errored_cases*/}
      </td>

      <td className="text-center">
      {/* counts.skipped_tests */}
      </td>
      <td className="text-center details-required">
        {/* {counts.failed_tests + counts.errored_tests} */}
        <div className="hover-details text-center">
          <p>
            <b>failed</b>:
            {/* {counts.failed_tests} */}
          </p>
          <p>
            <b>errored</b>: 
            {/* {counts.errored_tests} */}
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
