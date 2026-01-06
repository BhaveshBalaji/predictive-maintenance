# src/actions/action_engine.py
from confluent_kafka import Consumer, Producer
import json, sys, os, datetime
from collections import defaultdict
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.confluent_client import get_consumer_config, get_producer_config

SCORED_TOPIC = "sensor.scored"
ACTION_TOPIC = "sensor.actions"

# 🏭 All machines in the plant (demo scale)
ALL_MACHINES = {f"mach-{i:02d}" for i in range(1, 11)}

# ⏱️ Track how long a machine stays unhealthy
machine_status_counter = defaultdict(int)

# 🛑 Track machines that are already stopped
stopped_machines = set()

# 🧨 Ensure SYSTEM_SHUTDOWN is emitted only once
system_shutdown_emitted = False

# Track when a machine entered a non-normal state
machine_status_since = {}

# 🔗 Dependency graph (demo)
DEPENDENCIES = {
    "mach-07": ["mach-02", "mach-05"],
    "mach-02": ["mach-08"]
}

# 📝 Track last action emitted per machine to avoid duplicates
last_action_per_machine = {}

def decide_action(event):
    status = event["status"]
    machine = event["machine_id"]
    now = datetime.now(timezone.utc)

    # Reset when healthy
    if status == "NORMAL":
        machine_status_since.pop(machine, None)
        last_action_per_machine.pop(machine, None)
        return None

    # Logic for unhealthy states
    if status == "WARNING":
        action = "NOTIFY_WARNING"
    elif status == "CRITICAL":
        action = "STOP_MACHINE|SCHEDULE_MAINTENANCE" # Composite action to be handled
    elif status == "EMERGENCY":
        action = "STOP_MACHINE"
    else:
        return None

    # Only return action if it's different from the last one emitted
    if action and last_action_per_machine.get(machine) != action:
        return action

    return None

    return None

def emit_action(producer, base_event, machine_id, action, message):
    """
    Emit a single action event to Kafka
    """
    action_event = {
        "event_id": base_event.get("event_id", "system"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "machine_id": machine_id,
        "component_id": base_event.get("component_id"),
        "status": base_event.get("status"),
        "anomaly_score": base_event.get("anomaly_score"),
        "action": action,
        "message": message
    }

    producer.produce(
        ACTION_TOPIC,
        json.dumps(action_event).encode("utf-8")
    )

    print(f"🚨 {action} → {machine_id}")


def emit_system_shutdown(producer):
    """
    Emit a global system-level shutdown event
    """
    global system_shutdown_emitted

    if system_shutdown_emitted:
        return

    shutdown_event = {
        "event_id": "SYSTEM",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "SYSTEM_SHUTDOWN",
        "message": "All machines halted due to cascading failures"
    }

    producer.produce(
        ACTION_TOPIC,
        json.dumps(shutdown_event).encode("utf-8")
    )

    system_shutdown_emitted = True
    print("🛑 SYSTEM_SHUTDOWN → ALL MACHINES HALTED")


def main():
    consumer = Consumer(get_consumer_config(group_id="action-engine"))
    producer = Producer(get_producer_config())

    consumer.subscribe([SCORED_TOPIC, ACTION_TOPIC])
    print("Gear Action Engine started (monitoring scores and actions)")

    # Emit startup alert
    startup_event = {
        "event_id": "SYSTEM_START",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "machine_id": "SYSTEM",
        "action": "SYSTEM_ONLINE",
        "message": "Predictive Maintenance Action Engine is now monitoring assets."
    }
    producer.produce(ACTION_TOPIC, json.dumps(startup_event).encode("utf-8"))
    producer.flush()

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None or msg.error():
                continue

            event = json.loads(msg.value().decode("utf-8"))
            topic = msg.topic()

            # Handle global maintenance completion
            if topic == ACTION_TOPIC:
                if event.get("action") == "MAINTENANCE_DONE":
                    machine = event.get("machine_id")
                    if machine in stopped_machines:
                        stopped_machines.discard(machine)
                        print(f"🔄 Action Engine: Machine {machine} is back online.")
                continue

            # Only process SCORED_TOPIC from here on
            if topic != SCORED_TOPIC:
                continue

            machine = event["machine_id"]

            # Skip already stopped machines
            if machine in stopped_machines:
                continue

            action_raw = decide_action(event)
            if not action_raw:
                continue

            # Split predictive message if present
            # Handle composite actions (e.g., STOP + SCHEDULE)
            actions_to_emit = []
            if "|" in action_raw and "STOP_MACHINE" in action_raw:
                parts = action_raw.split("|")
                for p in parts:
                    actions_to_emit.append((p, f"{p} triggered automatically due to {event['status']} state"))
            else:
                actions_to_emit.append((action_raw, f"{action_raw} triggered for {machine}"))

            for action, message in actions_to_emit:
                # Update last action (track the raw string to avoid loops)
                last_action_per_machine[machine] = action_raw

                # Emit primary action
                emit_action(
                    producer,
                    event,
                    machine,
                    action,
                    message
                )

                # Handle STOP logic
                if action == "STOP_MACHINE":
                    stopped_machines.add(machine)

                    # Cascading stops
                    for dep in DEPENDENCIES.get(machine, []):
                        if dep not in stopped_machines:
                            stopped_machines.add(dep)
                            emit_action(
                                producer,
                                event,
                                dep,
                                "STOP_MACHINE",
                                f"Automatic shutdown: dependent machine {machine} is in {event['status']} state"
                            )

            # 🔥 Check global shutdown condition
            if stopped_machines == ALL_MACHINES:
                emit_system_shutdown(producer)

            producer.poll(0)

    except KeyboardInterrupt:
        print("Stopping Action Engine")
    finally:
        consumer.close()
        producer.flush()


if __name__ == "__main__":
    main()
