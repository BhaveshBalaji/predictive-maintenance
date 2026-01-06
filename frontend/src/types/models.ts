export interface MachineStatus {
  machine_id: string;
  status: string;
  anomaly_score: number;
  last_updated: string;
}

export interface MachineMetric {
  timestamp: string;
  temperature_c: number;
  vibration_mm_s: number;
  rpm: number;
  anomaly_score: number;
  status: string;
}

export interface ActionEvent {
  timestamp: string;
  machine_id: string;
  action: string;
  message: string;
}
