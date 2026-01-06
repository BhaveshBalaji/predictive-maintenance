import { useEffect, useState, useCallback } from "react";
import { getMachines, getMachineMetrics, getActions } from "../api/client";
import MachineTable from "../components/MachineTable";
import LineChart from "../components/LineChart";
import AlertsPanel from "../components/AlertsPanel";
import Chatbot from "../components/Chatbot";
import { MachineMetric, MachineStatus, ActionEvent } from "../types/models";

export default function Dashboard() {
  const [machines, setMachines] = useState<MachineStatus[]>([]);
  const [metrics, setMetrics] = useState<MachineMetric[]>([]);
  const [actions, setActions] = useState<ActionEvent[]>([]);
  const [selectedMachineId, setSelectedMachineId] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [machinesData, actionsData] = await Promise.all([
        getMachines(),
        getActions()
      ]);
      setMachines(machinesData);
      setActions(actionsData);

      if (selectedMachineId) {
        const metricsData = await getMachineMetrics(selectedMachineId);
        setMetrics(metricsData);
      } else if (machinesData.length > 0) {
        setSelectedMachineId(machinesData[0].machine_id);
      }
    } catch (error) {
      console.error("Failed to fetch data:", error);
    }
  }, [selectedMachineId]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000); // Refresh every 3 seconds
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleMachineAction = async (id: string, action: string) => {
    try {
      await import("../api/client").then(m => m.postMachineAction(id, action));
      fetchData(); // Refresh immediately
    } catch (error) {
      console.error("Failed to trigger machine action:", error);
    }
  };

  // Expose to window for MachineTable to call (simple way for this demo)
  useEffect(() => {
    (window as any).triggerMachineAction = handleMachineAction;
    return () => { delete (window as any).triggerMachineAction; };
  }, [fetchData]);

  const selectMachine = async (id: string) => {
    setSelectedMachineId(id);
    try {
      const data = await getMachineMetrics(id);
      setMetrics(data);
    } catch (error) {
      console.error("Failed to fetch metrics for machine:", id, error);
    }
  };

  const isSystemShutdown = actions.some(a => a.action === 'SYSTEM_SHUTDOWN');

  return (
    <div className="dashboard-container">
      {isSystemShutdown && (
        <div style={{
          gridColumn: '1 / -1',
          background: 'rgba(255, 77, 79, 0.2)',
          border: '1px solid #ff4d4f',
          borderRadius: '8px',
          padding: '1rem',
          textAlign: 'center',
          color: '#ff4d4f',
          fontWeight: 'bold',
          fontSize: '1.2rem',
          animation: 'pulse 2s infinite',
          marginBottom: '1rem'
        }}>
          🚨 GLOBAL SYSTEM SHUTDOWN DETECTED - ALL OPERATIONS HALTED 🚨
        </div>
      )}
      <header className="header">
        <h1>PREDICTIVE MAINTENANCE DASHBOARD</h1>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <button
            className="btn-action"
            style={{ fontSize: '0.7rem', padding: '0.3rem 0.6rem' }}
            onClick={() => (window as any).triggerMachineAction?.('SYSTEM', 'SET_MODE_NORMAL')}
          >
            Normal Mode
          </button>
          <button
            className="btn-action"
            style={{ fontSize: '0.7rem', padding: '0.3rem 0.6rem', borderColor: '#0044ffff', color: '#0400ffff' }}
            onClick={() => (window as any).triggerMachineAction?.('SYSTEM', 'SET_MODE_GRADUAL')}
          >
            Gradual Drift
          </button>
          <button
            className="btn-action"
            style={{ fontSize: '0.7rem', padding: '0.3rem 0.6rem', borderColor: '#ff4d4f', color: '#ff4d4f' }}
            onClick={() => (window as any).triggerMachineAction?.('SYSTEM', 'SET_MODE_SUDDEN')}
          >
            Sudden Fault
          </button>
          <div style={{ width: '1px', height: '24px', background: 'var(--glass-border)', margin: '0 0.5rem' }} />
          <span className="status-badge status-normal">System Online</span>
          <span style={{ fontSize: '0.8rem', opacity: 0.6 }}>
            Last Update: {new Date().toLocaleTimeString()}
          </span>
        </div>
      </header>

      <main className="main-content">
        <LineChart data={metrics} machineId={selectedMachineId || ""} />
        <MachineTable
          machines={machines}
          onSelect={selectMachine}
          selectedId={selectedMachineId || undefined}
        />
      </main>

      <aside className="sidebar">
        <AlertsPanel actions={actions} />
        <Chatbot />
      </aside>
    </div>
  );
}
