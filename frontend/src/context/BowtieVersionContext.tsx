import {
  Dispatch,
  ReactNode,
  SetStateAction,
  createContext,
  useMemo,
  useState,
} from "react";

interface BowtieVersionProviderProps {
  children?: ReactNode;
  version?: string;
  setVersion?: Dispatch<SetStateAction<string>>;
}

export const BowtieVersionContext = createContext<BowtieVersionProviderProps>(
  {},
);

export const BowtieVersionContextProvider = ({
  children,
}: BowtieVersionProviderProps) => {
  const [version, setVersion] = useState("");

  const value = useMemo(() => ({ version, setVersion }), [version, setVersion]);
  return (
    <BowtieVersionContext.Provider value={value}>
      {children}
    </BowtieVersionContext.Provider>
  );
};
