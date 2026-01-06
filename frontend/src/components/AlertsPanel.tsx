import { ActionEvent } from "../types/models";

export default function AlertsPanel({ actions }: { actions: ActionEvent[] }) {
  const getAlertClass = (action: string) => {
    const a = action.toLowerCase();
    if (a.includes('shutdown') || a.includes('stop')) return 'critical';
    if (a.includes('maintenance') || a.includes('critical')) return 'warning';
    return '';
  };

  // Deduplicate: only show the latest unique message for each machine
  const uniqueActions = actions.reduce((acc: ActionEvent[], current) => {
    const existingIndex = acc.findIndex(
      a => a.machine_id === current.machine_id && a.action === current.action
    );
    if (existingIndex > -1) {
      acc[existingIndex] = current; // Update with latest
    } else {
      acc.push(current);
    }
    return acc;
  }, []);

  return (
    <div className="card">
      <h3>🔔 System Alerts</h3>
      <div className="alerts-list">
        {uniqueActions.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '1rem' }}>
            No active alerts
          </div>
        ) : (
          [...uniqueActions].reverse().map((a, i) => (
            <div
              key={i}
              className={`alert-item ${getAlertClass(a.action)}`}
              style={a.action.includes('SHUTDOWN') ? {
                background: 'rgba(255, 77, 79, 0.15)',
                borderLeft: '4px solid #ff4d4f',
                animation: 'pulse 2s infinite'
              } : {}}
            >
              <strong style={{ display: 'flex', justifyContent: 'space-between' }}>
                {a.action.replace(/_/g, ' ')}
                {a.action.includes('STOP') && <span>🛑</span>}
                {a.action.includes('SHUTDOWN') && <span>⚠️</span>}
              </strong>
              <small>{a.machine_id !== 'SYSTEM' ? `${a.machine_id} • ` : ''}{a.message}</small>
              <div style={{ fontSize: '0.7rem', marginTop: '0.25rem', opacity: 0.6 }}>
                {new Date(a.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
