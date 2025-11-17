import { api } from "./client";
import type {
  CrashedContainerChartStats,
  CrashedContainerLogs,
} from "../models/crashedContainer";

export async function getChartStats(
  date_from: string,
  date_to: string
): Promise<CrashedContainerChartStats[]> {
  try {
    const res = await api.get("/crashed_containers/chart-stats", {
      params: { date_from, date_to },
    });

    return res.data;
  } catch (error) {
    console.error(error);
    return [];
  }
}

export async function getCrashedContainersMetrics(
  date_from: string,
  date_to: string
): Promise<CrashedContainerLogs[]> {
  try {
    const res = await api.get("/crashed_containers", {
      params: { date_from, date_to },
    });

    return res.data;
  } catch (error) {
    console.error(error);
    return [];
  }
}
