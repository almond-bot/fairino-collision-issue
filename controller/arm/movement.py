import time

from controller.arm import settings, shared
from controller.arm.models import CollisionStrategy, CoordinateSystem
from core import utils
from core.exceptions import CancelledTaskErrorCollisionDetected
from models.arm_state import ArmCartesianState, ArmJointState

logger = utils.create_logger(__name__)

def linear(
    arm_cartesian_state: ArmCartesianState,
    velocity: int | None = None,
    acceleration: int | None = None,
    radius: int | None = None,
):
    shared.wait_for_motion_allowed()

    arm = shared.get_arm()

    logger.debug(
        f"Moving linear to {arm_cartesian_state.to_list()} with velocity {velocity}, acceleration {acceleration}, radius {radius}"
    )
    err = arm.MoveL(
        list(arm_cartesian_state.to_list()),
        1,
        0,
        vel=velocity
        if velocity is not None and velocity < shared.ARM_L_VELOCITY
        else shared.ARM_L_VELOCITY,
        acc=acceleration if acceleration is not None else shared.ARM_L_ACCELERATION,
        blendR=radius if radius is not None else 0,
    )

    if radius is None:
        wait_to_stabilize()
        logger.debug("Finished moving linear")

    if err != 0:
        raise Exception(f"Arm error: {err}")


def linear_offset(
    offset: ArmCartesianState,
    start: ArmCartesianState | None = None,
    velocity: int | None = None,
    acceleration: int | None = None,
    radius: int | None = None,
    coordinate_system: CoordinateSystem = CoordinateSystem.TOOL,
):
    shared.wait_for_motion_allowed()

    arm = shared.get_arm()
    current_pos = start if start is not None else shared.get_arm_cartesian_state()

    logger.debug(
        f"Moving linear offset from {current_pos.to_list()} to {offset.to_list()} with velocity {velocity}, acceleration {acceleration}, radius {radius}"
    )
    err = arm.MoveL(
        list(current_pos.to_list()),
        1,
        0,
        vel=velocity
        if velocity is not None and velocity < shared.ARM_L_VELOCITY
        else shared.ARM_L_VELOCITY,
        acc=acceleration if acceleration is not None else shared.ARM_L_ACCELERATION,
        offset_flag=coordinate_system.value,
        offset_pos=list(offset.to_list()),
        blendR=radius if radius is not None else 0,
    )

    if radius is None:
        wait_to_stabilize()
        logger.debug("Finished moving linear offset")

    if err != 0:
        raise Exception(f"Arm error: {err}")


# MARK - Helpers


def torque_check(
    max_drop: float,
    dir: ArmCartesianState,
    threshold: ArmJointState,
    sleep: bool = True,
) -> tuple[bool, float]:
    settings.set_collision_strategy(CollisionStrategy.ERROR_STOP)
    settings.start_custom_collision_detection(threshold)
    start_pose = shared.get_arm_cartesian_state()

    linear_offset(dir * max_drop, velocity=1, acceleration=100, radius=0)

    logger.debug(
        f"Starting torque check with max drop {max_drop} in direction {dir.to_list()} and threshold {threshold.to_list()}"
    )
    drop = 0
    while not (shared.collision_detected()):
        try:
            shared.wait_for_motion_allowed()
        except CancelledTaskErrorCollisionDetected:
            pass

        if drop > max_drop:
            logger.warning("Torque check exceeded max drop")
            settings.stop_motion()
            return False, drop

        time.sleep(shared.ARM_STATUS_RATE_SECONDS)

        incremental_pose = shared.get_arm_cartesian_state()
        drop = start_pose.get_linear_distance(incremental_pose)

    logger.debug(f"Finished torque check with drop {drop}")

    settings.clear_errors()
    settings.stop_custom_collision_detection()
    settings.set_collision_strategy(CollisionStrategy.IMPACT_REBOUND)
    settings.set_collision_level(
        ArmJointState(j1=100, j2=100, j3=100, j4=100, j5=100, j6=100)
    )

    # 5 second sleep to "fix" phantom vibrations
    if sleep:
        for _ in range(10):
            shared.wait_for_motion_allowed()
            time.sleep(0.5)

    return True, drop


def wait_to_stabilize(
    extra_time: float = 0,
    timeout: float = 120,
):
    """
    Wait for the arm to stabilize by monitoring the motion done flag.

    Args:
        extra_time: Extra time to wait after stabilization
    """
    if timeout <= 0:
        raise ValueError("Timeout must be greater than 0")

    check_interval = 0.01
    stable_duration = 0.1
    stable_start_time = None

    logger.debug(f"Waiting for arm to stabilize with timeout {timeout}s")
    timeout_time = time.time() + timeout
    while time.time() < timeout_time:
        if shared.is_motion_done():
            current_time = time.time()

            if stable_start_time is None:
                stable_start_time = current_time
            elif current_time - stable_start_time >= stable_duration:
                time.sleep(extra_time)
                logger.debug(
                    f"Arm stabilized in {current_time - stable_start_time:.2f}s + extra time {extra_time:.2f}s"
                )
                return
        else:
            stable_start_time = None

        time.sleep(check_interval)

    raise TimeoutError("Arm did not stabilize within timeout")
