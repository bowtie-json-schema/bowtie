import {
  Dispatch,
  ReactNode,
  SetStateAction,
  createContext,
  useMemo,
  useState,
} from "react";

type BowtieVersionProviderProps = {
  children?: ReactNode;
  version?: string;
  setVersion: Dispatch<SetStateAction<any>>;
};

export const BowtieVersionContext = createContext<BowtieVersionProviderProps>({
  setVersion: () => null,
});

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
