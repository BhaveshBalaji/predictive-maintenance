import {
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Area,
  AreaChart
} from "recharts";
import { MachineMetric } from "../types/models";

export default function LineChart({ data }: { data: MachineMetric[] }) {
  return (
    <div className="card" style={{ height: '400px' }}>
      <h3>📈 Real-time Telemetry</h3>
      <ResponsiveContainer width="100%" height="90%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorAnomaly" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00f2ea" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#00f2ea" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis
            dataKey="timestamp"
            hide
          />
          <YAxis
            stroke="#a0a0a0"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            domain={[0, 1]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a1a1a',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              color: '#fff'
            }}
            itemStyle={{ color: '#00f2ea' }}
            labelFormatter={(label) => new Date(label).toLocaleTimeString()}
          />
          <Area
            type="monotone"
            dataKey="anomaly_score"
            stroke="#00f2ea"
            strokeWidth={3}
            fillOpacity={1}
            fill="url(#colorAnomaly)"
            animationDuration={500}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
