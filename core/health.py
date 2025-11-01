from controller import arm
from core.exceptions import (
    CancelledTaskErrorCollisionDetected,
)

def raise_if_cancelled():
    if arm.shared.collision_detected():
        raise CancelledTaskErrorCollisionDetected
