# ReceptivIQ Web

React + Vite + TypeScript frontend for the ReceptivIQ Platform.

## Development

```bash
npm install
npm run dev
```

Vite dev server runs on `http://localhost:5173` and proxies `/api` to the FastAPI backend on `http://localhost:8000`.

## Production build

```bash
npm run build
npm run preview
```

## Docker

```bash
docker build -t receptiviq-web .
docker run -p 8080:80 receptiviq-web
```

## Stack

- Vite 5 + React 18 + TypeScript 5
- Tailwind CSS 3 with `class`-strategy dark mode
- React Router 6, Zustand, TanStack Query 5
- Axios with auth + refresh-token interceptor
- React Hook Form + Zod
- Sonner toasts, Lucide icons, Inter font
