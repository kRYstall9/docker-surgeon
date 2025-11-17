import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import type { CrashedContainerChartStats } from "../../models/crashedContainer";
import { Spinner } from "../spinner/spinner";

interface ChartProps {
  loading: boolean;
  stats: CrashedContainerChartStats[];
}

export function Chart({ loading, stats }: ChartProps) {
  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    BarElement,
    Title,
    Tooltip,
    Legend
  );

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top" as const,
      },
      title: {
        display: true,
        text: "Crashed Containers Chart",
      },
    },
  };

  const safeStats = Array.isArray(stats) ? stats : [];

  const labels = Array.from(
    new Set(
      safeStats.map(
        (s: CrashedContainerChartStats) =>
          new Date(s.crashed_on!).toISOString().split("T")[0]
      )
    )
  )
    .sort(
      (a: string, b: string) => new Date(a).getTime() - new Date(b).getTime()
    )
    .map((dateStr: string) => new Date(dateStr).toISOString().split("T")[0]);

  const containers = Array.from(
    new Set(safeStats.map((s: CrashedContainerChartStats) => s.container_name))
  );

  const datasets = containers.map((name) => {
    return {
      label: name,
      backgroundColor: `hsl(${Math.random() * 360}, 70%, 60%)`,
      data: labels.map((date) => {
        const stat = safeStats.find(
          (s: CrashedContainerChartStats) =>
            s.crashed_on === date && s.container_name === name
        );
        return stat ? stat.crash_count : 0;
      }),
    };
  });

  const data = {
    labels,
    datasets: datasets,
  };

  return (
    <div className="h-[calc(100%-4rem)] flex justify-center items-center">
      {loading && <Spinner/>}
      {!loading && <Bar options={options} data={data}/>}
    </div>
  );
}
