import { ReactNode, createContext, useState, useEffect } from "react";

interface ThemeContextProviderProps {
  isDarkMode?: boolean;
  children?: ReactNode;
  toggleDarkMode?: () => void;
}

export const ThemeContext = createContext<ThemeContextProviderProps>({});

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
