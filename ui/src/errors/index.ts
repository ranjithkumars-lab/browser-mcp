export class UiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "UiError";
  }
}

export class ApiConnectionError extends UiError {
  constructor(message: string) {
    super(0, message);
    this.name = "ApiConnectionError";
  }
}

export class WebSocketDisconnectedError extends Error {
  constructor(message = "WebSocket connection lost") {
    super(message);
    this.name = "WebSocketDisconnectedError";
  }
}