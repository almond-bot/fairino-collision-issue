import asyncio
import time

from controller import arm
from core.exceptions import CancelledTaskErrorCollisionDetected
from models.arm_state import ArmCartesianState, ArmJointState

HOME_POSE = ArmCartesianState(
    x=200,
    y=60,
    z=500,
    roll=-90,
    pitch=0,
    yaw=-45,
)

def job():
    arm.shared.setup(l_velocity=100, l_acceleration=100, j_velocity=100, j_acceleration=100)
    arm.movement.linear(HOME_POSE, velocity=10, acceleration=10)

    while True:
        try:
            hit, _ = arm.movement.torque_check(max_drop=20, dir=ArmCartesianState(y=-1), threshold=ArmJointState(j5=0.05), sleep=False)
            if hit:
                arm.movement.linear(HOME_POSE, velocity=10, acceleration=10, radius=0)

            arm.movement.linear_offset(ArmCartesianState(y=-230), radius=0)
            arm.movement.linear(HOME_POSE)
        except CancelledTaskErrorCollisionDetected:
            continue

async def main():
    asyncio.create_task(arm.tasks.run_arm_status())
    time.sleep(1)
    await asyncio.to_thread(job)

if __name__ == "__main__":
    asyncio.run(main())