import { Navbar } from "../../components/navbar/navbar";
import {Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend} from 'chart.js';
import {Line} from 'react-chartjs-2';

export function Homepage() {
    ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

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
                        {Array.from({ length: 15 }).map((_, i) => (
                            <button
                            key={i}
                            className="w-full bg-gray-600 hover:bg-gray-700 sm:py-2 rounded-md text-white cursor-pointer"
                            >
                            Cont {i + 1}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="col-span-2 text-start p-5 max-h-[50vh] overflow-y-auto rounded-md sm:rounded-xl bg-[#242424]">
                    <p>Selected container logs...</p>
                </div>
            </div>
        </div>
    );

}