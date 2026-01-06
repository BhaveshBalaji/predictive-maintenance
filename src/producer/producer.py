# src/producer/producer.py
from confluent_kafka import Producer, Consumer
import json, time, sys, os, datetime
from threading import Thread

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.confluent_client import get_producer_config, get_consumer_config
from .data_simulator import Simulator

# Kafka topics
RAW_TOPIC = "sensor.raw"
ACTION_TOPIC = "sensor.actions"

# Constants
TOTAL_MACHINES = {f"mach-{i:02d}" for i in range(1, 11)}
MAINTENANCE_DURATION = 60 # seconds
maintenance_queue = {} # machine_id -> restart_timestamp
stopped_machines = set()
shutdown = False
simulator = Simulator(mode="normal")

# Function to listen for actions
def listen_for_actions():
    """Listen for STOP_MACHINE and SCHEDULE_MAINTENANCE events"""
    global shutdown, simulator

    # Kafka consumer for actions
    consumer = Consumer(get_consumer_config(group_id="producer-control"))

    # Subscribe to action topic for stop_machine and schedule_maintenance events
    consumer.subscribe([ACTION_TOPIC])

    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue

        event = json.loads(msg.value().decode("utf-8"))
        action = event.get("action")
        machine = event.get("machine_id")

        if action == "SYSTEM_SHUTDOWN":
            print("🛑 Global shutdown signal received")
            shutdown = True
            break

        # Handle Simulator Mode changes
        if action == "SET_MODE_NORMAL":
            simulator.mode = "normal"
            print("🕹️  Simulator mode set to NORMAL")
            continue
        elif action == "SET_MODE_GRADUAL":
            simulator.mode = "gradual_drift"
            simulator.drift_factor = 0.0 # reset drift when switching
            print("🕹️  Simulator mode set to GRADUAL DRIFT")
            continue
        elif action == "SET_MODE_SUDDEN":
            simulator.mode = "sudden_fault"
            print("🕹️  Simulator mode set to SUDDEN FAULT")
            continue

        if not machine:
            continue

        if action == "STOP_MACHINE":
            stopped_machines.add(machine)
            print(f"🛑 Producer stopping data for {machine}")

            if stopped_machines == TOTAL_MACHINES:
                print("🛑 ALL MACHINES STOPPED — shutting down producer")
                shutdown = True
                break
        
        elif action == "SCHEDULE_MAINTENANCE":
            stopped_machines.add(machine)
            restart_time = time.time() + MAINTENANCE_DURATION
            maintenance_queue[machine] = restart_time
            print(f"🛠️  Maintenance scheduled for {machine}. Restarting in {MAINTENANCE_DURATION}s")

    consumer.close()


def main():
    producer = Producer(get_producer_config())

    Thread(target=listen_for_actions, daemon=True).start()

    print("🚀 Producer started")

    try:
        while not shutdown:
            # Check maintenance queue
            now = time.time()
            to_restart = [m for m, t in maintenance_queue.items() if now >= t]
            
            for m in to_restart:
                del maintenance_queue[m]
                stopped_machines.discard(m)
                simulator.reset_machine(m)
                
                # Notify maintenance done
                done_event = {
                    "event_id": "MAINTENANCE_DONE",
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                    "machine_id": m,
                    "action": "MAINTENANCE_DONE",
                    "message": f"Maintenance completed for {m}. System restarting..."
                }
                producer.produce(ACTION_TOPIC, json.dumps(done_event).encode("utf-8"))
                print(f"✅ Maintenance done for {m}. Resuming data.")

            event = simulator.next_event()

            if event["machine_id"] in stopped_machines:
                continue  # do not emit stopped machine data
            
            # Emit raw data
            producer.produce(
                RAW_TOPIC,
                json.dumps(event).encode("utf-8")
            )
            producer.poll(0)
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Stopping producer manually")

    finally:
        producer.flush()
        print("✅ Producer exited cleanly")


if __name__ == "__main__":
    main()
