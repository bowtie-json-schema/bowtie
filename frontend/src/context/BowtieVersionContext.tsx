import { ReactNode, createContext, useMemo, useState } from "react";

type BowtieVersionProviderProps = {
  children?: ReactNode;
  version?: string;
};

export const BowtieVersionContext = createContext<BowtieVersionProviderProps>(
  {},
);

export const BowtieVersionContextProvider = ({
  children,
}: BowtieVersionProviderProps) => {
  const [version, setVersion] = useState();

  const value = useMemo(() => ({ version, setVersion }), [version, setVersion]);
  return (
    <BowtieVersionContext.Provider value={value}>
      {children}
    </BowtieVersionContext.Provider>
  );
};
