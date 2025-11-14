export interface CrashedContainerBase {
    container_id:string;
    container_name:string;
}

export interface CrashedContainerLogs extends CrashedContainerBase {
    logs: string;
    crashed_on:Date
}

export interface CrashedContainerChartStats extends CrashedContainerBase{
    crash_count:number;
}