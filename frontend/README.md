# AlphaMesh Frontend

当前前端是一个 Vite + React 的 MVP dashboard，用于验证 AlphaMesh 后端 API、LLM Agent 状态、研究报告、Automation Flow 和 Agent Run 日志。

## 本地启动

```bash
npm install
npm run dev
```

访问:

```text
http://localhost:5173
```

默认会通过 `VITE_API_BASE_URL` 访问后端 API。开发环境可复制 `.env.example` 为 `.env` 后调整:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 构建

```bash
npm run build
```
