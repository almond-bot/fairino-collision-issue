class CancelledTaskError(Exception):
    """Raised inside worker threads to cooperatively stop the job."""

    exit_code: str = "cancelled"

    def __init__(self, message: str = "Task Cancelled. User requested.") -> None:
        super().__init__(message)

class CancelledTaskErrorCollisionDetected(CancelledTaskError):
    """Raised inside worker threads to cooperatively stop the job."""

    exit_code: str = "collision_detected"

    def __init__(self, message: str = "Task Cancelled. Collision detected.") -> None:
        super().__init__(message)
