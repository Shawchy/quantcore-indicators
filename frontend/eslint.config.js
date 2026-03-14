import globals from 'globals'
import js from '@eslint/js'
import tseslint from 'typescript-eslint'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'

export default tseslint.config(
  // 忽略文件
  {
    ignores: ['node_modules/', 'dist/', 'build/', '**/*.d.ts'],
  },

  // 基础配置
  js.configs.recommended,
  ...tseslint.configs.recommended,

  // TypeScript 文件配置
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: {
        ...globals.browser,
        ...globals.es2020,
      },
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      // TypeScript 规则
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],

      // React Hooks 规则
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',

      // React Refresh 规则
      'react-refresh/only-export-components': 'warn',

      // 通用规则
      'no-console': 'warn',
      'no-debugger': 'warn',
    },
  },

  // React 组件文件特殊配置
  {
    files: ['**/*.tsx'],
    rules: {
      // 允许 React 组件使用 JSX 语法而不需要显式导入 React
      '@typescript-eslint/no-require-imports': 'off',
    },
  },
)
