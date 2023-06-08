import Svg from "../../assets/svg/Svg";
import { copyToClipboard } from "../../utilities/utilFunctions";

const SchemaDisplay = ({ schema }) => {
  return (
    <div className="card mb-3 mw-100">
      <div className="row">
        <div className="col-8 pe-0">
          <div className="d-flex align-items-center highlight-toolbar ps-3 pe-2 py-1 border-0 border-top border-bottom">
            <small className="font-monospace text-body-secondary text-uppercase">
              Schema
            </small>
            <div className="d-flex ms-auto">
              <button
                type="button"
                id="copy-button-schema"
                className="btn mt-0 me-0"
                onClick={() =>
                  copyToClipboard("schema-code", "copy-button-schema")
                }
                aria-label="Copy to clipboard"
                data-bs-toggle="tooltip"
                data-bs-placement="top"
                data-bs-custom-class="custom-tooltip"
                data-bs-title="Copy to clipboard"
              >
                <Svg icon="copyIcon" />
              </button>
            </div>
          </div>
          <div className="card-body">
            <pre>{JSON.stringify(schema, null, 2)}</pre>
          </div>
        </div>
        <div className="col-4 border-start ps-0">
          <div className="d-flex align-items-center highlight-toolbar ps-3 pe-2 py-1 border-0 border-top border-bottom">
            <small className="font-monospace text-body-secondary text-uppercase">
              Instance
            </small>
            <div className="d-flex ms-auto">
              <button
                type="button"
                id="copy-button-instance"
                onClick={() =>
                  copyToClipboard("instance-info", "copy-button-instance")
                }
                className="btn mt-0 me-0"
                aria-label="Copy to clipboard"
                data-bs-toggle="tooltip"
                data-bs-placement="top"
                data-bs-custom-class="custom-tooltip"
                data-bs-title="Copy to clipboard"
              >
                <Svg icon="copyIcon" />
              </button>
            </div>
          </div>
          <div id="instance-info" className="card-body"></div>
        </div>
      </div>
    </div>
  );
};

export default SchemaDisplay;
