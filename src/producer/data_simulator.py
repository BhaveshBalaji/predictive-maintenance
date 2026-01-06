# src/producer/data_simulator.py
import uuid
import random
import datetime

class Simulator:
    def __init__(self, mode="normal"):
        self.mode = mode
        self.drift_factor = 0.0
        # Randomly select a machine to simulate fault
        self.primary_fault_machine = f"mach-{random.randint(1,10):02d}"
        self.secondary_spread = False

    def next_event(self):

        # Randomly select a machine for the event
        base_temp = 60.0
        base_vibration = 0.02

        machine_id = f"mach-{random.randint(1,10):02d}"

        temp = base_temp + random.uniform(-0.5, 0.5)
        vibration = base_vibration + random.uniform(-0.003, 0.003)

        # Gradual drift simulation
        if self.mode == "gradual_drift":
            if machine_id == self.primary_fault_machine:
                self.drift_factor += 0.05  # slower, more realistic drift
                temp += self.drift_factor
                vibration += self.drift_factor * 0.02

                # After significant drift, allow a CHANCE of cascade (not always)
                if self.drift_factor > 5 and not self.secondary_spread:
                    if random.random() < 0.3: # 30% chance to start spreading
                        self.secondary_spread = True

            elif self.secondary_spread:
                # Only affect some machines during spread, not all
                if random.random() < 0.4:
                    temp += random.uniform(1, 3)
                    vibration += random.uniform(0.02, 0.08)

        # Sudden fault simulation
        elif self.mode == "sudden_fault":
            if machine_id == self.primary_fault_machine:
                temp += random.uniform(30, 45)
                vibration += random.uniform(1.0, 2.0)

        # Produce event
        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "machine_id": machine_id,
            "component_id": f"comp-{random.randint(1,20):03d}",
            "temperature_c": round(temp, 3),
            "vibration_mm_s": round(vibration, 4),
            "rpm": random.randint(1000, 5000)
        }

    # Reset machine state
    def reset_machine(self, machine_id):
        if machine_id == self.primary_fault_machine:
            self.drift_factor = 0.0
            self.secondary_spread = False
            # Pick a new fault machine for next time
            self.primary_fault_machine = f"mach-{random.randint(1,10):02d}"
