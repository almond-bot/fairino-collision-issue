from enum import Enum


class ArmState(Enum):
    STOP = 1
    RUN = 2
    SUSPEND = 3
    DRAG = 4


class ArmMode(Enum):
    AUTOMATIC = 0
    MANUAL = 1


class CoordinateSystem(Enum):
    BASE = 1
    TOOL = 2


class CollisionStrategy(Enum):
    ERROR_PAUSE = 0
    KEEP_RUNNING = 1
    ERROR_STOP = 2
    HEAVY_MOMENT = 3
    SHOCK_RESPONSE = 4
    IMPACT_REBOUND = 5
