from fastapi import FastAPI
from typing import List
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from .kafka_consumer import (
    start_consumers,
    machine_metrics,
    machine_status,
    action_events,
    produce_action
)
from .models import MachineMetric, MachineStatus, ActionEvent

# What is lifespan doing? - ANS: It is a context manager that is called when the application starts and stops. It is used to start and stop the Kafka consumers.
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Kafka consumers for API")
    start_consumers()
    yield


app = FastAPI(
    title="Predictive Maintenance API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GET endpoint that returns the list of all machines.
@app.get("/machines", response_model=List[MachineStatus])
def get_machine_status():
    return list(machine_status.values())

# GET endpoint that returns the list of metrics for a specific machine.
@app.get("/machines/{machine_id}/metrics", response_model=List[MachineMetric])
def get_machine_metrics(machine_id: str):
    return list(machine_metrics.get(machine_id, []))

# GET endpoint that returns the list of actions.
@app.get("/actions", response_model=List[ActionEvent])
def get_actions():
    return list(action_events)

# POST endpoint that triggers an action for a specific machine.
@app.post("/machines/{machine_id}/action")
def post_machine_action(machine_id: str, action: str):
    message = f"Manual {action} triggered for {machine_id}"
    produce_action(machine_id, action, message)
    return {"status": "success", "message": message}

# GET endpoint that returns the health of the API.
@app.get("/")
def health():
    return {
        "status": "running",
        "machines_tracked": len(machine_status),
        "actions_logged": len(action_events)
    }
