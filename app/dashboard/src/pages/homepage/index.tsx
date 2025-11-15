import { Navbar } from "../../components/navbar/navbar";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { useEffect, useState } from "react";
import { Bar } from 'react-chartjs-2';
import type { CrashedContainerChartStats, CrashedContainerLogs } from "../../models/crashedContainer";
import { getChartStats, getCrashedContainersMetrics } from "../../api/crashedContainers";

export function Homepage() {
    ChartJS.register(CategoryScale, LinearScale, PointElement, BarElement, Title, Tooltip, Legend);

    const [metrics, setMetrics] = useState<CrashedContainerLogs[]>([]);
    const [chartStats, setChartStats] = useState<CrashedContainerChartStats[]>([]);
    const [selectedContainer, setSelectedContainer] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const today = new Date().toISOString().split("T")[0];

        getCrashedContainersMetrics(today)
            .then((data) => {
                setMetrics(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("API error:", err);
                setLoading(false);
            });
    }, []);

    useEffect(() => {

        const today = new Date().toISOString().split("T")[0];
        getChartStats(subtractDaysFormatted(7), today)
            .then((data: CrashedContainerChartStats[]) => {
                setChartStats(data);
            })
    }, []);

    function subtractDaysFormatted(days: number): string {
        const d = new Date();
        d.setDate(d.getDate() - days);
        return d.toISOString().split("T")[0];
    }


    const buildMetricsSection = () => {
        const uniqueCrashedContainers = Object.values(metrics.reduce((acc: Record<string, CrashedContainerLogs>, item: CrashedContainerLogs) => {
            if (!acc[item.container_id]) {
                acc[item.container_id] = { ...item };
            }
            else {
                acc[item.container_id].logs += `\n\n${item.logs}`;
            }

            return acc;
        }, {} as Record<string, CrashedContainerLogs>));

        return uniqueCrashedContainers;
    }

    const uniqueCrashedContainers = buildMetricsSection();
    const selected = uniqueCrashedContainers.find((x: any) => x.container_id === selectedContainer);

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top' as const,
            },
            title: {
                display: true,
                text: 'Crashed Containers Chart',
            }
        }
    }

    const labels = Array.from(
        new Set(chartStats.map((s: CrashedContainerChartStats) => new Date(s.crashed_on!)))
    )
        .sort((a: any, b: any) => a.getTime() - b.getTime())
        .map((dateStr: any) => {
            new Date(dateStr).toLocaleDateString(undefined, {
                day: "2-digit",
                month: "2-digit"
            })
        });

    const data = {
        labels,
        datasets: [{
            data: chartStats.map((ct: CrashedContainerChartStats) => ({
                x: ct.crashed_on,
                y: ct.crash_count
            }))
        }]
    }

    // const data = {
    //     labels,
    //     datasets: [
    //         {
    //             label: 'Dataset 1',
    //             data: labels.map(() => Math.random() * 100),
    //             borderColor: 'rgb(255, 99, 132)',
    //             backgroundColor: 'rgba(255, 99, 132, 0.5)',
    //         },
    //         {

    //             label: 'Dataset 2',
    //             data: labels.map(() => Math.random() * 100),
    //             borderColor: 'rgb(255, 99, 132)',
    //             backgroundColor: 'rgba(255, 99, 132, 0.5)',
    //         },
    //     ]
    // }

    return (
        <div className="w-[75%] flex flex-col min-h-screen my-5 p-0 gap-10">
            <Navbar />

            <div className="w-full h-[50vh] container-bg-color rounded-xl p-4">
                <p className="text-start text-sm sm:text-xl p-3">Summary</p>
                <div className="h-[calc(100%-4rem)]">
                    <Bar options={options} data={data} />
                </div>
            </div>

            <div className="w-full grid grid-cols-3 gap-4 container-bg-color rounded-xl p-4 text-xs sm:text-sm">
                <div className="col-span-3 text-start text-xl mb-2">
                    <p className="text-start text-sm sm:text-xl p-3">Metrics</p>
                </div>

                <div className="col-span-1 flex justify-center items-start">
                    <div className="w-full sm:w-[80%]  h-[50vh] flex flex-col gap-3 p-2 sm:p-4 rounded-md sm:rounded-xl overflow-x-auto overflow-y-auto bg-[#242424]">
                        {
                            loading ?
                                (<p>Loading</p>)
                                :
                                (uniqueCrashedContainers.map((cont: any) => {
                                    return (
                                        <button
                                            key={cont.container_id}
                                            onClick={() => setSelectedContainer(cont.container_id)}
                                            className="w-full bg-gray-600 hover:bg-gray-700 sm:py-2 rounded-md text-white cursor-pointer"
                                        >
                                            {cont.container_name}
                                        </button>
                                    );
                                }))
                        }
                    </div>
                </div>

                <div className="col-span-2 text-start p-5 h-[50vh] overflow-y-auto rounded-md sm:rounded-xl bg-[#242424] whitespace-pre-wrap">
                    {
                        selectedContainer && selected ? (
                            <p>
                                {selected.logs}
                            </p>
                        )
                            :
                            (
                                <p>Select a container to view logs...</p>
                            )
                    }
                </div>
            </div>
        </div>
    );

}