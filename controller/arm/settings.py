import time
from typing import Callable

from controller.arm import shared
from controller.arm.models import ArmMode, ArmState, CollisionStrategy
from core import utils
from models.arm_state import ArmCartesianState, ArmJointState

logger = utils.create_logger(__name__)

RETRY_ATTEMPTS = 3


# Only return if the setting was applied successfully within the timeout
def _verify(check: Callable[[], bool], action: Callable[[], int], *args, **kwargs):
    logger.debug(f"{action.__name__} started with args {args} and kwargs {kwargs}")
    start = time.time()
    i = 0
    while check():
        if time.time() - start > 1:
            raise Exception("Timeout waiting for arm to be in the desired state")

        err = action(*args, **kwargs)
        if err != 0:
            raise Exception(f"Arm error: {err}")

        i += 1
        time.sleep(shared.ARM_STATUS_RATE_SECONDS)

    logger.debug(f"{action.__name__} {i} times")
    logger.debug(f"{action.__name__} took {time.time() - start} seconds")


# If we can't check if a setting was applied, we try X times
def _try_multiple_times(action: Callable[[], int], *args, **kwargs):
    logger.debug(f"{action.__name__} started with args {args} and kwargs {kwargs}")

    for _ in range(RETRY_ATTEMPTS):
        err = action(*args, **kwargs)
        if err != 0:
            raise Exception(f"Arm error: {err}")

        time.sleep(shared.ARM_STATUS_RATE_SECONDS)

    logger.debug(f"{action.__name__} finished")


# MARK - Setters


def set_realtime_sample_rate(rate: int):
    arm = shared.get_arm()
    _try_multiple_times(arm.SetRobotRealtimeStateSamplePeriod, 1000 / rate)


def pause_motion():
    arm = shared.get_arm()

    _verify(
        lambda: not shared.is_motion_done()
        and shared.get_arm_state() != ArmState.SUSPEND,
        arm.PauseMotion,
    )

    shared.set_motion_paused(True)


def resume_motion():
    arm = shared.get_arm()

    _verify(
        lambda: shared.get_arm_state() == ArmState.SUSPEND,
        arm.ResumeMotion,
    )

    shared.set_motion_paused(False)


def stop_motion():
    arm = shared.get_arm()

    _verify(
        lambda: not shared.is_motion_done(),
        arm.StopMotion,
    )


def change_tcp(tcp: ArmCartesianState):
    arm = shared.get_arm()
    _try_multiple_times(arm.SetToolCoord, 1, tcp.to_list(), 0, 0, 0, 0)


def set_collision_level(level: ArmJointState):
    arm = shared.get_arm()

    level /= 10

    for config in [0, 1]:
        _try_multiple_times(arm.SetAnticollision, 1, level.to_list(), config)


def set_collision_strategy(strategy: CollisionStrategy):
    arm = shared.get_arm()
    _try_multiple_times(arm.SetCollisionStrategy, strategy.value)


def start_custom_collision_detection(threshold: ArmJointState):
    arm = shared.get_arm()
    threshold = [t if t is not None else 1e9 for t in threshold.to_list()]
    _try_multiple_times(
        arm.CustomCollisionDetectionStart,
        1,
        threshold,
        [1e9] * 6,
        0,
    )


def stop_custom_collision_detection():
    arm = shared.get_arm()
    _try_multiple_times(arm.CustomCollisionDetectionEnd)


def set_digital_output(id: int, value: int):
    shared.wait_for_motion_allowed()

    arm = shared.get_arm()
    _verify(lambda: get_digital_output(id) != value, arm.SetDO, id, value)


def set_tool_digital_output(id: int, value: int):
    shared.wait_for_motion_allowed()

    arm = shared.get_arm()
    _verify(lambda: get_tool_digital_output(id) != value, arm.SetToolDO, id, value)


def start_acceleration_smoothing():
    arm = shared.get_arm()
    _try_multiple_times(arm.AccSmoothStart, 1)


def set_global_velocity_and_acceleration(velocity: int, acceleration: int):
    arm = shared.get_arm()

    _try_multiple_times(arm.SetSpeed, velocity)
    _try_multiple_times(arm.SetOaccScale, acceleration)


def clear_errors():
    arm = shared.get_arm()
    _verify(shared.error_detected, arm.ResetAllError)


def set_automatic_mode():
    arm = shared.get_arm()
    _verify(lambda: shared.get_arm_mode() != ArmMode.AUTOMATIC, arm.Mode, 0)


def set_manual_mode():
    arm = shared.get_arm()
    _verify(lambda: shared.get_arm_mode() != ArmMode.MANUAL, arm.Mode, 1)


def enable_drag_mode():
    arm = shared.get_arm()

    _verify(lambda: shared.get_arm_state() != ArmState.DRAG, arm.DragTeachSwitch, 1)


def disable_drag_mode():
    arm = shared.get_arm()
    _verify(lambda: shared.get_arm_state() == ArmState.DRAG, arm.DragTeachSwitch, 0)


# MARK - Getters


def get_digital_output(id: int) -> int:
    arm_status = shared.get_arm_status()

    if 0 <= id < 8:
        return (arm_status.cl_dgt_output_l & (0x01 << id)) >> id
    elif 8 <= id < 16:
        id -= 8
        return (arm_status.cl_dgt_output_h & (0x01 << id)) >> id
    else:
        return 0


def get_digital_input(id: int) -> int:
    arm_status = shared.get_arm_status()

    if 0 <= id < 8:
        return (arm_status.cl_dgt_input_l & (0x01 << id)) >> id
    elif 8 <= id < 16:
        id -= 8
        return (arm_status.cl_dgt_input_h & (0x01 << id)) >> id
    else:
        return 0


def get_tool_digital_output(id: int) -> int:
    arm_status = shared.get_arm_status()

    if 0 <= id < 2:
        return (arm_status.tl_dgt_output_l & (0x01 << id)) >> id
    else:
        return 0


def wait_for_motion_allowed():
    from core.health import raise_if_cancelled

    raise_if_cancelled()

    logger.debug("Motion allowed")


def get_tool_digital_input(id: int) -> int:
    arm_status = shared.get_arm_status()

    if 0 <= id < 2:
        id += 1
        return (arm_status.tl_dgt_input_l & (0x01 << id)) >> id
    else:
        return 0
