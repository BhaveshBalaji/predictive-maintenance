# src/utils/confluent_client.py
import os

def read_config_from_envfile(path=".env"):
    """
    Reads key=value lines from .env (or client.properties style) and returns a dict
    Skips comments and blank lines.
    """
    config = {}
    with open(path, "r") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            config[k.strip()] = v.strip()
    return config

def get_producer_config(envfile_path=".env"):
    cfg = read_config_from_envfile(envfile_path)
    # confluent_kafka expects a dict with keys like 'bootstrap.servers', 'sasl.username', etc.
    return cfg.copy()

def get_consumer_config(envfile_path=".env", group_id="python-group-1"):
    cfg = read_config_from_envfile(envfile_path)
    cfg["group.id"] = group_id
    cfg["auto.offset.reset"] = "earliest"
    return cfg.copy()
