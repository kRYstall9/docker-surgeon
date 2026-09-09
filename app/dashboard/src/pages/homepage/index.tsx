import { Navbar } from "../../components/navbar/navbar";
import { useEffect, useMemo, useState } from "react";
import type {
  CrashedContainerChartStats,
  CrashedContainerLogs,
} from "../../models/crashedContainer";
import {
  getChartStats,
  getCrashedContainersMetrics,
} from "../../api/crashedContainers";
import { Chart } from "../../components/chart/chart";
import { DatePickerForm } from "../../components/datepickerform/datepickerform";
import { formatLocalDate } from "../../utils/utils";
import { LogsViewer } from "../../components/logsViewer/logsviewer";

export function Homepage() {
  const [containerLogs, setContainerLogs] = useState<Record<string, CrashedContainerLogs[]>>({});
  const [chartStats, setChartStats] = useState<Record<string, CrashedContainerChartStats[]>>({});

  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState<{ startDate: Date; endDate: Date }>({startDate: new Date(new Date().setDate(new Date().getDate() - 7)), endDate: new Date()});

  const apiCalls = useMemo(async () => {
    try {
      const [containerLogsRes, statsRes] = await Promise.all([
        getCrashedContainersMetrics(
          formatLocalDate(dateRange.startDate),
          formatLocalDate(dateRange.endDate)
        ),
        getChartStats(
          formatLocalDate(dateRange.startDate),
          formatLocalDate(dateRange.endDate)
        ),
      ]);
      
      if (!Array.isArray(containerLogsRes) || !Array.isArray(statsRes)) {
        console.error("API response is not an array", { containerLogsRes, statsRes });
        return;
      }

      const logsByMachine = containerLogsRes.reduce((acc: Record<string, CrashedContainerLogs[]>, item: CrashedContainerLogs) => {
        if (!acc[item.machine]) {
          acc[item.machine] = [];
        }
        acc[item.machine].push(item);
        return acc;
      }, {} as Record<string, CrashedContainerLogs[]>);

      setContainerLogs(logsByMachine);

      const statsByMachine = statsRes.reduce((acc: Record<string, CrashedContainerChartStats[]>, item: CrashedContainerChartStats) => {
        if (!acc[item.machine]) {
          acc[item.machine] = [];
        }
        acc[item.machine].push(item);
        return acc;
      }, {} as Record<string, CrashedContainerChartStats[]>);

      setChartStats(statsByMachine);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [dateRange]);

  useEffect(() => {
    setLoading(true);
  }, [apiCalls]);

  return (
    <div className="w-[75%] flex flex-col min-h-screen my-5 p-0 gap-10">
      <Navbar />

      <div>
        <DatePickerForm
          dateRange={dateRange}
          setDateRange={setDateRange}
          setLoading={setLoading}
        />
      </div>

      <div className="w-full h-full container-bg-color rounded-xl gap-3 p-4">
        <p className="text-start text-sm sm:text-xl p-3"> Summary </p>
        <div className={`w-full h-[50vh] grid grid-cols-1 ${Object.keys(chartStats).length > 1 ? 'md:grid-cols-2 gap-3' : ''} overflow-y-auto overflow-x-hidden`}>
          {
            Object.keys(chartStats).length > 0 && (
              Object.entries(chartStats).map(([machine, stats]) => {
                return (
                    <Chart key={machine} loading={loading} stats={stats} title={`${machine} Crashed Containers`} />
                )
              })
            )
          }
        </div>
      </div>

      <div className="w-full container-bg-color rounded-xl p-4 text-xs sm:text-sm">
        <div className="col-span-3 text-start text-xl mb-2">
          <p className="text-start text-sm sm:text-xl p-3"> Crash History </p>
        </div> 
        <LogsViewer logs={containerLogs} />
      </div>
    </div>
  );
}
