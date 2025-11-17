import { Navbar } from "../../components/navbar/navbar";
import { useCallback, useEffect, useState } from "react";
import type {
  CrashedContainerChartStats,
  CrashedContainerLogs,
} from "../../models/crashedContainer";
import {
  getChartStats,
  getCrashedContainersMetrics,
} from "../../api/crashedContainers";
import { Chart } from "../../components/chart/chart";
import { Spinner } from "../../components/spinner/spinner";
import { DatePickerForm } from "../../components/datepickerform/datepickerform";
import { formatLocalDate } from "../../utils/utils";

export function Homepage() {
  const [containerLogs, setContainerLogs] = useState<CrashedContainerLogs[]>([]);
  const [chartStats, setChartStats] = useState<CrashedContainerChartStats[]>(
    []
  );
  const [selectedContainer, setSelectedContainer] = useState<string | null>(
    null
  );
  const [loading, setLoading] = useState(true);

  const today = new Date();
  const weekEarlier = new Date();
  weekEarlier.setDate(today.getDate() - 7);

  const apiCalls = useCallback(async () => {
    try {
      const [containerLogsRes, statsRes] = await Promise.all([
        getCrashedContainersMetrics(
          formatLocalDate(weekEarlier),
          formatLocalDate(today)
        ),
        getChartStats(
          formatLocalDate(weekEarlier),
          formatLocalDate(today)
        ),
      ]);

      setContainerLogs(containerLogsRes);
      setChartStats(statsRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    apiCalls();
  }, [apiCalls]);

  const buildLogsSection = () => {
    if (!Array.isArray(containerLogs)) return [];

    const uniqueCrashedContainers = Object.values(
      containerLogs.reduce(
        (
          acc: Record<string, CrashedContainerLogs>,
          item: CrashedContainerLogs
        ) => {
          if (!acc[item.container_name]) {
            acc[item.container_name] = { ...item };
          } else {
            acc[item.container_name].logs += `\n\n${item.logs}`;
          }

          return acc;
        },
        {} as Record<string, CrashedContainerLogs>
      )
    );

    return uniqueCrashedContainers;
  };

  const uniqueCrashedContainers = buildLogsSection();
  const selected = uniqueCrashedContainers.find(
    (x: CrashedContainerLogs) => x.container_id === selectedContainer
  );

  return (
    <div className="w-[75%] flex flex-col min-h-screen my-5 p-0 gap-10">
      <Navbar />

      <div>
        <DatePickerForm
          initialStartDate={weekEarlier}
          initialEndDate={today}
          setChartStats={setChartStats}
          setLoading={setLoading}
          setContainerLogs={setContainerLogs}
        />
      </div>

      <div className="w-full h-[50vh] container-bg-color rounded-xl p-4">
        <p className="text-start text-sm sm:text-xl p-3"> Summary </p>
        <Chart loading={loading} stats={chartStats} />
      </div>

      <div className="w-full grid grid-cols-3 gap-4 container-bg-color rounded-xl p-4 text-xs sm:text-sm">
        <div className="col-span-3 text-start text-xl mb-2">
          <p className="text-start text-sm sm:text-xl p-3"> Crash History </p>
        </div>

        <div className="col-span-1 flex justify-center items-start">
          <div
            className={`w-full sm:w-[80%]  h-[50vh] flex flex-col gap-3 p-2 sm:p-4 rounded-md sm:rounded-xl overflow-x-auto overflow-y-auto bg-[#242424] ${
              loading ? "justify-center items-center" : ""
            }`}
          >
            {loading ? (
              <Spinner />
            ) : (
              uniqueCrashedContainers.map((cont: CrashedContainerLogs) => {
                return (
                  <button
                    key={cont.container_id}
                    onClick={() => setSelectedContainer(cont.container_id)}
                    className="w-full bg-gray-600 hover:bg-gray-700 sm:py-2 rounded-md text-white cursor-pointer"
                  >
                    {cont.container_name}
                  </button>
                );
              })
            )}
          </div>
        </div>

        <div
          className={`col-span-2 text-start p-5 h-[50vh] overflow-y-auto rounded-md sm:rounded-xl bg-[#242424] whitespace-pre-wrap ${
            loading ? "flex justify-center items-center" : ""
          }`}
        >
          {loading && <Spinner />}
          {!loading && selectedContainer && selected && <p>{selected.logs}</p>}
          {!loading &&
            (!selectedContainer || !selected) &&
            containerLogs.length > 0 && <p>Select a container to view logs...</p>}
        </div>
      </div>
    </div>
  );
}
