"""
GenAI Control Plane Engine
Analyzes logs and provides TTL optimization, prefetch recommendations, and explainability
"""

import asyncio
import logging
from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from engines.ttl_optimizer import TTLOptimizer
from engines.prefetch_analyzer import PrefetchAnalyzer
from engines.explainability import ExplainabilityEngine
from services.log_collector import LogCollector
from services.config_manager import ConfigManager
from api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
log_collector = LogCollector()
ttl_optimizer = TTLOptimizer()
prefetch_analyzer = PrefetchAnalyzer()
explainability_engine = ExplainabilityEngine()
config_manager = ConfigManager()


async def background_analysis_loop():
    """Background task that periodically analyzes logs and updates recommendations"""
    # Get analysis interval from environment (default: 5 minutes = 300 seconds)
    analysis_interval = int(os.getenv("ANALYSIS_INTERVAL_SECONDS", "300"))

    logger.info("🚀 Starting background analysis loop")
    logger.info(
        f"⏱️  Analysis interval: {analysis_interval} seconds ({analysis_interval//60} minutes)"
    )

    while True:
        try:
            # Collect logs from monitoring service
            logs = await log_collector.fetch_logs()

            if logs:
                logger.info(f"📊 Analyzing {len(logs)} log entries")

                # Run TTL optimization
                ttl_recommendations = await ttl_optimizer.analyze(logs)
                if ttl_recommendations:
                    await config_manager.update_ttl_config(ttl_recommendations)
                    logger.info(
                        f"✅ Updated {len(ttl_recommendations)} TTL recommendations"
                    )

                # Run prefetch analysis
                prefetch_recommendations = await prefetch_analyzer.analyze(logs)
                if prefetch_recommendations:
                    await config_manager.update_prefetch_config(
                        prefetch_recommendations
                    )
                    logger.info(
                        f"✅ Updated {len(prefetch_recommendations)} prefetch rules"
                    )

                # Generate explainability data
                await explainability_engine.process_logs(logs)

            # Wait before next analysis cycle
            await asyncio.sleep(analysis_interval)

        except Exception as e:
            logger.error(f"❌ Error in analysis loop: {e}")
            await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🎯 GenAI Control Plane starting up...")

    # Start background analysis task
    task = asyncio.create_task(background_analysis_loop())

    yield

    # Shutdown
    logger.info("🛑 GenAI Control Plane shutting down...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# Create FastAPI app
app = FastAPI(
    title="Smart CDN - GenAI Control Plane",
    description="AI-driven CDN optimization engine",
    version="1.0.0",
    lifespan=lifespan,
)

# Include API routes and inject dependencies
from api import routes as api_routes

api_routes.config_manager = config_manager
api_routes.ttl_optimizer = ttl_optimizer
api_routes.prefetch_analyzer = prefetch_analyzer
api_routes.explainability_engine = explainability_engine

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "service": "GenAI Control Plane",
        "status": "running",
        "features": [
            "AI-Driven TTL Optimization",
            "Smart Prefetching",
            "Explainability Layer",
        ],
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
