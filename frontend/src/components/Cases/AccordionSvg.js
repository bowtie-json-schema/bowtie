import Svg from "../../assets/svg/Svg";

const AccordionSvg = ({ testResult }) => {
  if (testResult === "skipped") {
    return (
      <td className="text-center text-bg-warning">
        <Svg icon="exclamation" />
      </td>
    );
  } else if (testResult === "errored") {
    return (
      <td className="text-center text-bg-danger">
        <Svg icon="exclamation" />
      </td>
    );
  } else if (testResult === "passed") {
    return (
      <td className="text-center">
        <Svg icon="check" />
      </td>
    );
  } else if (testResult === "failed") {
    return (
      <td className="text-center">
        <Svg icon="cross" />
      </td>
    );
  } else if (testResult === "unexpectedlyValid") {
    return (
      <td className="text-center text-bg-danger">
        <Svg icon="check" />
      </td>
    );
  } else if (testResult === "unexpectedlyInvalid") {
    return (
      <td className="text-center text-bg-danger">
        <Svg icon="cross" />
      </td>
    );
  }
  return null;
};

export default AccordionSvg;
