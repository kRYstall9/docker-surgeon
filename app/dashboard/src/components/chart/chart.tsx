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
  type ChartOptions,
} from "chart.js";
import type { CrashedContainerChartStats } from "../../models/crashedContainer";
import { Spinner } from "../spinner/spinner";

interface ChartProps {
  loading: boolean;
  stats: CrashedContainerChartStats[];
  title: string;
}

export function Chart({ loading, stats, title }: ChartProps) {
  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    BarElement,
    Title,
    Tooltip,
    Legend
  );

  const options:ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    resizeDelay: 250,
    scales: {
      y: {
        beforeSetDimensions: (axis) => {
          axis.chart.options.scales!.y!.max = Math.max(0, ...safeStats.map((s) => s.crash_count)) + 10;
        }
      }
    },
    plugins: {
      legend: {
        position: "top" as const,
      },
      title: {
        display: true,
        text: title,
        font: {
          size: 16
        }
      },
    },
  };

  const safeStats = Array.isArray(stats) ? stats : [];

  const labels = Array.from(
    new Set(
      safeStats.map(
        (s: CrashedContainerChartStats) =>
          new Date(s.crashed_on!).toLocaleDateString()
      )
    )
  )
    .sort(
      (a: string, b: string) => new Date(a).getTime() - new Date(b).getTime()
    )
    .map((dateStr: string) => dateStr);

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
            new Date(s.crashed_on!).toLocaleDateString() === new Date(date).toLocaleDateString() && s.container_name === name
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
    <div className="h-full flex justify-center items-center border border-gray-700 rounded-xl">
      {loading && <Spinner/>}
      {!loading && <Bar options={options} data={data} />}
    </div>
  );
}
