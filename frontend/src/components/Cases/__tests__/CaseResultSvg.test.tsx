import { expect, test } from "@jest/globals";
import { create } from "react-test-renderer";
import CaseResultSvg from "../CaseResultSvg";
import { CaseResult } from "../../../data/parseReportData";
import {
  CheckCircleFill,
  XCircleFill,
  ExclamationOctagon,
} from "react-bootstrap-icons";

test("Case Result Icon Successful Expected True", () => {
  const testCaseData = {
    state: "successful",
    valid: true,
  } as CaseResult;

  const testRenderer = create(<CaseResultSvg result={testCaseData} />);
  const testInstance = testRenderer.root;
  expect(testInstance.findByType(CheckCircleFill));
});

test("Case Result Icon Successful Expected False", () => {
  const testCaseData = {
    state: "successful",
    valid: false,
  } as CaseResult;

  const testRenderer = create(<CaseResultSvg result={testCaseData} />);
  const testInstance = testRenderer.root;
  expect(testInstance.findByType(XCircleFill));
});

test("Case Result Icon Skipped", () => {
  const testCaseData = {
    state: "skipped",
  } as CaseResult;

  const testRenderer = create(<CaseResultSvg result={testCaseData} />);
  const testInstance = testRenderer.root;
  expect(testInstance.findByType(ExclamationOctagon));
});

test("Case Result Icon Errored", () => {
  const testCaseData = {
    state: "errored",
  } as CaseResult;

  const testRenderer = create(<CaseResultSvg result={testCaseData} />);
  const testInstance = testRenderer.root;
  expect(testInstance.findByType(ExclamationOctagon));
});
