from confluent_kafka import Producer
import json
import time
import sys
import os

# Fix Python path so utils can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.confluent_client import get_producer_config
from data_simulator import Simulator

TOPIC = "sensor.raw"

def delivery_report(err, msg):
    if err is not None:
        print("❌ Delivery failed:", err)
    else:
        pass
        # Uncomment if you want verbose logging
        # print(f"✅ Delivered to {msg.topic()} [{msg.partition()}]")

def main():
    producer = Producer(get_producer_config())
    simulator = Simulator(mode="normal")  # later: "drift"

    print("🚀 Starting sensor data producer...")

    try:
        while True:
            event = simulator.next_event()
            producer.produce(
                TOPIC,
                value=json.dumps(event).encode("utf-8"),
                callback=delivery_report
            )
            producer.poll(0)
            time.sleep(0.05)  # ~20 events/sec
    except KeyboardInterrupt:
        print("\n🛑 Stopping producer...")
    finally:
        producer.flush()

if __name__ == "__main__":
    main()
