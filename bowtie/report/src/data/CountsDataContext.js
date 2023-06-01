import { createContext, useState } from "react";

export const CountsDataContext = createContext();

export const CountsDataProvider = ({ children }) => {
  const [totalErroredCases, setTotalErroredCases] = useState(0);
  const [totalFailedTests, setTotalFailedTests] = useState(0);
  const [totalErroredTests, setTotalErroredTests] = useState(0);
  const [totalSkippedTests, setTotalSkippedTests] = useState(0);

  const updateTotalErroredCases = (value) => {
    setTotalErroredCases((prevTotal) => prevTotal + value);
  };

  const updateTotalFailedTests = (value) => {
    setTotalFailedTests((prevTotal) => prevTotal + value);
  };

  const updateTotalErroredTests = (value) => {
    setTotalErroredTests((prevTotal) => prevTotal + value);
  };

  const updateTotalSkippedTests = (value) => {
    setTotalSkippedTests((prevTotal) => prevTotal + value);
  };

  const contextValue = {
    totalErroredCases,
    totalFailedTests,
    totalErroredTests,
    totalSkippedTests,
    updateTotalErroredCases,
    updateTotalFailedTests,
    updateTotalErroredTests,
    updateTotalSkippedTests,
  };

  return (
    <CountsDataContext.Provider value={contextValue}>
      {children}
    </CountsDataContext.Provider>
  );
};
