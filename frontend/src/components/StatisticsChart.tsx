import { quantileSeq, median, mean } from "mathjs";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { ReportData } from "../data/parseReportData";

export const StatisticsChart = ({ reportData }: { reportData: ReportData }) => {
  const totalTests = Array.from(reportData.cases.values())
    .reduce((total, testCase) => total + testCase.tests.length, 0);

  const implementationEntries = Array.from(reportData.implementationsResults.entries());

  const chartData = implementationEntries.map(([id, results], index) => {
    const totals = results.totals;
    const failed = totals.failedTests ?? 0;
    const errored = totals.erroredTests ?? 0;
    const skipped = totals.skippedTests ?? 0;
    
    const successCount = totalTests - (failed + errored + skipped);
    const score = (successCount / totalTests) * 100;

    return {
      x: index,
      y: Math.round(score * 100) / 100,
      name: id.split(":").pop(),
    };
  });

  const scores = chartData.map(d => d.y).sort((a, b) => a - b);
  const q25 = quantileSeq(scores, 0.25);
  const medianScore = median(scores);
  const q75 = quantileSeq(scores, 0.75);
  const meanScore = mean(scores);

  return (
    <div className="mt-4 mb-5 p-3 border">
      <h4 className="text-center mb-4" >
        Compliance Chart
      </h4>
      
      <div style={{ width: "100%", height: 450 }}>
        <ResponsiveContainer>
          <ScatterChart margin={{ top: 10, right: 30, bottom: 0, left: 0 }}>
            <XAxis type="number" dataKey="x" hide/> 
            <YAxis 
              type="number" 
              dataKey="y" 
              domain={['auto', 'auto']}
              tick={{ fill: "currentColor", fontSize: 15 }} 
            />
            
            <Tooltip 
              content={({ active, payload }) => {
                if (active && payload?.length) {
                  const item = payload[0] as { payload: { name: string; y: number } };
                  const data = item.payload;
                  return (
                    <div style={{ border: 'solid', padding: '8px'}}>
                      <p style={{ margin: 0 }}><b>{data.name}</b></p>
                      <p style={{ margin: 0 }}>Compliance: {data.y}%</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            
            <ReferenceLine y={q25} stroke="#096dd9" strokeDasharray="3 3"/>
            <ReferenceLine y={medianScore} stroke="#389e0d" />
            <ReferenceLine y={q75} stroke="#cf1322" strokeDasharray="3 3"/>
            <ReferenceLine y={meanScore} stroke="#8c8c8c" strokeDasharray="2 2" />
            
            <Scatter data={chartData}>
              {chartData.map((_, index) => (
                <Cell key={index} fill="grey" />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <div className="d-flex justify-content-center mt-3 p-2 border mx-auto" 
           style={{ maxWidth: "550px" }}>
        <div className="mx-3 d-flex align-items-center">
          <div style={{ width: 12, height: 2, borderTop: "2px dashed #cf1322", marginRight: 5 }}></div>
          <span className="small">Q75: {q75.toFixed(1)}%</span>
        </div>
        <div className="mx-3 d-flex align-items-center">
          <div style={{ width: 12, height: 2, backgroundColor: "#389e0d", marginRight: 5 }}></div>
          <span className="small">Median: {medianScore.toFixed(1)}%</span>
        </div>
        <div className="mx-3 d-flex align-items-center">
          <div style={{ width: 12, height: 0, borderTop: "2px dashed #096dd9", marginRight: 5 }}></div>
          <span className="small">Q25: {q25.toFixed(1)}%</span>
        </div>
        <div className="mx-3 d-flex align-items-center">
          <div style={{ width: 12, height: 0, borderTop: "2px dashed #8c8c8c", marginRight: 5 }}></div>
          <span className="small">Mean: {meanScore.toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
};