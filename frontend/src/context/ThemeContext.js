import { createContext, useState, useEffect } from "react";

export const ThemeContext = createContext();

const ThemeContextProvider = ({ children }) => {
  const [theme, setTheme] = useState(
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );

  useEffect(() => {
    document
      .querySelector("body")
      .setAttribute("data-bs-theme", theme ? "dark" : "light");
  }, [theme]);

  const handleTheme = () => {
    setTheme(!theme);
  };

  const value = { theme, handleTheme };
  return (
    <ThemeContext.Provider value={value}>
        { children }
    </ThemeContext.Provider>
  );
};

export default ThemeContextProvider;
