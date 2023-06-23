import { createContext, useState, useEffect } from "react";

export const ThemeContext = createContext();

const ThemeContextProvider = ({ children }) => {
  const [isDarkMode, setDarkMode] = useState(
    window.matchMedia("(prefers-color-scheme: dark)").matches,
  );

  useEffect(() => {
    document
      .querySelector("body")
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
