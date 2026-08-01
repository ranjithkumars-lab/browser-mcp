from browser_mcp.errors import BrowserError


class EventEngineError(BrowserError):
    pass


class InvalidEventPatternError(EventEngineError):
    pass


class SubscriberExecutionError(EventEngineError):
    pass


class EventBufferFullError(EventEngineError):
    pass


class MiddlewareExecutionError(EventEngineError):
    pass


class StreamDisconnectedError(EventEngineError):
    pass
