import threading
import time

from controller.arm import settings
from controller.arm.models import ArmMode, ArmState, CollisionStrategy
from core import utils
from lib.fairino.robot import RPC, RobotStatePkg
from models.arm_state import ArmCartesianState, ArmJointState

ARM_IP = "192.168.57.2"
ARM_PORT = 20004
ARM_STATUS_RATE = 100  # Hz
ARM_STATUS_RATE_SECONDS = 1 / ARM_STATUS_RATE
ARM_L_VELOCITY = 10
ARM_J_VELOCITY = 10
ARM_L_ACCELERATION = 10
ARM_J_ACCELERATION = 10

logger = utils.create_logger(__name__)

_arm: RPC | None = None
_arm_status: RobotStatePkg | None = None
_is_motion_paused_event = threading.Event()


# MARK - Connection


RETRY_ATTEMPTS = 3
connect_lock = threading.Lock()


def connect():
    with connect_lock:
        global _arm
        logger.info("Connecting to arm")

        if _arm:
            logger.info("Arm already connected, skipping connection")
            return
        else:
            # Reset RPC.is_conect
            RPC.is_conect = True
            _arm = RPC(ARM_IP)

        if not _arm.is_conect:
            logger.warning("Failed to connect to arm, cleaning up RPC client")
            _arm.CloseRPC()
            _arm = None
            return

        logger.info("Arm connected")


def disconnect():
    with connect_lock:
        global _arm
        logger.info("Disconnecting from arm")

        if not _arm:
            return

        _arm.CloseRPC()
        _arm = None

        logger.info("Disconnected from arm")


def setup(l_velocity: int, j_velocity: int, l_acceleration: int, j_acceleration: int):
    global ARM_L_VELOCITY, ARM_J_VELOCITY, ARM_L_ACCELERATION, ARM_J_ACCELERATION

    # Try to connect arm if it is not connected
    if not is_connected():
        for attempt in range(RETRY_ATTEMPTS):
            logger.warning("Arm not connected, trying to reconnect")
            connect()

            if is_connected():
                break

            # Add a small delay between retry attempts, except after the last attempt
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(0.1)

        if not is_connected():
            raise Exception("Arm not connected")

    settings.set_realtime_sample_rate(ARM_STATUS_RATE)
    settings.clear_errors()
    settings.resume_motion()
    settings.disable_drag_mode()
    settings.stop_custom_collision_detection()
    settings.set_collision_strategy(CollisionStrategy.IMPACT_REBOUND)
    settings.set_collision_level(
        ArmJointState(j1=100, j2=100, j3=100, j4=100, j5=100, j6=100)
    )
    settings.change_tcp(ArmCartesianState(y=-88, z=19.35))
    settings.set_automatic_mode()
    settings.start_acceleration_smoothing()
    settings.set_global_velocity_and_acceleration(velocity=100, acceleration=100)
    ARM_L_VELOCITY = l_velocity
    ARM_J_VELOCITY = j_velocity
    ARM_L_ACCELERATION = l_acceleration
    ARM_J_ACCELERATION = j_acceleration


# MARK - Getters


def get_arm() -> RPC:
    # Try to connect arm
    if not is_connected():
        for attempt in range(RETRY_ATTEMPTS):
            logger.warning("Arm not connected, trying to reconnect")
            connect()

            if is_connected():
                break

            # Add a small delay between retry attempts, except after the last attempt
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(0.1)

        if not is_connected():
            raise Exception("Arm not connected")

    return _arm


def is_connected() -> bool:
    return _arm is not None and _arm.robot is not None and _arm.is_conect


def is_motion_paused() -> bool:
    return _is_motion_paused_event.is_set()


def get_arm_status(
    timeout: float = 10, throw_on_timeout: bool = True
) -> RobotStatePkg | None:
    if _arm_status is not None:
        return _arm_status

    end_time = time.time() + timeout
    while time.time() < end_time:
        time.sleep(0.1)
        if _arm_status is not None:
            logger.debug(f"Got arm status in {time.time() - end_time:.2f}s")
            return _arm_status

    if throw_on_timeout:
        raise TimeoutError("Arm status not available within timeout")


def get_arm_joint_state() -> ArmJointState | None:
    arm_status = get_arm_status()
    arm_joint_state = ArmJointState(*arm_status.jt_cur_pos)
    return arm_joint_state


def get_arm_cartesian_state() -> ArmCartesianState | None:
    arm_status = get_arm_status()
    arm_cartesian_state = ArmCartesianState(*arm_status.tl_cur_pos)
    return arm_cartesian_state


def get_arm_torque_state() -> ArmJointState | None:
    arm_status = get_arm_status()
    arm_torque_state = ArmJointState(*arm_status.jt_cur_tor) * 1000
    return arm_torque_state


def collision_detected() -> bool | None:
    arm_status = get_arm_status()
    arm_collision_state = bool(arm_status.collisionState)
    return arm_collision_state


def emergency_stop_detected() -> bool | None:
    arm_status = get_arm_status(timeout=1, throw_on_timeout=False)
    if arm_status is None:
        return None

    arm_emergency_stop_state = bool(arm_status.EmergencyStop)
    return arm_emergency_stop_state


def error_detected() -> bool | None:
    arm_status = get_arm_status()
    arm_error_state = arm_status.main_code != 0 or arm_status.sub_code != 0
    return arm_error_state


def is_motion_done() -> bool | None:
    arm_status = get_arm_status()
    motion_done = bool(arm_status.motion_done)
    return motion_done


def get_arm_state() -> ArmState | None:
    arm_status = get_arm_status()
    arm_state = ArmState(arm_status.robot_state)
    return arm_state


def get_arm_mode() -> ArmMode | None:
    arm_status = get_arm_status()
    arm_mode = ArmMode(arm_status.robot_mode)
    return arm_mode


# MARK - Setters


def set_arm_status(status: RobotStatePkg):
    global _arm_status
    _arm_status = status


def set_motion_paused(paused: bool):
    if paused:
        _is_motion_paused_event.set()
    else:
        _is_motion_paused_event.clear()


# MARK - Helpers


def reset():
    settings.clear_errors()
    settings.enable_drag_mode()
