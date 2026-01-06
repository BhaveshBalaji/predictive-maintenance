from confluent_kafka import Consumer, Producer
import json
import threading
from datetime import datetime
from collections import defaultdict, deque
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.confluent_client import get_consumer_config, get_producer_config

# =========================
# In-memory state (API reads from this)
# =========================

machine_metrics = defaultdict(lambda: deque(maxlen=100))
machine_status = {}
action_events = deque(maxlen=200)

# Global producer for manual actions
api_producer = None

# =========================
# Helpers
# =========================

def parse_ts(ts: str):
    return datetime.fromisoformat(ts.replace("Z", "")) if ts else datetime.utcnow()

# =========================
# Consumers
# =========================

def consume_scored_events():
    consumer = Consumer(get_consumer_config(group_id="api-scoring"))
    consumer.subscribe(["sensor.scored"])
    print("📥 API consumer listening to sensor.scored")

    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue

        event = json.loads(msg.value().decode("utf-8"))
        machine_id = event.get("machine_id")

        if not machine_id:
            continue  # ignore malformed events

        metric = {
            "timestamp": parse_ts(event.get("timestamp")),
            "temperature_c": event.get("temperature_c"),
            "vibration_mm_s": event.get("vibration_mm_s"),
            "rpm": event.get("rpm"),
            "anomaly_score": event.get("anomaly_score", 0.0),
            "status": event.get("status", "UNKNOWN")
        }

        machine_metrics[machine_id].append(metric)

        machine_status[machine_id] = {
            "machine_id": machine_id,
            "status": metric["status"],
            "anomaly_score": metric["anomaly_score"],
            "last_updated": metric["timestamp"]
        }


def consume_action_events():
    consumer = Consumer(get_consumer_config(group_id="api-actions"))
    consumer.subscribe(["sensor.actions"])
    print("📥 API consumer listening to sensor.actions")

    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue

        event = json.loads(msg.value().decode("utf-8"))

        action_events.append({
            "timestamp": parse_ts(event.get("timestamp")),
            "machine_id": event.get("machine_id"),
            "action": event.get("action"),
            "message": event.get("message")
        })

        # Dynamically update machine status based on actions
        machine_id = event.get("machine_id")
        action = event.get("action")
        if machine_id and machine_id != "SYSTEM":
            current_status = machine_status.get(machine_id, {"anomaly_score": 0.0})
            
            new_status_label = None
            if action == "STOP_MACHINE":
                new_status_label = "STOPPED"
            elif action == "SCHEDULE_MAINTENANCE":
                new_status_label = "Automatically Shutdown - Scheduled maintenance"
            elif action == "MAINTENANCE_DONE":
                new_status_label = "NORMAL"
            
            if new_status_label:
                machine_status[machine_id] = {
                    "machine_id": machine_id,
                    "status": new_status_label,
                    "anomaly_score": current_status.get("anomaly_score", 0.0),
                    "last_updated": parse_ts(event.get("timestamp"))
                }


def start_consumers():
    global api_producer
    api_producer = Producer(get_producer_config())
    
    threading.Thread(target=consume_scored_events, daemon=True).start()
    threading.Thread(target=consume_action_events, daemon=True).start()

def produce_action(machine_id: str, action: str, message: str):
    if not api_producer:
        return
        
    event = {
        "event_id": "manual",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "machine_id": machine_id,
        "action": action,
        "message": message
    }
    
    api_producer.produce(
        "sensor.actions",
        json.dumps(event).encode("utf-8")
    )
    api_producer.flush()
