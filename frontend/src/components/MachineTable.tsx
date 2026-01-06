import { MachineStatus } from "../types/models";

interface MachineTableProps {
  machines: MachineStatus[];
  onSelect: (id: string) => void;
  selectedId?: string;
}

export default function MachineTable({
  machines,
  onSelect,
  selectedId
}: MachineTableProps) {
  return (
    <div className="card">
      <h3>🔌 Connected Assets</h3>
      <table className="machine-table">
        <thead>
          <tr>
            <th>Machine ID</th>
            <th>Status</th>
            <th>Anomaly Score</th>
            <th>Last Updated</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {machines.map((m) => (
            <tr
              key={m.machine_id}
              onClick={() => onSelect(m.machine_id)}
              style={{
                background: selectedId === m.machine_id ? 'rgba(0, 242, 234, 0.1)' : 'transparent',
                borderLeft: selectedId === m.machine_id ? '4px solid var(--teal-primary)' : 'none',
                cursor: 'pointer'
              }}
            >
              <td>{m.machine_id}</td>
              <td>
                <span className={`status-badge status-${m.status.toLowerCase().replace(/[^a-z0-9]/g, '-')}`}>
                  {m.status}
                </span>
              </td>
              <td style={{ color: m.anomaly_score > 0.7 ? '#ff4d4f' : 'inherit' }}>
                {(m.anomaly_score * 100).toFixed(1)}%
              </td>
              <td>{new Date(m.last_updated).toLocaleTimeString()}</td>
              <td onClick={(e) => e.stopPropagation()}>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    className="btn-action"
                    style={{ whiteSpace: 'nowrap', fontSize: '0.75rem', padding: '0.4rem 0.8rem' }}
                    onClick={() => {
                      (window as any).triggerMachineAction?.(m.machine_id, 'SCHEDULE_MAINTENANCE');
                    }}
                    title="Schedule Maintenance"
                    disabled={m.status === 'STOPPED'}
                  >
                    Schedule Maintenance
                  </button>
                  <button
                    className="btn-action"
                    style={{
                      whiteSpace: 'nowrap',
                      fontSize: '0.75rem',
                      padding: '0.4rem 0.8rem',
                      borderColor: '#ff4d4f',
                      color: '#ff4d4f'
                    }}
                    onClick={() => {
                      (window as any).triggerMachineAction?.(m.machine_id, 'STOP_MACHINE');
                    }}
                    title="Emergency Shutdown"
                    disabled={m.status === 'STOPPED'}
                  >
                    Shutdown
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
