import { createContext, useMemo, useState } from "react";

export const BowtieVersionContext = createContext();

export const BowtieVersionContextProvider = ({ children }) => {
  const [version, setVersion] = useState();

  const value = useMemo(() => ({ version, setVersion }), [version, setVersion]);
  return (
    <BowtieVersionContext.Provider value={value}>
      {children}
    </BowtieVersionContext.Provider>
  );
};
