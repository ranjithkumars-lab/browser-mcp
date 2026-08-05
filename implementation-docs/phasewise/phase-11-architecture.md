# Phase 11: Presentation Gateway & Parameter Resolver

This document outlines the architectural enhancements introduced in Phase 11 to solve LLM hallucination and state-tracking problems.

## 1. Parameter Resolver & Execution Context

### The Problem
Previously, the backend relied exclusively on prompt engineering to force the LLM to manage internal infrastructure identifiers (like `session_id`, `context_id`, and `page_id`). This proved brittle, as small LLMs (like `gpt-oss:20b`) would frequently omit these required arguments, leading to raw `TypeError` exceptions during tool execution.

### The Solution
We implemented an **Execution Context** and a **Parameter Resolver** interceptor. 

#### Execution Context Lifecycle
- **Initialization**: At the start of a chat stream, `ExecutionContext.from_messages(messages)` reconstructs the active state by replaying the conversation history (e.g., looking for past `browser.create_session` results).
- **Dynamic Updates**: As the agent executes tools in real-time, `exec_context.update_from_result(name, result)` updates the context with any new IDs.

#### Parameter Resolver Flow
When the LLM calls a tool:
1. `ChatAgent` receives the raw arguments.
2. `resolver.resolve(name, arguments)` is called.
3. If the tool requires `session_id` but the LLM omitted it, the resolver injects `exec_context.session_id`.
4. The ToolRegistry executes the tool with the fully resolved arguments.

This creates a clean architectural boundary where the LLM can just say `browser.screenshot()` without tracking infrastructure details.

## 2. Presentation Gateway Consistency Filter

### The Problem
When a tool execution failed (or if the LLM hallucinated without running a tool at all), the LLM might still output text like: *"Screenshot attached"* or *"Login completed successfully"*. This confused users because the UI showed the claim without the corresponding artifact or timeline evidence.

### The Solution
We enhanced the `PresentationGateway` (in `formatter.py`) to enforce evidence-based rendering.

#### Presentation Consistency Rules
1. During the chat stream, the backend routing layer tracks whether any `ArtifactMessage` or `WorkflowMessage` was emitted.
2. Before sending the final `done` event (which contains the assistant's synthesized text response), the stream invokes `_formatter.filter_hallucinations()`.
3. The filter checks for hardcoded hallucinated phrases (e.g., `"screenshot attached"`, `"download completed"`, `"login succeeded"`).
4. If the required evidence (e.g., `has_artifacts=True`) is missing, the gateway strips these phrases from the text via regex replacement.

This guarantees that the Presentation Layer will never claim an artifact exists unless the system actually generated one.
