import { CheckCircleFill, ExclamationOctagon, XCircleFill } from 'react-bootstrap-icons';

const AccordionSvg = ({ testResult }) => {
  if (testResult === "skipped") {
    return (
      <td className="text-center text-bg-warning">
        <ExclamationOctagon />
      </td>
    );
  } else if (testResult === "errored") {
    return (
      <td className="text-center text-bg-danger">
        <ExclamationOctagon />
      </td>
    );
  } else if (testResult === "passed") {
    return (
      <td className="text-center">
        <CheckCircleFill />
      </td>
    );
  } else if (testResult === "failed") {
    return (
      <td className="text-center">
        <XCircleFill />
      </td>
    );
  } else if (testResult === "unexpectedlyValid") {
    return (
      <td className="text-center text-bg-danger">
        <CheckCircleFill />
      </td>
    );
  } else if (testResult === "unexpectedlyInvalid") {
    return (
      <td className="text-center text-bg-danger">
        <XCircleFill />
      </td>
    );
  }
  return null;
};

export default AccordionSvg;
