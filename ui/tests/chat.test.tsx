import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { Chat } from "../src/pages/Chat";
import * as chatService from "../src/services/chat";

vi.mock("../src/services/chat", () => ({
  getChatConfig: vi.fn(),
  chatStream: vi.fn(),
}));

function renderChat() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <Chat />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.mocked(chatService.getChatConfig).mockResolvedValue({
    host: "http://ollama:11444",
    model: "gpt-oss:20b",
    tools: 54,
    tool_names: ["browser.goto", "browser.snapshot", "browser.search"],
  });
});

describe("Chat", () => {
  it("renders the config summary once loaded", async () => {
    renderChat();
    expect(await screen.findByText(/54 browser tools available/)).toBeTruthy();
  });

  it("sends a message and renders assistant text", async () => {
    async function* stream() {
      yield { type: "text", delta: "Hel" };
      yield { type: "text", delta: "lo" };
      yield { type: "done", content: "Hello", steps: 1 };
    }
    vi.mocked(chatService.chatStream).mockImplementation(async function* () {
      yield* stream();
    });

    renderChat();
    await screen.findByText(/54 browser tools available/);

    const textarea = screen.getByLabelText("Message");
    fireEvent.change(textarea, { target: { value: "hi" } });
    fireEvent.click(screen.getByText("Send"));

    expect(await screen.findByText("hi")).toBeTruthy();
    expect(await screen.findByText("Hello")).toBeTruthy();
  });

  it("renders tool call and result events", async () => {
    async function* stream() {
      yield { type: "tool_call", name: "browser.goto" };
      yield { type: "tool_result", name: "browser.goto", content: "loaded", error: false };
      yield { type: "done", content: "Done", steps: 2 };
    }
    vi.mocked(chatService.chatStream).mockImplementation(async function* () {
      yield* stream();
    });

    renderChat();
    await screen.findByText(/54 browser tools available/);

    const textarea = screen.getByLabelText("Message");
    fireEvent.change(textarea, { target: { value: "go" } });
    fireEvent.click(screen.getByText("Send"));

    expect((await screen.findAllByText("browser.goto")).length).toBeGreaterThan(0);
    expect(await screen.findByText("result")).toBeTruthy();
    expect(screen.queryByText('{"url":"https://x"}')).toBeNull();
    await waitFor(() => expect(chatService.chatStream).toHaveBeenCalled());
  });

  it("renders inline screenshot with caption and a file link for browser.screenshot results", async () => {
    const content = JSON.stringify({
      screenshot_path: "C:/shots/page_abc.png",
      mime_type: "image/png",
      width: 1280,
      height: 720,
      title: "Nasha Mukt YUVA | MYBharat",
      url: "https://mybharat.gov.in/nasha_mukt/delegate_registration",
      format: "png",
    });
    async function* stream() {
      yield { type: "tool_result", name: "browser.screenshot", content, error: false };
      yield { type: "done", content: "Done", steps: 1 };
    }
    vi.mocked(chatService.chatStream).mockImplementation(async function* () {
      yield* stream();
    });

    renderChat();
    await screen.findByText(/54 browser tools available/);

    const textarea = screen.getByLabelText("Message");
    fireEvent.change(textarea, { target: { value: "screenshot" } });
    fireEvent.click(screen.getByText("Send"));

    const image = await screen.findByRole("img", { name: "Nasha Mukt YUVA | MYBharat" });
    expect(image.getAttribute("src")).toBe("/api/v1/screenshots/page_abc.png");
    expect(screen.getByText("Nasha Mukt YUVA | MYBharat")).toBeDefined();

    const link = await screen.findByRole("link", { name: /open screenshot file/i });
    expect(link.getAttribute("href")).toBe("/api/v1/screenshots/page_abc.png");
  });

  it("shows an error message when the stream fails", async () => {
    vi.mocked(chatService.chatStream).mockImplementation(async function* () {
      yield { type: "error", detail: "connection refused" };
    });

    renderChat();
    await screen.findByText(/54 browser tools available/);

    const textarea = screen.getByLabelText("Message");
    fireEvent.change(textarea, { target: { value: "hi" } });
    fireEvent.click(screen.getByText("Send"));

    expect(await screen.findByText("connection refused")).toBeTruthy();
  });
});
