from datetime import datetime
from app.repositories.crashed_container_repository import CrashedContainerRepository

class StatsService:
     
    @staticmethod   
    def get_crashed_containers(date:str):
        
        try:
            date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Incorrect date format, should be YYYY-MM-DD")

        crashed_containers = CrashedContainerRepository.get_all_crashed_containers(date)
        return crashed_containers
    
    @staticmethod
    def get_crashed_containers_chart_stats(date:str):
        
        try:
            date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Incorrect date format, should be YYYY-MM-DD")

        graph_stats = CrashedContainerRepository.get_crashed_containers_stats_by_date(date)
        return graph_stats
        