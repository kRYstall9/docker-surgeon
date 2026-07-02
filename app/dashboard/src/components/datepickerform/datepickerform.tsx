import { useState } from "react";
import { DatePicker } from "../datepicker/datepicker";

interface DatePickerFormProps {
  setLoading: (loading: boolean) => void;
  setDateRange: (dateRange: { startDate: Date ; endDate: Date }) => void;
  dateRange: { startDate: Date; endDate: Date };
}

export function DatePickerForm({
  setLoading,
  dateRange,
  setDateRange,
}: DatePickerFormProps) {
  const [error, setError] = useState<string | null>(null);

  function onDateChange(date: Date, isStartDate: boolean){
    date.setHours(0, 0, 0, 0); // Normalize time to midnight for comparison

    if(isStartDate && date > dateRange.endDate){
      setError("Start date cannot be after end date.");
      return;
    }
    if(!isStartDate && date < dateRange.startDate){
      setError("End date cannot be before start date.");
      return;
    }
    setError(null);
    setLoading(true);
    setDateRange(isStartDate ? { ...dateRange, startDate: date } : { ...dateRange, endDate: date });
  }

  return (
    <div>
      <div className="flex flex-col sm:flex-row gap-5 justify-center items-center">
        <DatePicker
          value={dateRange.startDate}
          onChange={(date) => onDateChange(date, true)}
          label="Start Date"
        />
        <DatePicker 
          value={dateRange.endDate} 
          onChange={(date) => onDateChange(date, false)} 
          label="End Date" 
        />

      </div>
      {error && (
        <div className="text-center mt-2">
          <p className="text-red-500 text-sm font-medium">{error}</p>
        </div>
      )}
    </div>
  );
}
