import { useEffect, useRef, useState } from "react";

interface DatePickerProps {
  value: Date | null;
  onChange: (date: Date | null) => void;
  label: string;
}

export function DatePicker({ value, onChange, label }: DatePickerProps) {
  const [open, setOpen] = useState(false);
  const calendarRef = useRef<HTMLDivElement>(null);

  const [month, setMonth] = useState(value!.getMonth());
  const [year, setYear] = useState(value!.getFullYear());

  useEffect(() => {
    if (!open) return;

    function handleClickOutside(e: MouseEvent) {
      if (
        calendarRef.current &&
        !calendarRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [open]);

  function getDaysInMonth(year: number, month: number) {
    return new Date(year, month + 1, 0).getDate();
  }

  function getWeekday(year: number, month: number) {
    return new Date(year, month, 1).getDay(); // 0 = Sunday
  }

  function setToday() {
    const today = new Date();
    onChange(today);
    setMonth(today.getMonth());
    setYear(today.getFullYear());
  }

  const daysInMonth = getDaysInMonth(year, month);
  const firstWeekday = getWeekday(year, month);

  function handleSelect(day: number) {
    const newDate = new Date(year, month, day);
    onChange(newDate);
    setOpen(false);
  }

  function prevMonth() {
    if (month === 0) {
      setMonth(11);
      setYear((y) => y - 1);
    } else setMonth((m) => m - 1);
  }

  function nextMonth() {
    if (month === 11) {
      setMonth(0);
      setYear((y) => y + 1);
    } else setMonth((m) => m + 1);
  }

  return (
    <div className="relative inline-block">
      <div className="relative inline-block">
        <label className="absolute -top-1 left-2 bg-transparent text-[0.6rem] uppercase tracking-wide text-gray-300">
          {label}
        </label>
        <button
          onClick={() => setOpen((prev) => !prev)}
          className={`bg-[var(--homepage-bg-color)] text-white px-4 py-2 rounded-md border border-gray-700 hover:bg-gray-700 cursor-pointer`}
        >
          {value ? value.toLocaleDateString() : "Select date"}
        </button>
      </div>

      {open && (
        <div
          className="absolute mt-2 bg-gray-900 rounded-xl shadow-xl p-4 w-72 border border-gray-700 z-50"
          ref={calendarRef}
        >
          {/* Header */}
          <div className="flex justify-between items-center mb-3">
            <button
              className="text-gray-300 hover:text-white cursor-pointer"
              onClick={prevMonth}
            >
              ◀
            </button>
            <span className="text-white font-semibold">
              {new Date(year, month).toLocaleString("default", {
                month: "long",
              })}{" "}
              {year}
            </span>
            <button
              className="text-gray-300 hover:text-white cursor-pointer"
              onClick={nextMonth}
            >
              ▶
            </button>
          </div>

          {/* Grid giorni della settimana */}
          <div className="grid grid-cols-7 text-center text-xs text-gray-400 mb-1">
            <span>Su</span>
            <span>Mo</span>
            <span>Tu</span>
            <span>We</span>
            <span>Th</span>
            <span>Fr</span>
            <span>Sa</span>
          </div>

          {/* Giorni */}
          <div className="grid grid-cols-7 gap-1 text-center">
            {/* Spazi vuoti prima del primo giorno */}
            {Array.from({ length: firstWeekday }).map((_, i) => (
              <span key={"empty" + i}></span>
            ))}

            {/* Giorni effettivi */}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const day = i + 1;
              const isSelected =
                value &&
                value.getDate() === day &&
                value.getMonth() === month &&
                value.getFullYear() === year;

              const today = new Date();

              const isToday =
                today.getDate() === day &&
                today.getMonth() === month &&
                today.getFullYear() === year;

              return (
                <button
                  key={day}
                  onClick={() => handleSelect(day)}
                  className={`py-1 rounded-md cursor-pointer ${
                    isSelected
                      ? "bg-blue-500 text-white"
                      : "text-gray-300 hover:bg-gray-700"
                  }
                  ${isToday ? "text-orange-600" : ""}
                  `}
                >
                  {day}
                </button>
              );
            })}
          </div>
          <div>
            <button
              key="set-today-btn"
              id="set-today-btn"
              className="py-1 rounded-md bg-orange-600 hover:bg-orange-700 w-full cursor-pointer"
              onClick={setToday}
            >
              Today
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
