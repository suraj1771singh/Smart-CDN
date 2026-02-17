"""
Log Collector Service
Fetches logs from the monitoring service
"""
import logging
import requests
from typing import List, Dict
import os

logger = logging.getLogger(__name__)

class LogCollector:
    """Collects logs from monitoring service"""
    
    def __init__(self):
        self.monitoring_url = os.getenv('MONITORING_SERVICE_URL', 'http://monitoring:8001')
    
    async def fetch_logs(self) -> List[Dict]:
        """Fetch recent logs from monitoring service"""
        try:
            response = requests.get(
                f"{self.monitoring_url}/api/logs",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('logs', [])
            else:
                logger.warning(f"Failed to fetch logs: {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching logs: {e}")
            return []

