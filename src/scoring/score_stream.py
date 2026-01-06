# src/scoring/score_stream.py
from confluent_kafka import Consumer, Producer
import json, sys, os
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.confluent_client import get_consumer_config, get_producer_config

RAW_TOPIC = "sensor.raw"
SCORE_TOPIC = "sensor.scored"

BASE_TEMP = 60.0
BASE_VIB = 0.02

# 🔁 Stateful risk memory per machine
machine_risk = defaultdict(float)

def score_event(event):
    temp = event["temperature_c"]
    vib = event["vibration_mm_s"]

    instant_score = abs(temp - BASE_TEMP) / 10 + abs(vib - BASE_VIB) * 5
    machine_id = event["machine_id"]

    if instant_score < 0.4:
        instant_score = 0

    # 📈 Accumulate risk slowly
    machine_risk[machine_id] += instant_score * 0.3

    # 🧊 Natural recovery if healthy
    machine_risk[machine_id] *= 0.98

    machine_risk[machine_id] = max(0, min(machine_risk[machine_id], 10))

    risk = machine_risk[machine_id]

    if risk < 1.0:
        status = "NORMAL"
    elif risk < 2.5:
        status = "WARNING"
    elif risk < 4.5:
        status = "CRITICAL"
    else:
        status = "EMERGENCY"

    return round(risk, 3), status, status != "NORMAL"


def main():
    consumer = Consumer(get_consumer_config(group_id="scoring-service"))
    producer = Producer(get_producer_config())

    consumer.subscribe([RAW_TOPIC])
    print("🧠 Scoring service started (stateful)")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None or msg.error():
                continue

            event = json.loads(msg.value().decode("utf-8"))
            
            # get score, status, is_anomaly
            score, status, is_anomaly = score_event(event)

            event.update({
                "anomaly_score": score,
                "status": status,
                "is_anomaly": is_anomaly
            })

            producer.produce(
                SCORE_TOPIC,
                json.dumps(event).encode("utf-8")
            )
            producer.poll(0)

    except KeyboardInterrupt:
        print("Stopping scoring service")
    finally:
        consumer.close()
        producer.flush()


if __name__ == "__main__":
    main()
