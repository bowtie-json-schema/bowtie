import { describe, expect, test } from "@jest/globals";
import { create } from "react-test-renderer";
import CaseResultSvg from "../CaseResultSvg";
import { CaseResult } from "../../../data/parseReportData";
import {
  CheckCircleFill,
  XCircleFill,
  ExclamationOctagon,
  Icon,
} from "react-bootstrap-icons";

interface CaseResultIconTestParams {
  state: CaseResult["state"];
  valid?: boolean;
  icon: Icon;
}

const testCases: CaseResultIconTestParams[] = [
  {
    state: "successful",
    valid: true,
    icon: CheckCircleFill,
  },
  {
    state: "successful",
    valid: false,
    icon: XCircleFill,
  },
  {
    state: "skipped",
    icon: ExclamationOctagon,
  },
  {
    state: "errored",
    icon: ExclamationOctagon,
  },
];

describe.each(testCases)("Case Result Icons", ({ state, valid, icon }) => {
  const testCaseData = {
    state,
    valid,
  } as CaseResult;

  const testName = valid == undefined ? state : `${state} expected ${valid}`;
  test(testName, () => {
    const testRenderer = create(<CaseResultSvg result={testCaseData} />);
    const testInstance = testRenderer.root;
    expect(testInstance.findByType(icon));
  });
});
