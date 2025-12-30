# src/producer/data_simulator.py
import uuid
import random
import datetime

class Simulator:
    def __init__(self, mode="normal"):
        self.mode = mode
        self.drift_factor = 0.0
        self.primary_fault_machine = f"mach-{random.randint(1,10):02d}"
        self.secondary_spread = False

    def next_event(self):
        base_temp = 60.0
        base_vibration = 0.02

        machine_id = f"mach-{random.randint(1,10):02d}"

        temp = base_temp + random.uniform(-2, 2)
        vibration = base_vibration + random.uniform(-0.01, 0.02)

        if self.mode == "gradual_drift":
            if machine_id == self.primary_fault_machine:
                self.drift_factor += 0.2  # slow drift
                temp += self.drift_factor
                vibration += self.drift_factor * 0.04

                # After strong drift, allow cascade
                if self.drift_factor > 4:
                    self.secondary_spread = True

            elif self.secondary_spread:
                temp += random.uniform(2, 5)
                vibration += random.uniform(0.05, 0.15)

        elif self.mode == "sudden_fault":
            if machine_id == self.primary_fault_machine:
                temp += random.uniform(30, 45)
                vibration += random.uniform(1.0, 2.0)

        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "machine_id": machine_id,
            "component_id": f"comp-{random.randint(1,20):03d}",
            "temperature_c": round(temp, 3),
            "vibration_mm_s": round(vibration, 4),
            "rpm": random.randint(1000, 5000)
        }
