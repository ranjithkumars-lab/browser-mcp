from browser_mcp.errors import BrowserError


class WorkerError(BrowserError):
    pass


class JobClaimError(WorkerError):
    pass


class QueueConnectionError(WorkerError):
    pass


class JobExecutionError(WorkerError):
    pass
