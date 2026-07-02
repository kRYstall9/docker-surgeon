import { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Server,
  Box,
  FileText,
} from "lucide-react";
import type { CrashedContainerLogs } from "../../models/crashedContainer";

interface LogsViewerProps {
  logs: Record<string, CrashedContainerLogs[]>;
}

export function LogsViewer({ logs }: LogsViewerProps) {
  const [expandedMachine, setExpandedMachine] = useState<string | null>(null);
  const [selected, setSelected] = useState<CrashedContainerLogs | null>(null);

  const mergedLogs: Record<string, CrashedContainerLogs[]> = Object.fromEntries(
    Object.entries(logs).map(([machine, containers]) => {
      const map = new Map<string, CrashedContainerLogs>();

      for (const c of containers) {
        const existing = map.get(c.container_id);

        if (!existing) {
          map.set(c.container_id, {
            ...c,
            logs: c.logs,
          });
        } else {
          map.set(c.container_id, {
            ...existing,
            logs: `${existing.logs}\n\n${c.logs}`,
          });
        }
      }

      return [machine, Array.from(map.values())] as const;
    })
  );

  return (
    <div className="w-full grid grid-cols-1 md:grid-cols-12 gap-4">
      <div className="md:col-span-4 bg-[#242424] rounded-xl overflow-y-auto p-3 h-[250px] md:h-[55vh]">
        {Object.entries(mergedLogs).map(([machine, containers]) => (
          <div key={machine} className="mb-2">
            <button
              onClick={() =>
                setExpandedMachine((prev) =>
                  prev === machine ? null : machine
                )
              }
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:cursor-pointer hover:bg-neutral-700 transition"
            >
              {expandedMachine === machine ? (
                <ChevronDown size={'1rem'} />
              ) : (
                <ChevronRight size={'1rem'} />
              )}

              <Server size={'1rem'} />

              <span className="flex-1 text-left font-medium">{machine}</span>

              <span className="text-xs text-gray-400">
                {containers.length}
              </span>
            </button>

            {expandedMachine === machine && (
              <div className="mt-2 ml-5 flex flex-col gap-1">
                {containers.map((container) => (
                  <button
                    key={container.container_id}
                    onClick={() => setSelected(container)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-md text-left transition hover:cursor-pointer
                      ${
                        selected?.container_id === container.container_id
                          ? "bg-neutral-600 text-white"
                          : "hover:bg-neutral-700"
                      }`}
                  >
                    <Box size={'0.9rem'} />

                    <span className="truncate">
                      {container.container_name}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="md:col-span-8 bg-[#242424] rounded-xl flex flex-col h-[350px] md:h-[55vh] overflow-y-auto">
        {selected ? (
          <div className="text-center">
            <div className="border-b border-neutral-700 px-5 py-3">
              <h2 className="font-semibold text-lg">
                {selected.container_name}
              </h2>

              <p className="text-sm text-gray-400">
                Machine: {selected.machine}
              </p>
            </div>

            <pre className="flex-1 overflow-auto p-5 text-xs font-mono whitespace-pre-wrap leading-5 text-left">
              {selected.logs}
            </pre>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center flex-1 text-gray-500">
            <FileText size={'2rem'} className="mb-3 opacity-60" />

            <p className="text-lg">No container selected</p>

            <p className="text-sm">
              Select a container from the left panel to view its logs.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}