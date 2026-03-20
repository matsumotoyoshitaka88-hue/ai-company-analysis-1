import { TrafficLight } from "./TrafficLight";

interface Metric {
  name: string;
  value: string;
  benchmark: string;
  score: number;
}

interface Props {
  title: string;
  data: {
    score: number;
    traffic_light: string;
    metrics: Metric[];
  };
}

export function FinancialMetrics({ title, data }: Props) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-3 mb-3">
        <TrafficLight color={data.traffic_light} size="sm" />
        <h4 className="font-bold text-lg">{title}</h4>
        <span className="text-[var(--color-text-secondary)]">
          {data.score}/100
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="py-2 pr-4 font-medium text-[var(--color-text-secondary)] text-sm">
                指標
              </th>
              <th className="py-2 pr-4 font-medium text-[var(--color-text-secondary)] text-sm">
                実績値
              </th>
              <th className="py-2 pr-4 font-medium text-[var(--color-text-secondary)] text-sm">
                業界平均
              </th>
              <th className="py-2 font-medium text-[var(--color-text-secondary)] text-sm">
                スコア
              </th>
            </tr>
          </thead>
          <tbody>
            {data.metrics.map((m) => (
              <tr key={m.name} className="border-b border-gray-100">
                <td className="py-3 pr-4 font-medium">{m.name}</td>
                <td className="py-3 pr-4">{m.value}</td>
                <td className="py-3 pr-4 text-[var(--color-text-secondary)]">
                  {m.benchmark}
                </td>
                <td className="py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          m.score >= 70
                            ? "bg-green-500"
                            : m.score >= 40
                              ? "bg-yellow-400"
                              : "bg-red-500"
                        }`}
                        style={{ width: `${m.score}%` }}
                      />
                    </div>
                    <span className="text-sm">{m.score}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
