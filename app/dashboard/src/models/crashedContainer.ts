export interface CrashedContainerBase {
    container_id: string;
    container_name: string;
    crashed_on?: string | null;
}

export interface CrashedContainerLogs extends CrashedContainerBase {
    logs: string;

}

export interface CrashedContainerChartStats extends CrashedContainerBase {
    crash_count: number;
}