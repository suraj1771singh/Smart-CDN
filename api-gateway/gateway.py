"""
API Gateway
Unified API for accessing all Smart CDN features
"""

import logging
import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from typing import Optional

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart CDN API Gateway",
    description="Unified API for AI-driven CDN with explainability",
    version="1.0.0",
)

GENAI_URL = os.getenv("GENAI_URL", "http://genai-engine:8000")
MONITORING_URL = os.getenv("MONITORING_URL", "http://monitoring:8001")


# Helper function to proxy requests
def proxy_get(url: str):
    """Proxy GET request to backend service"""
    try:
        response = requests.get(url, timeout=60)  # Increased timeout for AI processing
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error proxying request to {url}: {e}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Interactive dashboard"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Smart CDN Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .header {
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                margin-bottom: 20px;
                text-align: center;
            }
            h1 {
                color: #667eea;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #666;
                font-size: 18px;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            .card {
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .card h2 {
                color: #667eea;
                margin-bottom: 15px;
                font-size: 20px;
            }
            .feature {
                margin: 10px 0;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }
            .endpoint {
                background: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
                font-family: monospace;
                font-size: 14px;
            }
            .endpoint a {
                color: #667eea;
                text-decoration: none;
            }
            .endpoint a:hover {
                text-decoration: underline;
            }
            .architecture {
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            pre {
                background: #2d2d2d;
                color: #f8f8f2;
                padding: 20px;
                border-radius: 8px;
                overflow-x: auto;
                font-size: 14px;
                line-height: 1.5;
            }
            .badge {
                display: inline-block;
                padding: 5px 10px;
                background: #667eea;
                color: white;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                margin-right: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Smart CDN with GenAI Control Plane</h1>
                <p class="subtitle">AI-Driven CDN Optimization • TTL Management • Smart Prefetching • Explainability</p>
            </div>

            <div class="grid">
                <div class="card">
                    <h2>🧠 AI Features</h2>
                    <div class="feature">
                        <strong>TTL Optimization</strong><br>
                        Adaptive cache TTL based on traffic patterns
                    </div>
                    <div class="feature">
                        <strong>Smart Prefetching</strong><br>
                        Predict and prefetch related assets
                    </div>
                    <div class="feature">
                        <strong>Explainability Layer</strong><br>
                        Understand why CDN makes each decision
                    </div>
                </div>

                <div class="card">
                    <h2>📊 Key Endpoints</h2>
                    <div class="endpoint">
                        <a href="/api/stats" target="_blank">GET /api/stats</a><br>
                        <span style="color: #666;">Overall CDN statistics</span>
                    </div>
                    <div class="endpoint">
                        <a href="/api/recommendations/ttl" target="_blank">GET /api/recommendations/ttl</a><br>
                        <span style="color: #666;">AI-optimized TTL values</span>
                    </div>
                    <div class="endpoint">
                        <a href="/api/recommendations/prefetch" target="_blank">GET /api/recommendations/prefetch</a><br>
                        <span style="color: #666;">Smart prefetch rules</span>
                    </div>
                    <div class="endpoint">
                        <a href="/api/explainability/recent" target="_blank">GET /api/explainability/recent</a><br>
                        <span style="color: #666;">Recent request explanations</span>
                    </div>
                </div>

                <div class="card">
                    <h2>🎯 Test the CDN</h2>
                    <div class="endpoint">
                        <a href="http://localhost:8080/hello.txt" target="_blank">http://localhost:8080/hello.txt</a><br>
                        <span style="color: #666;">Make requests through load balancer</span>
                    </div>
                    <div class="endpoint">
                        <a href="http://localhost:8001/api/stats" target="_blank">http://localhost:8001/api/stats</a><br>
                        <span style="color: #666;">View monitoring stats</span>
                    </div>
                    <p style="margin-top: 15px; color: #666; font-size: 14px;">
                        💡 Tip: Make multiple requests to see cache behavior and AI recommendations update
                    </p>
                </div>
            </div>

            <div class="architecture">
                <h2 style="color: #667eea; margin-bottom: 15px;">🏗️ Architecture</h2>
                <pre>
DATA PLANE (Fast Path - No AI)
┌─────────┐
│ Client  │
└────┬────┘
     │
     ▼
┌──────────────┐
│Load Balancer │ (port 8080)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Edge Servers │ (Cache + Logs)
│  edge1/edge2 │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Origin Server │
└──────────────┘

CONTROL PLANE (Smart - AI-Driven)
┌──────────────┐
│Edge Logs     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Monitoring   │ (port 8001)
│   Service    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ GenAI Engine │ (port 8000)
│ • TTL Opt    │
│ • Prefetch   │
│ • Explain    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Configuration │
│   Updates    │
└──────────────┘
                </pre>
            </div>

            <div class="card" style="margin-top: 20px;">
                <h2>🎓 Interview-Ready Talking Points</h2>
                <div class="feature">
                    <span class="badge">CONTROL PLANE</span>
                    GenAI lives outside the request path, analyzes async
                </div>
                <div class="feature">
                    <span class="badge">DATA PLANE</span>
                    Fast edge caching with minimal latency
                </div>
                <div class="feature">
                    <span class="badge">ADAPTIVE</span>
                    TTL values adjust based on traffic patterns
                </div>
                <div class="feature">
                    <span class="badge">EXPLAINABLE</span>
                    Every CDN decision has a human-readable explanation
                </div>
                <div class="feature">
                    <span class="badge">PREDICTIVE</span>
                    Smart prefetching reduces perceived latency
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "api-gateway"}


@app.get("/api/stats")
async def get_stats():
    """Get overall CDN statistics"""
    try:
        monitoring_stats = proxy_get(f"{MONITORING_URL}/api/stats")
        genai_stats = proxy_get(f"{GENAI_URL}/api/v1/stats")

        return {
            "status": "operational",
            "monitoring": monitoring_stats,
            "genai": genai_stats,
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/recommendations/ttl")
async def get_ttl_recommendations():
    """Get AI-driven TTL recommendations"""
    return proxy_get(f"{GENAI_URL}/api/v1/recommendations/ttl")


@app.get("/api/recommendations/prefetch")
async def get_prefetch_recommendations():
    """Get smart prefetch recommendations"""
    return proxy_get(f"{GENAI_URL}/api/v1/recommendations/prefetch")


@app.get("/api/explainability/recent")
async def get_recent_explanations(limit: int = 10):
    """Get recent request explanations"""
    return proxy_get(f"{GENAI_URL}/api/v1/explainability/recent?limit={limit}")


@app.get("/api/explainability/{request_id}")
async def get_explanation(request_id: str):
    """Get explanation for specific request"""
    return proxy_get(f"{GENAI_URL}/api/v1/explainability/{request_id}")


@app.get("/api/logs")
async def get_logs(limit: int = 50):
    """Get recent logs from monitoring"""
    return proxy_get(f"{MONITORING_URL}/api/logs?limit={limit}")


@app.get("/api/config/history")
async def get_config_history(limit: int = 20):
    """Get configuration change history"""
    return proxy_get(f"{GENAI_URL}/api/v1/config/history?limit={limit}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8888)
