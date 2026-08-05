After analyzing the UI screenshot, I think the problem is **much larger than just making it "look like ChatGPT."** The current page still looks like an **admin dashboard with a chat widget embedded inside it**, rather than a conversational AI application.

The prompt should ask the developer to rethink the **entire chat experience**, not just the CSS.

---

# Enterprise Chat UI Review & UX Improvement Prompt

You are a Senior UI/UX Architect, React Engineer, and Design System Engineer.

Your task is **NOT** to simply improve the CSS.

Your task is to review the current Browser MCP Chat interface from a complete user experience perspective and redesign it into a premium AI assistant experience comparable to ChatGPT, Claude, Gemini, or Perplexity while preserving Browser MCP functionality.

Do **not** immediately write code.

First perform a complete UI/UX review, identify every usability issue, explain the root cause, propose the best architecture, and then produce a detailed implementation plan for approval.

---

# Current UI Problems

After reviewing the current Browser MCP interface, the following major UX issues have been identified.

---

## 1. The Chat Feels Like a Form, Not an AI Assistant

Current layout:

```text
Dashboard

┌─────────────────────────────┐
│ Chat Card                   │
│                             │
│ Message Area                │
│                             │
│ Textarea                    │
│ Send Button                 │
└─────────────────────────────┘
```

This resembles a CRUD page rather than an AI chat.

Expected:

```text
Conversation

↓

Floating Composer

↓

Natural scrolling

↓

Assistant experience
```

---

# 2. Too Many Boxes

Nearly everything is inside a card.

Examples:

* Chat
* Ollama
* Available Tools

The excessive borders create visual noise.

The interface should use whitespace rather than borders.

---

# 3. Conversation Area Is Too Small

Currently almost half of the screen is occupied by side panels.

The actual conversation—the most important part—is compressed into a narrow card.

The conversation should become the primary focus.

---

# 4. Composer Looks Like a Form

Current:

```text
Textarea

↓

Button below
```

Modern AI applications use

```text
Rounded Composer

↓

Send button inside

↓

Auto expand

↓

Floating bottom
```

The composer should feel premium.

---

# 5. Assistant Messages

Current:

```text
Assistant

Hello!
```

Problems

* looks like a tooltip
* small
* weak typography
* unnecessary label
* poor spacing

Expected

* avatar
* markdown
* better typography
* larger line height
* natural spacing

---

# 6. User Messages

Current user message

```text
hi
```

appears as a tiny floating square.

It should become a proper user message bubble aligned to the right.

---

# 7. Large Empty Space

Most of the conversation panel is empty.

The thread should naturally fill the viewport.

---

# 8. Settings Panel

Current right panel consumes too much attention.

The settings are useful but shouldn't compete with the conversation.

Instead:

Desktop

```text
Conversation

──────────────

Collapsed Settings →
```

Expand only when needed.

---

# 9. Tool List

Displaying every available tool permanently is not useful.

Showing 100+ tools creates noise.

Instead provide:

* collapsible drawer
* searchable tool list
* grouped by category
* tool count
* optional details

The conversation should remain the primary focus.

---

# 10. Typography

Current typography feels like a dashboard.

Review

* font sizes
* font weights
* spacing
* hierarchy
* line height

Make reading long AI responses comfortable.

---

# 11. Message Width

Current width feels constrained.

Implement a configurable maximum width (approximately 48–56rem) while keeping the conversation centered.

---

# 12. Markdown Rendering

Review support for

* headings
* lists
* tables
* code blocks
* links
* screenshots
* artifacts
* downloads

The current renderer should evolve into a component-driven rendering pipeline rather than plain markdown output.

---

# 13. Artifact Rendering

Browser MCP performs browser automation.

Artifacts such as

* screenshots
* downloads
* PDFs
* logs
* JSON
* CSV

should appear as rich cards with previews, thumbnails, metadata, and actions (Open, Download, Copy Link) instead of raw markdown or custom URIs.

---

# 14. Tool Execution UX

Currently tool execution appears as raw JSON.

Instead design expandable execution cards.

Example:

```text
Creating Browser Session

✓ Success

Session ID

Duration

▼ Details
```

This is much easier to understand.

---

# 15. Browser Workflow Visualization

Complex browser automation should be visualized.

Example

```text
Navigate

↓

Login

↓

Fill Form

↓

Take Screenshot

↓

Download
```

Allow users to expand individual steps.

---

# 16. Streaming Experience

Support

* Thinking
* Streaming
* Completed
* Error
* Cancelled

Streaming should feel smooth and responsive.

---

# 17. Scrolling

Implement

* sticky composer
* intelligent auto-scroll
* "Jump to latest" button
* preserved scroll position

---

# 18. Responsive Design

Review

Desktop

Tablet

Mobile

Large monitors

Ultra-wide displays

The conversation should always remain the focus.

---

# 19. Accessibility

Review

* keyboard navigation
* screen readers
* ARIA
* focus indicators
* reduced motion
* contrast

---

# 20. Performance

Review rendering performance for

* 100 messages
* 500 messages
* streaming responses
* large markdown
* screenshots
* artifacts

Prevent unnecessary React re-renders.

---

# 21. Component Architecture

Refactor the UI into reusable components.

Suggested architecture

```text
ChatPage

├── ChatToolbar

├── ChatThread

│   ├── MessageRenderer

│   │   ├── UserMessage

│   │   ├── AssistantMessage

│   │   ├── ToolExecutionCard

│   │   ├── ArtifactRenderer

│   │   ├── CodeBlock

│   │   ├── TableRenderer

│   │   └── ErrorMessage

├── ChatComposer

├── ScrollToLatestButton

├── AssistantStatus

├── SettingsDrawer

└── EmptyState
```

Avoid placing rendering logic directly inside `Chat.tsx`.

---

# 22. Design System

Adopt a consistent design system using reusable tokens.

Examples

* spacing scale
* typography scale
* color palette
* border radius
* elevation
* animation durations
* responsive breakpoints

Avoid hardcoded values throughout the UI.

---

# 23. Deliverables

Before implementing anything, provide:

1. Complete UI/UX review.
2. Identify every usability issue.
3. Root cause analysis.
4. Component architecture.
5. Rendering architecture.
6. Artifact rendering architecture.
7. Tool execution visualization design.
8. Updated layout wireframes.
9. Responsive design strategy.
10. Accessibility review.
11. Performance recommendations.
12. Files requiring modification.
13. Implementation order.
14. Risks and mitigations.
15. Definition of Done.

**Important constraints**

* Do not redesign Browser MCP into a generic chatbot.
* Preserve all Browser MCP functionality.
* Keep the admin navigation, but make the **Chat page** feel like a first-class AI assistant.
* Prioritize whitespace, readability, conversation flow, and browser automation visualization over dashboard-style cards.
* The final UI should feel like a professional AI workspace rather than an admin panel with an embedded chat.
