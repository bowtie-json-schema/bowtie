import { describe, expect, test } from "vitest";
import { render } from "@testing-library/react";
import {
  CheckCircleFill,
  XCircleFill,
  ExclamationOctagon,
  Icon,
} from "react-bootstrap-icons";

import CaseResultSvg from "./CaseResultSvg";
import { CaseResult } from "../../data/parseReportData";

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

describe.each(testCases)(
  "Case Result Icons",
  ({ state, valid, icon: IconComponent }) => {
    const testCaseData = {
      state,
      valid,
    } as CaseResult;

    const testName = valid == undefined ? state : `${state} expected ${valid}`;
    test(testName, () => {
      const { container } = render(
        <table>
          <tbody>
            <tr>
              <CaseResultSvg result={testCaseData} />
            </tr>
          </tbody>
        </table>,
      );
      const renderedSvg = container.querySelector("svg");

      expect(renderedSvg).not.toBeNull();

      const { container: iconContainer } = render(<IconComponent />);
      const expectedSvg = iconContainer.querySelector("svg");

      expect(renderedSvg?.innerHTML).toBe(expectedSvg?.innerHTML);
    });
  },
);
