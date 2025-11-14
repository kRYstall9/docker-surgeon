import { api } from "./client";
import type {CrashedContainerChartStats, CrashedContainerLogs } from "../models/crashedContainer";

export async function getChartStats(date:string): Promise<CrashedContainerChartStats[]> {

    try{
        const res = await api.get('/chart-stats', {
            params: { date }
        });

        return res.data;
    }
    catch(error){
        console.error(error);
        return [];
    }
}

export async function getCrashedContainersMetrics(date:string): Promise<CrashedContainerLogs[]> {

    try{
        const res = await api.get('/crashed_containers', {
            params: { date }
        });

        return res.data;
    }
    catch(error){
        console.error(error);
        return []
    }

}