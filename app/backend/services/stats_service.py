from datetime import datetime
from app.backend.repositories.crashed_container_repository import CrashedContainerRepository

class StatsService:
     
    @staticmethod   
    def get_crashed_containers(date_from:str, date_to:str):
        
        try:
            date_from = datetime.strptime(date_from, "%Y-%m-%d")
            date_to = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Incorrect date format, should be YYYY-MM-DD")

        crashed_containers = CrashedContainerRepository.get_all_crashed_containers(date_from, date_to)
        return crashed_containers
    
    @staticmethod
    def get_crashed_containers_chart_stats(date_from:str, date_to:str):
        
        try:
            date_from = datetime.strptime(date_from, "%Y-%m-%d")
            date_to = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Incorrect date format, should be YYYY-MM-DD")

        graph_stats = CrashedContainerRepository.get_crashed_containers_stats_by_date(date_from, date_to)
        return graph_stats
        