import js from "@eslint/js";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import tsdoc from "eslint-plugin-tsdoc";
import tseslint from "typescript-eslint";

export default tseslint.config(
  js.configs.recommended,
  react.configs.flat.recommended,
  react.configs.flat["jsx-runtime"],
  ...tseslint.configs.recommendedTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  {
    plugins: {
      react,
      tsdoc,
      "react-hooks": reactHooks,
    },
    rules: {
      "react/prop-types": 0,
      "no-restricted-imports": [
        "error",
        {
          name: "react-bootstrap",
          message:
            "Import react-bootstrap/<your-component> instead. See https://react-bootstrap.netlify.app/docs/getting-started/introduction/#importing-components.",
        },
      ],
      "tsdoc/syntax": "warn",
      ...reactHooks.configs.recommended.rules,
    },
    settings: {
      react: { version: "detect" },
    },
  },
);
