import { Navbar } from "../../components/navbar/navbar";
import {Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend} from 'chart.js';
import { useEffect, useState } from "react";
import {Line} from 'react-chartjs-2';
import type { CrashedContainerLogs } from "../../models/crashedContainer";
import { getCrashedContainersMetrics } from "../../api/crashedContainers";
import { build } from "vite";

export function Homepage() {
    ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);


    const [stats, setStats] = useState<CrashedContainerLogs[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const today = new Date().toISOString().split("T")[0];

        getCrashedContainersMetrics(today)
            .then((data) => {
                setStats(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("API error:", err);
                setLoading(false);
            });
    }, []);

    const buildMetricsSection = () => {
        const uniqueCrashedContainers = Object.values(stats.reduce((acc,item) => {
            if(!acc[item.container_id]){
                acc[item.container_id] = {...item};
            }
            else{
                acc[item.container_id].logs += `\n\n${item.logs}`;
            }

            return acc;
        }, {} as Record<string, CrashedContainerLogs>));

        return uniqueCrashedContainers;
    }

    const uniqueCrashedContainers = buildMetricsSection();

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins:{
            legend: {
                position: 'top' as const,
            },
            title: {
                display: true,
                text: 'Sample Line Chart',
            }
        }
    }

    const labels = ['January', 'February', 'March', 'April', 'May', 'June', 'July'];
    const data = {
        labels,
        datasets: [
            {
                label: 'Dataset 1',
                data: labels.map(() => Math.random() * 100),
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.5)',
            },
            {
            
                label: 'Dataset 2',
                data: labels.map(() => Math.random() * 100),
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.5)',
            },
        ]
    }

    return (
        <div className="w-[75%] flex flex-col min-h-screen my-5 p-0 gap-10">
            <Navbar />

            <div className="w-full h-[50vh] container-bg-color rounded-xl p-4">
                <p className="text-start text-sm sm:text-xl p-3">Summary</p>
                <div className="h-[calc(100%-4rem)]">
                    <Line options={options} data={data} />
                </div>
            </div>

            <div className="w-full grid grid-cols-3 gap-4 container-bg-color rounded-xl p-4 text-xs sm:text-sm">
                <div className="col-span-3 text-start text-xl mb-2">
                    <p className="text-start text-sm sm:text-xl p-3">Metrics</p>
                </div>

                <div className="col-span-1 flex justify-center items-start">
                    <div className="w-full sm:w-[80%]  max-h-[50vh] flex flex-col gap-3 p-2 sm:p-4 rounded-md sm:rounded-xl overflow-x-auto overflow-y-auto bg-[#242424]">
                        {
                            loading ?
                            (<p>Loading</p>)
                            :
                            (uniqueCrashedContainers.map((cont) => {
                                return (
                                    <button
                                    key={cont.container_id}
                                    className="w-full bg-gray-600 hover:bg-gray-700 sm:py-2 rounded-md text-white cursor-pointer"
                                    >
                                    {cont.container_name}
                                    </button>
                                );
                            }))
                        }
                    </div>
                </div>

                <div className="col-span-2 text-start p-5 max-h-[50vh] overflow-y-auto rounded-md sm:rounded-xl bg-[#242424]">
                    <p>Selected container logs...</p>
                </div>
            </div>
        </div>
    );

}