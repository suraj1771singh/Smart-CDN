# 🚀 Smart CDN with GenAI Control Plane

A Content Delivery Network (CDN) with AI-driven optimization, explainability, and smart prefetching. The architecture separates the data plane (fast request handling) from the control plane (intelligent optimization) for scalable performance.

## 🎯 Core Philosophy

### ❌ GenAI is NOT in the request path

### ✅ GenAI lives in the **Control Plane**

```
DATA PLANE (Fast)
Client → Load Balancer → Edge Cache → Origin

CONTROL PLANE (Smart)
Logs → GenAI → Recommendations → Config Updates
```

This mirrors **real CDN architectures** where AI analyzes patterns asynchronously without adding latency to user requests.

---

## 🏗️ Architecture

```
Clients
   ↓
Load Balancer (port 8080)
   ↓
Edge Servers (edge1, edge2) - Cache + Logging
   ↓
Origin Server - Static Content

   ║ (Async Analytics)
   ║
   ▼
Monitoring Service (port 8001) - Log Aggregation
   ↓
GenAI Engine (port 8000) - AI Analysis
   • TTL Optimizer
   • Prefetch Analyzer
   • Explainability Engine
   ↓
Configuration Updates
   ↓
API Gateway (port 8888) - Unified Interface
```

---

## 🥇 Three Core Features

### 1. AI-Driven TTL Optimization (Primary Feature)

**Problem:** Static TTLs don't adapt to traffic patterns.

**Solution:** GenAI analyzes request patterns and recommends optimal cache durations.

**Inputs to AI:**

- Request frequency per file
- Cache hit/miss ratio
- File type (image, CSS, JS, HTML)
- Time-based traffic spikes

**AI Output Example:**

```json
{
  "file": "/promo/banner.jpg",
  "recommended_ttl": 21600,
  "ttl_human": "6h",
  "reason": "Traffic increased 5× in last 10 mins - high-read, low-change content",
  "stats": {
    "total_requests": 127,
    "cache_hit_ratio": "78.74%",
    "file_type": "image"
  }
}
```

**Why This Is Smart:**

- TTL becomes **adaptive** instead of static
- Reduces origin load during traffic spikes
- Improves cache efficiency automatically

---

### 2. Explainability Layer (Uniqueness Booster)

**Problem:** CDN decisions are opaque black boxes.

**Solution:** Every CDN decision has a human-readable explanation.

**What We Explain:**

- Why cache HIT or MISS happened
- Why a particular edge served the request
- Why TTL was increased/decreased

**Example Explanation:**

```json
{
  "request_path": "/index.html",
  "edge_server": "edge1",
  "cache_status": "MISS",
  "ttl": 300,
  "summary": "Cache MISS: File '/index.html' requested for first time in this region, fetched from origin",
  "explanations": {
    "cache": "First-time request - not yet cached",
    "routing": "Routed to edge1 (closest to client location)",
    "ttl": "TTL set to 5 minutes - HTML may update frequently"
  }
}
```

**Where It Lives:**

- Stored in logs
- Exposed via API: `GET /api/explainability/recent`
- Available as debug headers

---

### 3. Smart Prefetching (Performance Multiplier)

**Problem:** Users request related assets sequentially, causing delays.

**Solution:** AI detects patterns and prefetches related assets proactively.

**Pattern Detection:**

```
Observed Pattern:
/index.html → /style.css → /script.js

AI Recommendation:
When /index.html is requested, prefetch /style.css and /script.js
```

**Output Example:**

```json
{
  "trigger_file": "/index.html",
  "prefetch_files": ["/style.css", "/script.js", "/logo.png"],
  "confidence": 0.9,
  "reason": "Pattern detected: /index.html is frequently followed by 3 assets"
}
```

**Why This Is Safe:**

- Prefetch happens **after** serving main request (non-blocking)
- Only caches predicted assets
- TTL rules still apply

---

## 📦 Component Responsibilities

| Component              | Responsibility                             |
| ---------------------- | ------------------------------------------ |
| **Edge Servers**       | Cache content, execute prefetch, send logs |
| **Load Balancer**      | Distribute traffic across edge servers     |
| **Origin Server**      | Source of truth for content                |
| **Monitoring Service** | Aggregate logs from all edge servers       |
| **GenAI Engine**       | Analyze patterns, generate recommendations |
| **API Gateway**        | Unified interface for all services         |

---

## 🚀 Getting Started

### Prerequisites

- Docker
- Docker Compose
- 8GB RAM minimum
- Ports 8000, 8001, 8080, 8888 available

### Configuration

Create a `.env` file in the project root:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your-api-key-here

# GenAI Model (gpt-3.5-turbo or gpt-4)
GENAI_MODEL=gpt-3.5-turbo

# Analysis interval in seconds (default: 300 = 5 minutes)
ANALYSIS_INTERVAL_SECONDS=300

# Enable/disable AI features (true/false)
USE_GENAI_TTL=true
USE_GENAI_PREFETCH=true
USE_GENAI_EXPLAIN=true
```

### Quick Start

1. **Clone and navigate to project:**

```bash
cd cdn-simulator
```

2. **Configure environment (see Configuration above)**

3. **Build and start all services:**

```bash
docker-compose up --build
```

4. **Access the dashboard:**

```
http://localhost:8888
```

You'll see an interactive dashboard with all features and endpoints!

5. **Test the CDN:**

```bash
# Make requests through the CDN
curl -i http://localhost:8080/hello.txt
curl -i http://localhost:8080/index.html
curl -i http://localhost:8080/style.css
```

6. **View AI recommendations:**

```bash
# TTL recommendations
curl http://localhost:8888/api/recommendations/ttl

# Prefetch recommendations
curl http://localhost:8888/api/recommendations/prefetch

# Recent explanations
curl http://localhost:8888/api/explainability/recent
```

---

## 🔍 Observe Smart Behavior

### First Request (Cache MISS)

```bash
curl -i http://localhost:8080/hello.txt
```

Response headers:

```
X-Cache-Status: MISS
X-Edge-Server: edge1
X-Cache-TTL: 60s
```

**Explanation:** First request, fetched from origin and cached.

### Second Request (Cache HIT)

```bash
curl -i http://localhost:8080/hello.txt
```

Response headers:

```
X-Cache-Status: HIT
X-Edge-Server: edge2
X-Cache-TTL: 60s
```

**Explanation:** Served from edge cache (much faster!).

### After Multiple Requests (AI Optimization)

After making 20+ requests:

```bash
curl http://localhost:8888/api/recommendations/ttl | jq
```

Output:

```json
{
  "total_rules": 3,
  "recommendations": {
    "/hello.txt": {
      "ttl": 3600,
      "ttl_human": "1h",
      "reason": "High traffic (47 requests) - increased TTL for better cache efficiency | Low cache hit ratio (34.04%) - increasing TTL"
    }
  }
}
```

**AI detected high traffic and optimized TTL automatically!**

---

## 📊 Key Endpoints

### Main Dashboard

- **Dashboard:** `http://localhost:8888/`
- **CDN:** `http://localhost:8080/`

### AI Recommendations

- **TTL Recommendations:** `GET http://localhost:8888/api/recommendations/ttl`
- **Prefetch Rules:** `GET http://localhost:8888/api/recommendations/prefetch`
- **Statistics:** `GET http://localhost:8888/api/stats`

### Explainability

- **Recent Explanations:** `GET http://localhost:8888/api/explainability/recent`
- **Specific Request:** `GET http://localhost:8888/api/explainability/{request_id}`

### Monitoring

- **Logs:** `GET http://localhost:8888/api/logs`
- **Config History:** `GET http://localhost:8888/api/config/history`

---

## 🧪 Testing Scenarios

### Scenario 1: Test Cache Behavior

```bash
# Make 10 requests and observe cache status
for i in {1..10}; do
  curl -i http://localhost:8080/hello.txt | grep -E "X-Cache-Status|X-Edge-Server"
done
```

You'll see cache MISses become HITs, and load balancing between edge servers.

### Scenario 2: Trigger TTL Optimization

```bash
# Make 50 requests to trigger AI analysis
for i in {1..50}; do
  curl -s http://localhost:8080/hello.txt > /dev/null
  echo "Request $i sent"
done

# Wait 30 seconds for AI analysis
sleep 30

# Check TTL recommendations
curl http://localhost:8888/api/recommendations/ttl | jq
```

### Scenario 3: Test Prefetch Pattern Detection

```bash
# Simulate user browsing pattern 20 times
for i in {1..20}; do
  curl -s http://localhost:8080/index.html > /dev/null
  curl -s http://localhost:8080/style.css > /dev/null
  curl -s http://localhost:8080/script.js > /dev/null
  sleep 0.5
done

# Wait for AI analysis
sleep 30

# Check prefetch recommendations
curl http://localhost:8888/api/recommendations/prefetch | jq
```

---

## 🛠️ Development

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f genai-engine
docker-compose logs -f edge1
docker-compose logs -f monitoring
```

### Rebuild After Changes

```bash
docker-compose down
docker-compose up --build
```

### Clean Everything

```bash
docker-compose down -v
docker system prune -a
```

### Access Persistent Data

AI-generated configurations are stored locally in the `data/` folder:

```bash
# View TTL recommendations
cat data/ttl_config.json

# View prefetch rules
cat data/prefetch_config.json

# View configuration history
cat data/config_history.json
```

These files persist across container restarts and can be edited or backed up directly.

### Add More Edge Servers

Edit `docker-compose.yml`:

```yaml
edge3:
  build: ./edge-enhanced
  container_name: edge3
  environment:
    - HOSTNAME=edge3
    - MONITORING_SERVICE_URL=http://monitoring:8001
  depends_on:
    - origin
    - monitoring
  networks:
    - cdn_network
```

Add to `load-balancer/nginx.conf`:

```nginx
upstream edge_pool {
  server edge1:80;
  server edge2:80;
  server edge3:80;
}
```

---

## 🔐 Safety & Control (Very Important)

### GenAI Does NOT:

❌ Modify infrastructure automatically  
❌ Sit in the request path  
❌ Add latency to user requests  
❌ Make uncontrolled changes

### GenAI DOES:

✅ Suggest configurations  
✅ Explain behavior  
✅ Optimize over time  
✅ Operate asynchronously

---

## 🧱 Project Structure

```
cdn-simulator/
│
├── docker-compose.yml           # Orchestrates all services
├── .env                         # Configuration (OpenAI key, etc.)
│
├── origin/                      # Origin server
│   ├── Dockerfile
│   ├── nginx.conf
│   └── static/                  # Static content
│       ├── hello.txt
│       ├── index.html
│       ├── style.css
│       └── script.js
│
├── edge-enhanced/               # Edge servers with logging
│   ├── Dockerfile
│   ├── nginx.conf              # Caching config
│   ├── log_sender.py           # Sends logs to monitoring
│   └── entrypoint.sh
│
├── load-balancer/               # Load balancer
│   └── nginx.conf
│
├── monitoring/                  # Log aggregation service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── server.py
│
├── control-plane/genai-engine/  # AI control plane
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # Main engine
│   ├── engines/
│   │   ├── ttl_optimizer.py    # TTL optimization
│   │   ├── prefetch_analyzer.py # Prefetch analysis
│   │   └── explainability.py   # Explainability
│   ├── services/
│   │   ├── log_collector.py    # Fetch logs
│   │   └── config_manager.py   # Manage config
│   └── api/
│       └── routes.py           # API endpoints
│
├── api-gateway/                 # Unified API
│   ├── Dockerfile
│   ├── requirements.txt
│   └── gateway.py              # API gateway + dashboard
│
├── data/                        # Persistent AI data storage
│   ├── ttl_config.json         # TTL recommendations
│   ├── prefetch_config.json    # Prefetch rules
│   └── config_history.json     # Change history
│
└── README.md                    # This file
```

---

## 📝 License

MIT License - Feel free to use this for learning and interviews!

---

## 🙏 Acknowledgments

This project implements real-world CDN concepts inspired by production systems like Cloudflare and Akamai, with a focus on control plane/data plane separation and AI-driven optimization.
