class SyncUpstreamError(Exception):
    """
    Raised when central-api can't be reached or returns an error response.
    Caught at the top of each sync cycle in `app.runner` — a failed cycle
    just gets retried on the next tick, it never crashes the worker.
    """
