import math
import os
import time
from abc import ABC, abstractmethod


class DroneProvider(ABC):
    @abstractmethod
    async def connect(self): ...
    @abstractmethod
    async def telemetry(self) -> dict: ...


class MockDroneProvider(DroneProvider):
    async def connect(self): return {"connected": True, "mode": "simulation"}
    async def telemetry(self) -> dict:
        phase = time.time() / 20
        return {"latitude": 29.7605 + math.sin(phase) * 0.0003, "longitude": -95.3001 + math.cos(phase) * 0.0003, "altitude": 74.2, "heading": int((phase * 20) % 360), "battery": 87, "speed": 6.4, "mission_state": "surveying", "simulated": True}
    async def arm(self): return {"simulated": True, "state": "armed"}
    async def takeoff(self): return {"simulated": True, "state": "airborne"}
    async def goto(self, latitude, longitude, altitude): return {"simulated": True, "target": [latitude, longitude, altitude]}
    async def start_mission(self): return {"simulated": True, "state": "surveying"}
    async def return_to_launch(self): return {"simulated": True, "state": "returning"}


class MAVSDKDroneProvider(DroneProvider):
    def __init__(self):
        if os.getenv("DRONE_MODE", "simulation") != "mavsdk" or os.getenv("DRONE_ALLOW_REAL_FLIGHT", "false").lower() != "true":
            raise RuntimeError("Real flight requires DRONE_MODE=mavsdk and DRONE_ALLOW_REAL_FLIGHT=true")
        self.system_address = os.getenv("MAVSDK_SYSTEM_ADDRESS", "udp://:14540")

    async def connect(self):
        from mavsdk import System
        self.drone = System()
        await self.drone.connect(system_address=self.system_address)
        return {"connected": True, "mode": "mavsdk"}

    async def telemetry(self):
        async for position in self.drone.telemetry.position():
            return {"latitude": position.latitude_deg, "longitude": position.longitude_deg, "altitude": position.relative_altitude_m, "simulated": False}

    async def arm(self): await self.drone.action.arm()
    async def takeoff(self): await self.drone.action.takeoff()
    async def goto(self, latitude, longitude, altitude): await self.drone.action.goto_location(latitude, longitude, altitude, 0)
    async def start_mission(self): await self.drone.mission.start_mission()
    async def return_to_launch(self): await self.drone.action.return_to_launch()
