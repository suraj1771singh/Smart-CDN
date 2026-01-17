#!/usr/bin/env python3
"""
Log Sender for Edge Servers
Monitors nginx access logs and sends them to monitoring service
"""
import os
import sys
import time
import json
import requests
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MONITORING_URL = os.getenv('MONITORING_SERVICE_URL', 'http://monitoring:8001')
LOG_FILE = '/var/log/nginx/cdn_access.log'
BATCH_SIZE = 10
SEND_INTERVAL = 5  # seconds

def parse_log_line(line):
    """Parse JSON log line from nginx"""
    try:
        log_data = json.loads(line)
        
        # Transform to monitoring service format
        return {
            'timestamp': log_data.get('timestamp'),
            'client_ip': log_data.get('client_ip'),
            'request_path': log_data.get('request_path'),
            'request_method': log_data.get('request_method'),
            'cache_status': log_data.get('cache_status', 'MISS'),
            'edge_server': log_data.get('edge_server', os.getenv('HOSTNAME', 'unknown')),
            'ttl': int(log_data.get('ttl', '60').rstrip('s')) if log_data.get('ttl') else 60,
            'response_time_ms': float(log_data.get('response_time', 0)) * 1000,
            'status_code': int(log_data.get('status_code', 200)),
            'bytes_sent': int(log_data.get('bytes_sent', 0))
        }
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning(f"Failed to parse log line: {e}")
        return None

def send_logs_batch(logs):
    """Send batch of logs to monitoring service"""
    try:
        response = requests.post(
            f"{MONITORING_URL}/api/logs/batch",
            json=logs,
            timeout=5
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Sent {len(logs)} logs to monitoring service")
            return True
        else:
            logger.error(f"❌ Failed to send logs: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error sending logs: {e}")
        return False

def tail_log_file(filename):
    """Tail log file and yield new lines"""
    try:
        with open(filename, 'r') as f:
            # Move to end of file
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    yield line.strip()
                else:
                    time.sleep(0.1)
    except FileNotFoundError:
        logger.error(f"Log file not found: {filename}")
        time.sleep(5)
        return

def main():
    """Main loop"""
    logger.info(f"🚀 Starting log sender for {os.getenv('HOSTNAME', 'unknown')}")
    logger.info(f"📡 Monitoring service: {MONITORING_URL}")
    logger.info(f"📄 Log file: {LOG_FILE}")
    
    # Wait for nginx to start and create log file
    wait_count = 0
    while not os.path.exists(LOG_FILE) and wait_count < 30:
        logger.info("⏳ Waiting for nginx to start...")
        time.sleep(1)
        wait_count += 1
    
    if not os.path.exists(LOG_FILE):
        logger.error("❌ Log file not found after waiting")
        sys.exit(1)
    
    # Buffer for batching logs
    log_buffer = []
    last_send_time = time.time()
    
    # Start tailing log file
    for line in tail_log_file(LOG_FILE):
        # Parse log line
        log_entry = parse_log_line(line)
        
        if log_entry:
            log_buffer.append(log_entry)
        
        # Send batch when buffer is full or interval elapsed
        current_time = time.time()
        if len(log_buffer) >= BATCH_SIZE or (current_time - last_send_time) >= SEND_INTERVAL:
            if log_buffer:
                send_logs_batch(log_buffer)
                log_buffer = []
                last_send_time = current_time

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Log sender stopped")
        sys.exit(0)

