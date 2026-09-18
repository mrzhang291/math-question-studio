// 文件说明：只构建教师工作台壳层；业务数据和操作仍由 Python 工作台服务提供。
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  build: {
    outDir: "../assets/react-shell",
    emptyOutDir: true,
    lib: {
      entry: "src/main.tsx",
      name: "TeacherWorkbenchShell",
      formats: ["iife"],
      fileName: () => "workbench-shell.js",
    },
    rollupOptions: {
      output: { assetFileNames: "workbench-shell.[ext]" },
    },
  },
});
