# src/actions/action_engine.py
from confluent_kafka import Consumer, Producer
import json, sys, os, datetime
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.confluent_client import get_consumer_config, get_producer_config

SCORED_TOPIC = "sensor.scored"
ACTION_TOPIC = "sensor.actions"

# ⏱️ How long machines remain unhealthy
machine_status_counter = defaultdict(int)

# 🏭 Simple dependency map (demo)
DEPENDENCIES = {
    "mach-07": ["mach-02", "mach-05"],
    "mach-02": ["mach-08"]
}

def decide_action(event):
    status = event["status"]
    machine_id = event["machine_id"]

    if status == "NORMAL":
        machine_status_counter[machine_id] = 0
        return None

    machine_status_counter[machine_id] += 1

    if status == "WARNING" and machine_status_counter[machine_id] >= 3:
        return "NOTIFY"

    if status == "CRITICAL" and machine_status_counter[machine_id] >= 5:
        return "SCHEDULE_MAINTENANCE"

    if status == "EMERGENCY":
        return "STOP_MACHINE"

    return None


def main():
    consumer = Consumer(get_consumer_config(group_id="action-engine"))
    producer = Producer(get_producer_config())

    consumer.subscribe([SCORED_TOPIC])
    print("⚙️ Action Engine started (stateful)")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None or msg.error():
                continue

            event = json.loads(msg.value().decode("utf-8"))
            action = decide_action(event)

            if not action:
                continue

            action_event = {
                "event_id": event["event_id"],
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "machine_id": event["machine_id"],
                "component_id": event["component_id"],
                "status": event["status"],
                "anomaly_score": event["anomaly_score"],
                "action": action,
                "message": f"{action} triggered for {event['machine_id']}"
            }

            producer.produce(ACTION_TOPIC, json.dumps(action_event).encode("utf-8"))
            producer.poll(0)

            print(f"🚨 {action} → {event['machine_id']}")

            # 🔥 Cascading impact
            if action == "STOP_MACHINE":
                for dep in DEPENDENCIES.get(event["machine_id"], []):
                    cascade_event = action_event.copy()
                    cascade_event["machine_id"] = dep
                    cascade_event["action"] = "STOP_MACHINE"
                    cascade_event["message"] = f"Stopped due to dependency on {event['machine_id']}"

                    producer.produce(
                        ACTION_TOPIC,
                        json.dumps(cascade_event).encode("utf-8")
                    )
                    print(f"⚠️ CASCADE STOP → {dep}")

    except KeyboardInterrupt:
        print("Stopping Action Engine")
    finally:
        consumer.close()
        producer.flush()


if __name__ == "__main__":
    main()
