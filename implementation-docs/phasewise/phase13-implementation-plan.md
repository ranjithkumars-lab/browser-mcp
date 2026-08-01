# Phase 13 Implementation Plan — Automation Control Center (Enterprise UI Architecture)

This document outlines the technical implementation plan for **Phase 13: Automation Control Center** of the Enterprise Browser MCP Platform. 
In accordance with our **Vibe Coding Rules**, no code will be written until this implementation plan is approved.

---

## 1. Executive Summary & Design Principles

The Automation Control Center is implemented as a **production-grade React + TypeScript application** following enterprise frontend engineering standards. The frontend is fully responsive, accessibility-compliant, mobile-first, strongly typed, and consumes the Browser Platform exclusively through the REST API and Browser Events Engine. Server state, UI state, and real-time event synchronization remain strictly separated.

> *"Phase 13 bridges the REST API and EventBus, providing visual operational control over the Worker System and Browser Core without duplicating business logic. It establishes a robust TypeScript-first frontend architecture mirroring the backend's enterprise quality."*

### Technology Stack
- **Framework:** React 19 + Vite
- **Language:** TypeScript
- **Styling:** Vanilla CSS Design System (CSS Variables, no framework)
- **Routing:** React Router
- **Server State:** React Query
- **Realtime:** WebSocketProvider
- **Testing:** Vitest + React Testing Library
- **API:** OpenAPI Generated Types

---

## 2. Directory & Component Layout

### Backend Additions (`src/browser_mcp/api/`)
The backend exposes `UiManager`, `FastAPIWebSocketProvider`, and `gateways/` (dashboard, workers, plugins) exactly as defined in previous revisions, maintaining the strict boundary:
`Browser Core -> BrowserEventManager -> ApiEngine -> Dashboard Gateway -> WebSocket Adapter -> React UI`.

### Frontend Application (`ui/`)
```text
ui/
├── index.html
├── package.json
├── tsconfig.json             # TypeScript configuration
├── vite.config.ts            
├── src/
│   ├── main.tsx              # React Entry point
│   ├── index.css             # Vanilla CSS Design System variables
│   ├── App.tsx               # Layout Shell
│   ├── assets/               # Icons and static images
│   ├── components/           # Reusable UI elements (Cards, Tables, Badges)
│   ├── layouts/              # Sidebar, Header, Dashboard shell
│   ├── providers/            # Theme, Api, Query, WebSocket, ErrorBoundary
│   ├── hooks/                # Custom React hooks wrapping queries/mutations
│   ├── services/             # API client modules (dashboard.ts, jobs.ts, etc.)
│   ├── types/                
│   │   └── api/              # OpenAPI generated types (BrowserEvent, Job, Worker)
│   ├── utils/                # Formatting and helpers
│   ├── errors/               # UiError -> ApiConnectionError -> WebSocketDisconnectedError
│   │
│   └── pages/                # The Operational Pages
│       ├── Dashboard.tsx     # High-level metrics via /api/v1/dashboard
│       ├── Jobs.tsx          # Live Job queue table
│       ├── Plugins.tsx       # Plugin catalog
│       ├── Workers.tsx       # Worker fleet status
│       ├── Logs.tsx          # Live scrolling event log via WS
│       ├── Artifacts.tsx     # File management
│       ├── Sessions.tsx      # Active browser session inspection
│       ├── Downloads.tsx     # Transfer Engine visibility
│       ├── Access.tsx        # API Key entry (Users/RBAC reserved)
│       └── Settings.tsx      # Read-only configuration viewer (Editing reserved)
```

*(Note: Live "Browser Preview -> Screenshot Stream" is architecturally reserved for a future phase.)*

---

## 3. Frontend Architecture Standards

### 3.1. Provider & State Architecture
State is strictly segregated:
1. **Server State**: Managed via `QueryProvider` (React Query). Caches API responses.
2. **UI State**: Managed via React Contexts (`ThemeProvider`, `SidebarProvider`).
3. **Real-time State**: Managed via `WebSocketProvider`. 
   *Flow:* `BrowserEvent -> WebSocketProvider -> Server State Cache -> React Components`.

### 3.2. API Services & Types
Pages never call `fetch()` directly.
- **Data Flow**: `Page.tsx` -> `useJobs()` hook -> `services/jobs.ts` -> API.
- **Types**: Interfaces like `BrowserEvent.ts`, `Job.ts`, `Worker.ts` are generated from OpenAPI schemas to ensure end-to-end type safety.

### 3.3. Responsive Architecture
Mobile-first CSS variables mapping breakpoints:
- `320+`, `640+`, `768+`, `1024+`, `1280+`, `1536+`.
Includes: mobile navigation drawer, collapsing sidebar, responsive cards, max-width constraints, and overflow-x-auto tables.

### 3.4. State Handlers (Loading / Error / Empty)
Every route and widget explicitly implements:
- **Loading**: Skeletons (e.g., metric skeletons on Dashboard).
- **Error**: Retry prompts wrapped in an `ErrorBoundaryProvider` (at Page and Widget levels).
- **Empty**: Informative Empty States with Call-to-Actions (e.g., "No active workers").
- **Success**: The core component render.

### 3.5. Accessibility (a11y)
Strict compliance: Semantic HTML, keyboard navigation, focus trapping, visible focus rings, `aria-label`, `aria-live`, `role="alert"`, and minimum 44x44 touch targets.

### 3.6. Design System & Performance
- **Styling**: Theme Tokens (Spacing scale, Light/Dark mode). **No hard-coded colors or spacing**. Glassmorphism overlays.
- **Performance**: Memoized components, lazy loading routes, code splitting, WebSocket frame batching, virtualized log viewers, responsive image loading.

### 3.7. Frontend Security
- API Keys are stored securely and never logged unencrypted.
- User content is strictly sanitized.
- CSP compatibility ensured.
- Secure WebSocket endpoints (`wss://`).

---

## 4. Documentation Strategy (`docs/ui/`)

Complete documentation suite under `docs/ui/`:
- `docs/ui/overview.md`
- `docs/ui/architecture.md` (Strict data flow).
- `docs/ui/websocket.md` (Event translation).
- `docs/ui/pages.md` (Page to Backend mapping).
- `docs/ui/deployment.md` (Static serving and SPA fallback).
- `docs/ui/design-system.md` (Vanilla CSS modules, Accessibility).

---

## 5. Verification Plan

1. **Frontend Testing Suite (`Vitest + RTL`)**:
   - Component, Responsive, Accessibility (a11y), and Dark Mode tests.
   - Explicit tests for Loading, Error, and Empty states.
   - API Mock tests and WebSocket synchronization tests.
   - `npm run lint` and `npm run typecheck` passing.
2. **Backend & Protocol Tests**:
   - `UiManager` instantiates `FastAPIWebSocketProvider`.
   - Dashboard gateway aggregates system statistics.

### 5.1. Definition of Done (Production Checklist)
- `[ ]` Responsive (Mobile First, Tablet, Desktop)
- `[ ]` Dark Mode & Light Mode
- `[ ]` Skeletons, Error States, Empty States
- `[ ]` Accessibility & Keyboard Navigation
- `[ ]` Theme Tokens (No Hardcoded Colors)
- `[ ]` No Console Errors
- `[ ]` API Types Generated
- `[ ]` WebSocket Tested
- `[ ]` Lint & Type Check Passing
- `[ ]` Production Build Passing
- `[ ]` Component Tests Passing
