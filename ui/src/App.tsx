import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "./providers/ThemeProvider";
import { ApiProvider } from "./providers/ApiProvider";
import { ErrorBoundaryProvider } from "./providers/ErrorBoundaryProvider";
import { WebSocketProvider } from "./providers/WebSocketProvider";
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

const pages = [
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

export function App() {
  const [page, setPage] = useState<string>("Dashboard");
  const PageComponent = pages.find((p) => p.name === page)?.component ?? Dashboard;

  return (
    <ErrorBoundaryProvider>
      <QueryClientProvider client={queryClient}>
        <ApiProvider>
          <ThemeProvider>
            <WebSocketProvider>
              <main>
                <aside>
                  <h1>Browser MCP</h1>
                  <nav aria-label="Control center navigation">
                    {pages.map((item) => (
                      <button
                        key={item.name}
                        aria-current={page === item.name ? "page" : undefined}
                        onClick={() => setPage(item.name)}
                      >
                        {item.name}
                      </button>
                    ))}
                  </nav>
                </aside>
                <section>
                  <header>
                    <h2>{page}</h2>
                    <button onClick={() => document.documentElement.classList.toggle("dark")}>
                      Theme
                    </button>
                  </header>
                  <PageComponent />
                </section>
              </main>
            </WebSocketProvider>
          </ThemeProvider>
        </ApiProvider>
      </QueryClientProvider>
    </ErrorBoundaryProvider>
  );
}