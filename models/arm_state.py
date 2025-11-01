from dataclasses import dataclass


@dataclass
class ArmJointState:
    j1: float | None = None
    j2: float | None = None
    j3: float | None = None
    j4: float | None = None
    j5: float | None = None
    j6: float | None = None

    def to_list(self) -> list[float | None]:
        return [self.j1, self.j2, self.j3, self.j4, self.j5, self.j6]

    def to_dict(self) -> dict[str, float | None]:
        return {
            "j1": self.j1,
            "j2": self.j2,
            "j3": self.j3,
            "j4": self.j4,
            "j5": self.j5,
            "j6": self.j6,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            j1=data["j1"],
            j2=data["j2"],
            j3=data["j3"],
            j4=data["j4"],
            j5=data["j5"],
            j6=data["j6"],
        )

    def __add__(self, other: "ArmJointState") -> "ArmJointState":
        return ArmJointState(
            j1=self.j1 + other.j1,
            j2=self.j2 + other.j2,
            j3=self.j3 + other.j3,
            j4=self.j4 + other.j4,
            j5=self.j5 + other.j5,
            j6=self.j6 + other.j6,
        )

    def __radd__(self, other: float) -> "ArmJointState":
        return self + ArmJointState(
            j1=other, j2=other, j3=other, j4=other, j5=other, j6=other
        )

    def __truediv__(self, other: float) -> "ArmJointState":
        return ArmJointState(
            j1=self.j1 / other,
            j2=self.j2 / other,
            j3=self.j3 / other,
            j4=self.j4 / other,
            j5=self.j5 / other,
            j6=self.j6 / other,
        )

    def __mul__(self, other: float) -> "ArmJointState":
        return ArmJointState(
            j1=self.j1 * other,
            j2=self.j2 * other,
            j3=self.j3 * other,
            j4=self.j4 * other,
            j5=self.j5 * other,
            j6=self.j6 * other,
        )

    def __str__(self):
        return f"ArmJointState(j1={round(self.j1, 2)}, j2={round(self.j2, 2)}, j3={round(self.j3, 2)}, j4={round(self.j4, 2)}, j5={round(self.j5, 2)}, j6={round(self.j6, 2)})"


@dataclass
class ArmCartesianState:
    x: float = 0
    y: float = 0
    z: float = 0
    roll: float = 0
    pitch: float = 0
    yaw: float = 0

    def to_list(self) -> list[float]:
        return [self.x, self.y, self.z, self.roll, self.pitch, self.yaw]

    def to_dict(self) -> dict[str, float]:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "roll": self.roll,
            "pitch": self.pitch,
            "yaw": self.yaw,
        }

    def copy(self) -> "ArmCartesianState":
        return ArmCartesianState(
            x=self.x,
            y=self.y,
            z=self.z,
            roll=self.roll,
            pitch=self.pitch,
            yaw=self.yaw,
        )

    @classmethod
    def from_dict(cls, data):
        return cls(
            x=data["x"],
            y=data["y"],
            z=data["z"],
            roll=data["roll"],
            pitch=data["pitch"],
            yaw=data["yaw"],
        )

    def __add__(self, other: "ArmCartesianState") -> "ArmCartesianState":
        return ArmCartesianState(
            x=self.x + other.x,
            y=self.y + other.y,
            z=self.z + other.z,
            roll=self.roll + other.roll,
            pitch=self.pitch + other.pitch,
            yaw=self.yaw + other.yaw,
        )

    def __sub__(self, other: "ArmCartesianState") -> "ArmCartesianState":
        return ArmCartesianState(
            x=self.x - other.x,
            y=self.y - other.y,
            z=self.z - other.z,
            roll=self.roll - other.roll,
            pitch=self.pitch - other.pitch,
            yaw=self.yaw - other.yaw,
        )

    def __mul__(self, other: float) -> "ArmCartesianState":
        return ArmCartesianState(
            x=self.x * other,
            y=self.y * other,
            z=self.z * other,
            roll=self.roll * other,
            pitch=self.pitch * other,
            yaw=self.yaw * other,
        )

    def __truediv__(self, other: float) -> "ArmCartesianState":
        return ArmCartesianState(
            x=self.x / other,
            y=self.y / other,
            z=self.z / other,
            roll=self.roll / other,
            pitch=self.pitch / other,
            yaw=self.yaw / other,
        )

    def get_linear_distance(self, other: "ArmCartesianState") -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return (dx**2 + dy**2 + dz**2) ** 0.5

    def __str__(self):
        return f"ArmCartesianState(x={round(self.x, 2)}, y={round(self.y, 2)}, z={round(self.z, 2)}, roll={round(self.roll, 2)}, pitch={round(self.pitch, 2)}, yaw={round(self.yaw, 2)})"
