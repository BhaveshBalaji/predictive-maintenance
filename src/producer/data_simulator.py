# src/producer/data_simulator.py
import time
import uuid
import random
import datetime
from utils.confluent_client import read_config_from_envfile

TOPIC = "sensor.raw"

class Simulator:
    def __init__(self, mode="normal"):
        self.mode = mode

    def next_event(self):
        """Return a dict sensor event. If mode!='normal', generate anomalous values."""
        base_temp = 60.0
        base_vibration = 0.02
        
        if self.mode != "normal":
            # create drift/anomaly
            temp = base_temp + random.uniform(15.0, 40.0)
            vibration = base_vibration + random.uniform(0.2, 1.5)
        else:
            temp = base_temp + random.uniform(-2.0, 2.0)
            vibration = base_vibration + random.uniform(-0.01, 0.02)

        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "machine_id": f"mach-{random.randint(1,10):02d}",
            "component_id": f"comp-{random.randint(1,20):03d}",
            "temperature_c": round(temp, 3),
            "vibration_mm_s": round(vibration, 4),
            "rpm": random.randint(1000, 5000)
        }
        return event