"""
TTL Optimization Engine
Analyzes request patterns and recommends optimal cache TTL values
"""

import logging
from typing import List, Dict, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import os
import json
from openai import OpenAI

logger = logging.getLogger(__name__)


class TTLOptimizer:
    """
    AI-driven TTL optimization based on:
    - Request frequency per file
    - Cache hit/miss ratio
    - File type patterns
    - Time-based spikes
    """

    def __init__(self):
        self.file_stats = defaultdict(
            lambda: {
                "requests": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "last_seen": None,
                "file_type": None,
                "request_times": [],
            }
        )

        # Default TTL rules by file type
        self.default_ttls = {
            "image": 3600,  # 1 hour
            "css": 1800,  # 30 minutes
            "js": 1800,  # 30 minutes
            "html": 300,  # 5 minutes
            "json": 600,  # 10 minutes
            "font": 86400,  # 24 hours
            "video": 7200,  # 2 hours
            "default": 1800,  # 30 minutes
        }

        # Initialize OpenAI client
        self.use_genai = os.getenv("USE_GENAI_TTL", "true").lower() == "true"
        api_key = os.getenv("OPENAI_API_KEY")

        if self.use_genai and api_key:
            try:
                self.openai_client = OpenAI(api_key=api_key)
                self.model = os.getenv("GENAI_MODEL", "gpt-3.5-turbo")
                logger.info(
                    f"🤖 TTL Optimizer: OpenAI integration enabled with model {self.model}"
                )
            except Exception as e:
                logger.warning(
                    f"⚠️ Failed to initialize OpenAI: {e}. Falling back to rule-based."
                )
                self.use_genai = False
        else:
            self.use_genai = False
            logger.info("📊 TTL Optimizer: Using rule-based optimization")

    async def analyze(self, logs: List[Dict]) -> List[Dict]:
        """
        Analyze logs and generate TTL recommendations
        """
        # Update stats from logs
        self._update_stats(logs)

        # Generate recommendations
        recommendations = []

        for file_path, stats in self.file_stats.items():
            recommendation = self._calculate_ttl(file_path, stats)
            if recommendation:
                recommendations.append(recommendation)

        return recommendations

    def _update_stats(self, logs: List[Dict]):
        """Update file statistics from logs"""
        for log in logs:
            file_path = log.get("request_path", "")
            cache_status = log.get("cache_status", "MISS")
            timestamp = log.get("timestamp")

            if not file_path:
                continue

            stats = self.file_stats[file_path]
            stats["requests"] += 1
            stats["last_seen"] = timestamp

            if cache_status == "HIT":
                stats["cache_hits"] += 1
            else:
                stats["cache_misses"] += 1

            # Track request times for pattern detection
            stats["request_times"].append(timestamp)

            # Determine file type
            if not stats["file_type"]:
                stats["file_type"] = self._detect_file_type(file_path)

    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type from path"""
        ext_map = {
            ".jpg": "image",
            ".jpeg": "image",
            ".png": "image",
            ".gif": "image",
            ".webp": "image",
            ".css": "css",
            ".js": "js",
            ".html": "html",
            ".htm": "html",
            ".json": "json",
            ".woff": "font",
            ".woff2": "font",
            ".ttf": "font",
            ".mp4": "video",
            ".webm": "video",
        }

        for ext, file_type in ext_map.items():
            if file_path.endswith(ext):
                return file_type

        return "default"

    def _calculate_ttl(self, file_path: str, stats: Dict) -> Optional[Dict]:
        """
        Calculate optimal TTL based on stats
        Uses OpenAI if enabled, otherwise falls back to rule-based
        """
        total_requests = stats["requests"]

        # Need minimum data points
        if total_requests < 5:
            return None

        if self.use_genai:
            return self._calculate_ttl_with_genai(file_path, stats)
        else:
            return self._calculate_ttl_rule_based(file_path, stats)

    def _calculate_ttl_with_genai(self, file_path: str, stats: Dict) -> Optional[Dict]:
        """
        Use OpenAI GPT to recommend optimal TTL
        """
        try:
            total_requests = stats["requests"]
            cache_hit_ratio = stats["cache_hits"] / total_requests
            file_type = stats["file_type"]
            has_spike = self._detect_spike(stats["request_times"])

            # Prepare context for GPT
            prompt = f"""You are a CDN optimization expert. Analyze this file's cache behavior and recommend an optimal TTL (Time To Live) in seconds.

File: {file_path}
File Type: {file_type}
Total Requests: {total_requests}
Cache Hit Ratio: {cache_hit_ratio:.2%}
Traffic Spike Detected: {has_spike}

Consider:
1. Static files (images, fonts) can have longer TTL (hours/days)
2. Dynamic files (HTML, API) need shorter TTL (minutes)
3. High traffic files benefit from longer TTL to reduce origin load
4. Low hit ratio may indicate TTL is too short
5. Traffic spikes require increased TTL

Respond ONLY with valid JSON in this exact format:
{{
  "recommended_ttl": <seconds as integer>,
  "reason": "<concise explanation>"
}}"""

            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a CDN optimization expert. Always respond with valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=200,
            )

            # Parse GPT response
            response_text = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            result = json.loads(response_text)

            base_ttl = int(result["recommended_ttl"])
            reason = result["reason"] + " 🤖 (AI-optimized)"

            return {
                "file": file_path,
                "recommended_ttl": base_ttl,
                "ttl_human": self._format_ttl(base_ttl),
                "reason": reason,
                "stats": {
                    "total_requests": total_requests,
                    "cache_hit_ratio": f"{cache_hit_ratio:.2%}",
                    "file_type": file_type,
                },
                "timestamp": datetime.utcnow().isoformat(),
                "optimization_method": "genai",
            }

        except Exception as e:
            logger.error(
                f"❌ GenAI TTL calculation failed: {e}. Falling back to rule-based."
            )
            return self._calculate_ttl_rule_based(file_path, stats)

    def _calculate_ttl_rule_based(self, file_path: str, stats: Dict) -> Optional[Dict]:
        """
        Rule-based TTL calculation (fallback method)

        Factors considered:
        1. Request frequency (high frequency = longer TTL)
        2. Cache hit ratio (high ratio = current TTL is good)
        3. File type (static assets = longer TTL)
        4. Traffic spikes (sudden increase = increase TTL)
        """
        total_requests = stats["requests"]
        cache_hit_ratio = stats["cache_hits"] / total_requests
        file_type = stats["file_type"]

        # Start with default TTL for file type
        base_ttl = self.default_ttls.get(file_type, self.default_ttls["default"])

        # Adjust based on request frequency
        if total_requests > 50:
            # High traffic file
            base_ttl = int(base_ttl * 2)
            reason = f"High traffic ({total_requests} requests) - increased TTL for better cache efficiency"
        elif total_requests > 20:
            base_ttl = int(base_ttl * 1.5)
            reason = (
                f"Moderate traffic ({total_requests} requests) - slightly increased TTL"
            )
        else:
            reason = f"Normal traffic ({total_requests} requests) - using standard TTL"

        # Adjust based on cache hit ratio
        if cache_hit_ratio < 0.3:
            # Low hit ratio, might need longer TTL
            base_ttl = int(base_ttl * 1.5)
            reason += f" | Low cache hit ratio ({cache_hit_ratio:.2%}) - increasing TTL"

        # Detect traffic spike
        if self._detect_spike(stats["request_times"]):
            base_ttl = int(base_ttl * 2)
            reason = f"Traffic spike detected - significantly increased TTL to reduce origin load"

        # Format TTL for human readability
        ttl_human = self._format_ttl(base_ttl)

        return {
            "file": file_path,
            "recommended_ttl": base_ttl,
            "ttl_human": ttl_human,
            "reason": reason + " 📊 (Rule-based)",
            "stats": {
                "total_requests": total_requests,
                "cache_hit_ratio": f"{cache_hit_ratio:.2%}",
                "file_type": file_type,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "optimization_method": "rule-based",
        }

    def _detect_spike(self, request_times: List[str]) -> bool:
        """Detect if there's a traffic spike in recent requests"""
        if len(request_times) < 10:
            return False

        # Check last 5 minutes vs previous period
        try:
            now = datetime.utcnow()
            recent_cutoff = now - timedelta(minutes=5)
            previous_cutoff = now - timedelta(minutes=10)

            recent_count = sum(
                1
                for t in request_times
                if datetime.fromisoformat(t.replace("Z", "")) > recent_cutoff
            )
            previous_count = sum(
                1
                for t in request_times
                if previous_cutoff
                < datetime.fromisoformat(t.replace("Z", ""))
                <= recent_cutoff
            )

            # Spike if recent requests are 3x more than previous period
            return recent_count > previous_count * 3
        except:
            return False

    def _format_ttl(self, seconds: int) -> str:
        """Format TTL in human-readable form"""
        if seconds >= 86400:
            return f"{seconds // 86400}d"
        elif seconds >= 3600:
            return f"{seconds // 3600}h"
        elif seconds >= 60:
            return f"{seconds // 60}m"
        else:
            return f"{seconds}s"
