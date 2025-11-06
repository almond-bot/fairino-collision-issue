import time

from robot import RPC

ARM_IP = "192.168.57.2"
HOME_POSE = [200, 60, 500, -90, 0, -45]
COLLISION_CHECK_POSE = [200, 60, 550, -90, 0, -45]
TOP_POSE = [200, 60, 1000, -90, 0, -45]

def main():
    arm = RPC(ARM_IP)

    arm.SetSpeed(100)
    arm.SetOaccScale(100)
    arm.SetCollisionStrategy(2)
    arm.SetAnticollision(0, [10, 10, 10, 10, 10, 10], 0)

    arm.MoveL(
        desc_pos=HOME_POSE,
        tool=1,
        user=0,
        vel=10,
        acc=10,
    )

    while True:
        arm.SetAnticollision(0, [1, 1, 1, 1, 1, 1], 0)

        arm.MoveL(
            desc_pos=COLLISION_CHECK_POSE,
            tool=1,
            user=0,
            vel=1,
            acc=100,
        )

        if arm.GetRobotErrorCode()[1][0] != 0:
            print("COLLISION DETECTED")
            print("Clearing Collision Error")

            arm.ResetAllError()

        arm.SetAnticollision(0, [10, 10, 10, 10, 10, 10], 0)

        arm.MoveL(
            desc_pos=TOP_POSE,
            tool=1,
            user=0,
            vel=100,
            acc=100,
        )

        arm.MoveL(
            desc_pos=HOME_POSE,
            tool=1,
            user=0,
            vel=100,
            acc=100,
        )

if __name__ == "__main__":
    main()