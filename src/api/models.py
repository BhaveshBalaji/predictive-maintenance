from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# It is a Pydantic model that represents a machine metric.
class MachineMetric(BaseModel):
    timestamp: datetime
    temperature_c: float
    vibration_mm_s: float
    rpm: int
    anomaly_score: Optional[float] = None
    status: Optional[str] = None

# It is a Pydantic model that represents a machine status.
class MachineStatus(BaseModel):
    machine_id: str
    status: str
    last_updated: datetime
    anomaly_score: float

# It is a Pydantic model that represents an action event.
class ActionEvent(BaseModel):
    timestamp: datetime
    machine_id: str
    action: str
    message: str
