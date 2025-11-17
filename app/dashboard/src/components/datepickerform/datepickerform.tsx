import { useState } from "react";
import { DatePicker } from "../datepicker/datepicker";
import {
  getChartStats,
  getCrashedContainersMetrics,
} from "../../api/crashedContainers";
import type {
  CrashedContainerChartStats,
  CrashedContainerLogs,
} from "../../models/crashedContainer";
import { formatLocalDate } from "../../utils/utils";

interface DatePickerFormProps {
  setContainerLogs: (containerLogs: CrashedContainerLogs[]) => void;
  setChartStats: (stats: CrashedContainerChartStats[]) => void;
  setLoading: (loading: boolean) => void;
  initialStartDate: Date;
  initialEndDate: Date;
}

export function DatePickerForm({
  setContainerLogs,
  setChartStats,
  setLoading,
  initialStartDate,
  initialEndDate,
}: DatePickerFormProps) {
  const [startDate, setStartDate] = useState<Date | null>(initialStartDate);
  const [endDate, setEndDate] = useState<Date | null>(initialEndDate);
  const [error, setError] = useState<string | null>(null);

  const apiCalls = async () => {
    try {
      setLoading(true);
      const [containerLogsRes, statsRes] = await Promise.all([
        getCrashedContainersMetrics(
          formatLocalDate(startDate!),
          formatLocalDate(endDate!)
        ),
        getChartStats(
          formatLocalDate(startDate!),
          formatLocalDate(endDate!)
        ),
      ]);

      setContainerLogs(containerLogsRes);
      setChartStats(statsRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if(!startDate || !endDate){
      setError("Please select both dates");
      return;
    }
    const start = new Date(startDate);
    const end = new Date(endDate);
    start.setHours(0,0,0,0);
    end.setHours(0,0,0,0);

    if (start > end) {
      setError("Start date cannot be later than end date");
      return;
    }

    await apiCalls();
  }

  return (
    <div>
      <div className="flex flex-col sm:flex-row gap-5 justify-center items-center">
        <DatePicker
          value={startDate}
          onChange={setStartDate}
          label="Start Date"
        />
        <DatePicker value={endDate} onChange={setEndDate} label="End Date" />
        <button
          onClick={handleSubmit}
          className="bg-orange-700 text-white px-4 py-2 rounded-md border border-gray-700 hover:bg-orange-500 cursor-pointer"
        >
          Submit
        </button>
      </div>
      {error && (
        <div className="text-center mt-2">
          <p className="text-red-500 text-sm font-medium">{error}</p>
        </div>
      )}
    </div>
  );
}
