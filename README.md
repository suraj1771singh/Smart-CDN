# 🚀 Smart CDN with GenAI Control Plane

A production-inspired Content Delivery Network (CDN) with AI-driven optimization, explainability, and smart prefetching. This project demonstrates **how real CDNs like Cloudflare and Akamai separate the data plane (fast) from the control plane (smart)**.

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

**Interview Gold:**

> "I added an explainability layer to make CDN decisions transparent and debuggable, turning a black box into a glass box."

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

### Quick Start

1. **Clone and navigate to project:**

```bash
cd cdn-simulator
```

2. **Build and start all services:**

```bash
docker-compose up --build
```

3. **Access the dashboard:**

```
http://localhost:8888
```

You'll see an interactive dashboard with all features and endpoints!

4. **Test the CDN:**

```bash
# Make requests through the CDN
curl -i http://localhost:8080/hello.txt
curl -i http://localhost:8080/index.html
curl -i http://localhost:8080/style.css
```

5. **View AI recommendations:**

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

## 🎓 Interview-Worthy Talking Points

### 1. Control Plane vs Data Plane

> "I separated the fast path (data plane) from the smart path (control plane), just like production CDNs. GenAI analyzes asynchronously without adding latency."

### 2. Adaptive TTL

> "Instead of static cache durations, my CDN uses AI to adapt TTL based on traffic patterns, reducing origin load and improving efficiency."

### 3. Explainability

> "Every CDN decision has a human-readable explanation. When debugging, you can see exactly why a cache miss occurred or why a particular edge was selected."

### 4. Predictive Prefetching

> "The system learns access patterns and prefetches related assets, reducing perceived latency for users."

### 5. Production-Inspired Architecture

> "This mirrors how Cloudflare and Akamai work - fast edge caching with async ML-driven optimization."

---

## 📈 Metrics You Can Demonstrate

After running tests:

1. **Cache Hit Rate Improvement:** Show how hit rate increases over time
2. **TTL Adaptation:** Demonstrate TTL changes based on traffic
3. **Pattern Detection:** Show prefetch rules generated from access patterns
4. **Explainability:** Pull up explanations for specific requests
5. **Distributed Load:** Show requests distributed across multiple edges

---

## 🧱 Project Structure

```
cdn-simulator/
│
├── docker-compose.yml           # Orchestrates all services
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
├── edge-enhanced/               # Enhanced edge servers
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
└── README.md                    # This file
```

---

## 🎉 What Makes This Project Stand Out

### 1. Production-Inspired Design

✅ Mirrors real CDN architectures (Cloudflare, Akamai)  
✅ Control plane / data plane separation  
✅ Asynchronous AI analysis

### 2. Unique Features

✅ Explainability layer (rare in CDNs)  
✅ Adaptive TTL optimization  
✅ Pattern-based prefetching

### 3. Interview-Ready

✅ Clear talking points  
✅ Demonstrable metrics  
✅ Comprehensive documentation

### 4. Technical Depth

✅ Multi-container orchestration  
✅ Log aggregation pipeline  
✅ AI-driven decision making  
✅ RESTful API design

---

## 🔮 Future Enhancements

- [ ] Geographic routing based on client location
- [ ] Real-time cache invalidation
- [ ] ML model training for better predictions
- [ ] WebSocket for live dashboard updates
- [ ] Prometheus metrics integration
- [ ] Grafana dashboards
- [ ] A/B testing different cache strategies

---

## 📝 License

MIT License - Feel free to use this for learning and interviews!

---

## 🙏 Acknowledgments

This project demonstrates real-world CDN concepts inspired by:

- Cloudflare's edge network architecture
- Akamai's adaptive optimization
- Modern control plane/data plane separation
- Production ML/AI integration patterns

---

**Built with ❤️ to demonstrate production-grade system design**

**Perfect for:** System design interviews • Portfolio projects • Learning CDN architecture • Understanding AI/ML integration in infrastructure
