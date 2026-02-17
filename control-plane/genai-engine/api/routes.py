"""
API Routes for GenAI Control Plane
Exposes recommendations, explainability, and configuration
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel

router = APIRouter()

# Global instances (injected from main.py)
config_manager = None
ttl_optimizer = None
prefetch_analyzer = None
explainability_engine = None

# Response Models
class TTLRecommendation(BaseModel):
    file: str
    recommended_ttl: int
    ttl_human: str
    reason: str

class PrefetchRule(BaseModel):
    trigger_file: str
    prefetch_files: List[str]
    confidence: float
    reason: str

class Explanation(BaseModel):
    request_path: str
    edge_server: str
    cache_status: str
    ttl: int
    summary: str

# Endpoints

@router.get("/recommendations/ttl", response_model=Dict)
async def get_ttl_recommendations():
    """Get current TTL recommendations"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("🌐 [DEBUG] API endpoint /recommendations/ttl called")
    logger.info(f"🌐 [DEBUG] config_manager instance ID: {id(config_manager)}")
    
    if config_manager is None:
        logger.error("❌ [DEBUG] config_manager is None!")
        return {
            "total_rules": 0,
            "recommendations": {},
            "description": "ERROR: Config manager not initialized"
        }
    
    config = config_manager.get_ttl_config()
    
    logger.info(f"🌐 [DEBUG] Returning {len(config)} TTL recommendations")
    
    return {
        "total_rules": len(config),
        "recommendations": config,
        "description": "AI-optimized TTL values for cached files"
    }

@router.get("/recommendations/prefetch", response_model=Dict)
async def get_prefetch_recommendations():
    """Get current prefetch recommendations"""
    if config_manager is None:
        return {
            "total_rules": 0,
            "recommendations": {},
            "description": "ERROR: Config manager not initialized"
        }
    
    config = config_manager.get_prefetch_config()
    
    return {
        "total_rules": len(config),
        "recommendations": config,
        "description": "Smart prefetch rules based on access patterns"
    }

@router.get("/explainability/recent")
async def get_recent_explanations(limit: int = 10):
    """Get recent request explanations"""
    if explainability_engine is None:
        return {"count": 0, "explanations": []}
    
    explanations = explainability_engine.get_recent_explanations(limit)
    
    return {
        "count": len(explanations),
        "explanations": explanations
    }

@router.get("/explainability/{request_id}")
async def get_explanation(request_id: str):
    """Get explanation for a specific request"""
    if explainability_engine is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    explanation = explainability_engine.get_explanation(request_id)
    
    if not explanation:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return explanation

@router.get("/config/history")
async def get_config_history(limit: int = 50):
    """Get configuration change history"""
    if config_manager is None:
        return {"total_changes": 0, "history": []}
    
    history = config_manager.get_config_history(limit)
    
    return {
        "total_changes": len(history),
        "history": history
    }

@router.get("/stats")
async def get_stats():
    """Get overall statistics"""
    if not all([config_manager, ttl_optimizer, prefetch_analyzer]):
        return {"status": "not_initialized"}
    
    return {
        "ttl_rules": len(config_manager.get_ttl_config()),
        "prefetch_rules": len(config_manager.get_prefetch_config()),
        "files_analyzed": len(ttl_optimizer.file_stats),
        "patterns_detected": len(prefetch_analyzer.pattern_counts),
        "status": "operational"
    }

@router.get("/debug/memory")
async def debug_memory():
    """Debug endpoint to see what's in memory"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("🐛 [DEBUG] Memory debug endpoint called")
    logger.info(f"🐛 [DEBUG] config_manager instance ID: {id(config_manager)}")
    logger.info(f"🐛 [DEBUG] config_manager is None: {config_manager is None}")
    
    if not all([config_manager, ttl_optimizer]):
        return {
            "error": "Services not initialized",
            "config_manager_none": config_manager is None,
            "ttl_optimizer_none": ttl_optimizer is None
        }
    
    return {
        "ttl_config_count": len(config_manager.ttl_config),
        "ttl_config_keys": list(config_manager.ttl_config.keys()),
        "ttl_config_raw": config_manager.ttl_config,
        "file_stats_count": len(ttl_optimizer.file_stats),
        "file_stats_keys": list(ttl_optimizer.file_stats.keys()),
        "config_history_count": len(config_manager.config_history),
        "instance_ids": {
            "config_manager": id(config_manager),
            "ttl_optimizer": id(ttl_optimizer)
        }
    }

