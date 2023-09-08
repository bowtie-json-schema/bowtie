module.exports = {
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  extends: [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:react/jsx-runtime",
    "plugin:react-hooks/recommended",
    "plugin:@typescript-eslint/eslint-recommended",
    "plugin:@typescript-eslint/recommended",
  ],
  parser: "@typescript-eslint/parser",
  plugins: ["@typescript-eslint"],
  settings: {
    react: {
      version: "18.2",
    },
  },
  rules: {
    "react/prop-types": 0,
    "react/no-unescaped-entities": 0,
    "@typescript-eslint/ban-ts-comment": 0, // REMOVEME: When we are typed
    "@typescript-eslint/no-explicit-any": 0, // REMOVEME: When we are typed
  },
};
