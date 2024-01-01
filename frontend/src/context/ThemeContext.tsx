import { ReactNode, createContext, useState, useEffect } from "react";

export const ThemeContext = createContext("light");

type ThemeContextProviderProps = {
  children: ReactNode;
};

const ThemeContextProvider = ({ children }: ThemeContextProviderProps) => {
  const [isDarkMode, setDarkMode] = useState(
    window.matchMedia("(prefers-color-scheme: dark)").matches,
  );

  useEffect(() => {
    document
      .querySelector("html")!
      .setAttribute("data-bs-theme", isDarkMode ? "dark" : "light");
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    setDarkMode((isDarkMode) => !isDarkMode);
  };

  const value = { isDarkMode, toggleDarkMode };
  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
};

export default ThemeContextProvider;
