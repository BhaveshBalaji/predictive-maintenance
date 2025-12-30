# src/producer/consumer.py
from confluent_kafka import Consumer
import json
import sys
import os

# Fix Python path so utils can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.confluent_client import get_consumer_config

cfg = get_consumer_config()
c = Consumer(cfg)
topic = "sensor.raw"
c.subscribe([topic])

try:
    while True:
        msg = c.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("Error:", msg.error())
            continue
        try:
            val = msg.value().decode("utf-8")
        except:
            val = msg.value()
        print("MSG:", val)
except KeyboardInterrupt:
    print("Stopping")
finally:
    c.close()
