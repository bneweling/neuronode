import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    plugins: {
      import: (await import("eslint-plugin-import")).default,
    },
    rules: {
      // K3.1.3 Import Consistency Rules - Allow @/* paths, forbid only ../ patterns
      "import/no-useless-path-segments": "error", // Remove unnecessary path segments
      "no-restricted-imports": [
        "error",
        {
          "patterns": [
            {
              "group": ["../*", "../*/*", "../../*", "../../../*"],
              "message": "Relative imports from parent directories are not allowed. Use @/* absolute paths instead."
            }
          ]
        }
      ],
      "import/order": [
        "error",
        {
          groups: [
            "builtin",   // Node.js built-in modules
            "external",  // NPM packages
            "internal",  // Internal modules (with @/ prefix)
            "parent",    // Parent directory imports
            "sibling",   // Same directory imports
            "index"      // Index file imports
          ],
          pathGroups: [
            {
              pattern: "@/**",
              group: "internal",
              position: "before"
            }
          ],
          pathGroupsExcludedImportTypes: ["builtin"],
          "newlines-between": "always",
          alphabetize: {
            order: "asc",
            caseInsensitive: true
          }
        }
      ],
    },
  },
];

export default eslintConfig;
