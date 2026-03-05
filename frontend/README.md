<div align="center">

# 🖥️ AI Camera Dashboard — Frontend

**Modern React dashboard for the AI Camera System**

[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=white)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=flat&logo=vite&logoColor=white)](https://vitejs.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3-06B6D4?style=flat&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)

</div>

---

## 📖 Overview

A real-time AI camera dashboard that:

- **Streams the live annotated camera feed** directly via MJPEG `<img>` — zero latency, browser-native
- **Receives detection results over WebSocket** (auto-reconnects on disconnect)
- **Displays YOLO detections** as cards with colour-coded confidence bars and bounding box coordinates
- **Shows Qwen3.5-0.8B VLM reasoning** updated every ~3 seconds
- **Monitors model health** (YOLO / Qwen / InsightFace load status + worker FPS)

---

## 🏗️ Architecture

```
Backend (FastAPI :8001)
    │
    ├── /api/stream  ─ MJPEG multipart   →  <img src> in CameraFeed
    ├── /api/ws      ─ WebSocket JSON    →  useDetectionWebSocket hook
    └── /api/detect/health ─ REST        →  useModelHealth hook (polls 5s)

Vite Dev Proxy (:5173) → Backend (:8001)
  All /api/* requests + WebSocket proxied — no CORS needed in dev
```

---

## 📁 Project Structure

```
frontend/
├── .env                             # Active environment variables
├── .env.example                     # Template — copy to .env
├── index.html                       # HTML entry (Inter + JetBrains Mono fonts)
├── vite.config.ts                   # Dev proxy → backend :8001 (HTTP + WS)
├── tailwind.config.js               # Custom ink palette, neon green, animations
├── postcss.config.js
├── tsconfig.json
└── src/
    ├── vite-env.d.ts                # VITE_ environment variable types
    ├── index.css                    # Global: dark theme, scrollbar, component utils
    ├── main.tsx                     # React DOM root
    ├── App.tsx                      # 3-column layout (sidebar | camera | reasoning)
    │
    ├── types/
    │   └── index.ts                 # TypeScript interfaces matching backend models
    │
    ├── hooks/
    │   ├── useDetectionWebSocket.ts # Auto-reconnecting WS with generation counter
    │   └── useModelHealth.ts        # Polls /api/detect/health every 5 s
    │
    └── components/
        ├── StatusBar.tsx            # Top bar: FPS, object/face count, connection badge
        ├── CameraFeed.tsx           # MJPEG stream + LIVE badge + error/retry state
        ├── DetectionList.tsx        # Scrollable detection cards + confidence bars
        ├── ReasoningPanel.tsx       # Qwen3.5 scene reasoning + timestamp
        └── ModelHealthPanel.tsx     # YOLO / Qwen / InsightFace status indicators
```

---

## 🖼️ UI Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  🎥 AI Camera System        FPS: 14.2  Objects: 3  Faces: 1  LIVE  │ ← StatusBar
├──────────────┬──────────────────────────────┬───────────────────────┤
│ Model Status │                              │  Qwen3.5 Reasoning    │
│  YOLO ●      │   Live annotated MJPEG feed  │                       │
│  Qwen3.5 ●   │   (bboxes + face landmarks)  │  "A person with       │
│  InsightFace●│                              │   glasses is seated…" │
│──────────────│                              │                       │
│ Detections   │──────────────────────────────│                       │
│              │  Objects: 3  Faces: 1  FPS   │  Updated every ~3s    │
│ [Person 89%] └──────────────────────────────┴───────────────────────┘
│ [Chair  67%]
│ [Face   76%]
└──────────────┘
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| [React 18](https://react.dev) | UI framework with concurrent features |
| [TypeScript 5](https://www.typescriptlang.org) | Type safety end-to-end |
| [Vite 5](https://vitejs.dev) | Lightning-fast dev server + HMR, production bundler |
| [Tailwind CSS 3](https://tailwindcss.com) | Utility-first styling with custom dark theme |
| [Lucide React](https://lucide.dev) | Crisp SVG icons |
| [Native WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket) | Real-time detection stream with auto-reconnect |

---

## 🚀 Getting Started

### Prerequisites

- Node.js **18+**
- The [AI Camera System backend](../README.md) running on port **8001**

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env if your backend runs on a different host/port
```

### 3. Start the dev server

```bash
npm run dev
```

Open **http://localhost:5173** in your browser.

> The Vite dev server automatically proxies `/api/*` requests to `http://localhost:8001`, so CORS is not an issue in development.

### 4. Production build

```bash
npm run build       # outputs to frontend/dist/
npm run preview     # preview the production build locally
```

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8001` | Backend HTTP base URL (used for REST calls) |
| `VITE_WS_URL` | *(auto-derived)* | WebSocket URL. Leave blank in dev (proxy used). Set for production VPS. |
| `VITE_STREAM_URL` | `http://localhost:8001/api/stream` | MJPEG stream URL |
| `VITE_WS_RECONNECT_DELAY` | `3000` | Milliseconds before WebSocket reconnect attempt |

> **Dev mode:** `VITE_WS_URL` should be left blank. The hook auto-derives `ws://localhost:5173/api/ws` which is proxied through Vite to the backend.
>
> **VPS / Production:** Set `VITE_WS_URL=ws://your-domain.com/api/ws` and `VITE_STREAM_URL=http://your-domain.com/api/stream`.

---

## 🔌 WebSocket Hook

```typescript
// useDetectionWebSocket — generation-counter pattern
// Handles React StrictMode double-mount, auto-reconnects on drop
const { data, status } = useDetectionWebSocket()

// data:   { detections, faces, reasoning, fps, frame_timestamp }
// status: 'connecting' | 'connected' | 'disconnected' | 'error'
```

The hook uses a **generation counter** to discard stale WebSocket callbacks on unmount/remount (important for React 18 StrictMode which double-mounts effects in development).

---

## 📄 License

MIT © 2026
