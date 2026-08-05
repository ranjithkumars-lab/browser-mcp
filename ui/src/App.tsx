import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider, useTheme } from "./providers/ThemeProvider";
import { ApiProvider } from "./providers/ApiProvider";
import { ErrorBoundaryProvider } from "./providers/ErrorBoundaryProvider";
import { WebSocketProvider } from "./providers/WebSocketProvider";
import { Icon, type IconName } from "./components/Icon";
import { Dashboard } from "./pages/Dashboard";
import { Jobs } from "./pages/Jobs";
import { Workers } from "./pages/Workers";
import { Logs } from "./pages/Logs";
import { Plugins } from "./pages/Plugins";
import { Artifacts } from "./pages/Artifacts";
import { Sessions } from "./pages/Sessions";
import { Downloads } from "./pages/Downloads";
import { Access } from "./pages/Access";
import { Settings } from "./pages/Settings";
import { Chat } from "./pages/Chat";

const queryClient = new QueryClient();

const NAV_GROUPS = [
  {
    title: "Main",
    items: [
      { name: "Dashboard", icon: "dashboard" as IconName },
      { name: "Chat", icon: "chat" as IconName },
    ],
  },
  {
    title: "System",
    items: [
      { name: "Jobs", icon: "jobs" as IconName },
      { name: "Workers", icon: "workers" as IconName },
      { name: "Logs", icon: "logs" as IconName },
      { name: "Plugins", icon: "plugins" as IconName },
    ],
  },
  {
    title: "Content",
    items: [
      { name: "Artifacts", icon: "artifacts" as IconName },
      { name: "Sessions", icon: "sessions" as IconName },
      { name: "Downloads", icon: "downloads" as IconName },
    ],
  },
  {
    title: "Admin",
    items: [
      { name: "Access", icon: "access" as IconName },
      { name: "Settings", icon: "settings" as IconName },
    ],
  },
] as const;

const ALL_PAGES = [
  { name: "Dashboard", component: Dashboard },
  { name: "Chat", component: Chat },
  { name: "Jobs", component: Jobs },
  { name: "Workers", component: Workers },
  { name: "Logs", component: Logs },
  { name: "Plugins", component: Plugins },
  { name: "Artifacts", component: Artifacts },
  { name: "Sessions", component: Sessions },
  { name: "Downloads", component: Downloads },
  { name: "Access", component: Access },
  { name: "Settings", component: Settings },
] as const;

function Shell() {
  const { dark, toggle } = useTheme();
  const [page, setPage] = useState<string>("Dashboard");
  const [open, setOpen] = useState(false);
  const PageComponent = ALL_PAGES.find((p) => p.name === page)?.component ?? Dashboard;

  const navigate = (name: string) => {
    setPage(name);
    setOpen(false);
  };

  return (
    <div className="app">
      <div className={`sidebar${open ? " open" : ""}`}>
        <div className="brand">
          <div className="brand-logo">B</div>
          <div>
            <div className="brand-name">Browser MCP</div>
            <div className="brand-sub">Control Center</div>
          </div>
        </div>
        <nav aria-label="Control center navigation">
          {NAV_GROUPS.map((group) => (
            <div className="nav-group" key={group.title}>
              <div className="nav-group-title">{group.title}</div>
              {group.items.map((item) => (
                <button
                  key={item.name}
                  className="nav-item"
                  aria-current={page === item.name ? "page" : undefined}
                  onClick={() => navigate(item.name)}
                >
                  <Icon name={item.icon} />
                  {item.name}
                </button>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">v1.0 &middot; 54 tools</div>
      </div>

      {open && <div className="sidebar-backdrop" onClick={() => setOpen(false)} />}

      <div className="main">
        <header className="topbar">
          <button
            type="button"
            className="icon-btn menu-toggle"
            aria-label="Toggle navigation"
            onClick={() => setOpen((v) => !v)}
          >
            <Icon name="menu" />
          </button>
          <div className="topbar-title">{page}</div>
          <div className="topbar-spacer" />
          <button
            type="button"
            className="icon-btn"
            aria-label="Toggle theme"
            onClick={toggle}
          >
            <Icon name={dark ? "sun" : "moon"} />
          </button>
        </header>
        <main className={`content ${page === "Chat" ? "content-chat" : ""}`}>
          <PageComponent />
        </main>
      </div>
    </div>
  );
}

export function App() {
  return (
    <ErrorBoundaryProvider>
      <QueryClientProvider client={queryClient}>
        <ApiProvider>
          <ThemeProvider>
            <WebSocketProvider>
              <Shell />
            </WebSocketProvider>
          </ThemeProvider>
        </ApiProvider>
      </QueryClientProvider>
    </ErrorBoundaryProvider>
  );
}
