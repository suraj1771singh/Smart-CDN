"""
Configuration Manager
Stores and distributes CDN configuration updates
"""
import logging
from typing import List, Dict
import json
from datetime import datetime
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages CDN configuration and recommendations with persistent storage"""
    
    def __init__(self, data_dir: str = "/data"):
        """
        Initialize ConfigManager with persistent file storage
        
        Args:
            data_dir: Directory to store configuration files (default: /data)
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.ttl_file = self.data_dir / "ttl_config.json"
        self.prefetch_file = self.data_dir / "prefetch_config.json"
        self.history_file = self.data_dir / "config_history.json"
        
        # Load existing data from files
        self.ttl_config = self._load_json(self.ttl_file, {})
        self.prefetch_config = self._load_json(self.prefetch_file, {})
        self.config_history = self._load_json(self.history_file, [])
        
        logger.info(f"💾 ConfigManager initialized with persistent storage at {data_dir}")
        logger.info(f"📂 Loaded {len(self.ttl_config)} TTL configs, {len(self.prefetch_config)} prefetch configs")
    
    async def update_ttl_config(self, recommendations: List[Dict]):
        """Update TTL configuration based on recommendations"""
        logger.info(f"🔧 [DEBUG] Received {len(recommendations)} TTL recommendations")
        
        for rec in recommendations:
            file_path = rec['file']
            ttl = rec['recommended_ttl']
            
            self.ttl_config[file_path] = {
                'ttl': ttl,
                'ttl_human': rec['ttl_human'],
                'reason': rec['reason'],
                'updated_at': rec['timestamp']
            }
            
            logger.info(f"📝 Updated TTL for {file_path}: {rec['ttl_human']}")
        
        # Save to file immediately
        self._save_json(self.ttl_file, self.ttl_config)
        
        logger.info(f"🔧 [DEBUG] Total TTL configs now stored: {len(self.ttl_config)}")
        logger.info(f"🔧 [DEBUG] Stored configs: {list(self.ttl_config.keys())}")
        logger.info(f"💾 Saved TTL config to {self.ttl_file}")
        
        self._add_to_history('ttl_update', recommendations)
    
    async def update_prefetch_config(self, recommendations: List[Dict]):
        """Update prefetch configuration based on recommendations"""
        for rec in recommendations:
            trigger_file = rec['trigger_file']
            prefetch_files = rec['prefetch_files']
            
            self.prefetch_config[trigger_file] = {
                'prefetch_files': prefetch_files,
                'confidence': rec['confidence'],
                'reason': rec['reason'],
                'updated_at': rec['timestamp']
            }
            
            logger.info(f"📝 Updated prefetch rule for {trigger_file}")
        
        # Save to file immediately
        self._save_json(self.prefetch_file, self.prefetch_config)
        logger.info(f"💾 Saved prefetch config to {self.prefetch_file}")
        
        self._add_to_history('prefetch_update', recommendations)
    
    def get_ttl_config(self) -> Dict:
        """Get current TTL configuration"""
        logger.info(f"🔍 [DEBUG] get_ttl_config() called - returning {len(self.ttl_config)} configs")
        logger.info(f"🔍 [DEBUG] Config keys: {list(self.ttl_config.keys())}")
        return self.ttl_config
    
    def get_prefetch_config(self) -> Dict:
        """Get current prefetch configuration"""
        return self.prefetch_config
    
    def get_config_history(self, limit: int = 50) -> List[Dict]:
        """Get configuration change history"""
        return self.config_history[-limit:]
    
    def _add_to_history(self, change_type: str, data: List[Dict]):
        """Add configuration change to history"""
        self.config_history.append({
            'type': change_type,
            'timestamp': datetime.utcnow().isoformat(),
            'changes': len(data),
            'data': data
        })
        
        # Keep last 100 changes
        if len(self.config_history) > 100:
            self.config_history = self.config_history[-100:]
        
        # Save history to file
        self._save_json(self.history_file, self.config_history)
    
    def _load_json(self, file_path: Path, default):
        """Load data from JSON file"""
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    logger.info(f"📂 Loaded data from {file_path}")
                    return data
            else:
                logger.info(f"📂 No existing file at {file_path}, starting fresh")
                return default
        except Exception as e:
            logger.error(f"❌ Error loading {file_path}: {e}")
            return default
    
    def _save_json(self, file_path: Path, data):
        """Save data to JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"💾 Saved data to {file_path}")
        except Exception as e:
            logger.error(f"❌ Error saving to {file_path}: {e}")

