"""
Explainability Engine
Makes CDN decisions transparent and debuggable
"""

import logging
from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime
import os
import json
from openai import OpenAI

logger = logging.getLogger(__name__)


class ExplainabilityEngine:
    """
    Generates human-readable explanations for:
    - Why cache HIT or MISS happened
    - Why a particular edge served the request
    - Why TTL was increased/decreased
    """

    def __init__(self):
        # Store recent explanations (last 1000)
        self.explanations = []
        self.max_explanations = 1000

        # Track first-time requests per file
        self.seen_files = set()

        # Initialize OpenAI client
        self.use_genai = os.getenv("USE_GENAI_EXPLAIN", "true").lower() == "true"
        api_key = os.getenv("OPENAI_API_KEY")

        if self.use_genai and api_key:
            try:
                self.openai_client = OpenAI(api_key=api_key)
                self.model = os.getenv("GENAI_MODEL", "gpt-3.5-turbo")
                logger.info(f"🤖 Explainability Engine: OpenAI integration enabled with model {self.model}")
            except Exception as e:
                logger.warning(
                    f"⚠️ Failed to initialize OpenAI: {e}. Falling back to template-based."
                )
                self.use_genai = False
        else:
            self.use_genai = False
            logger.info("📊 Explainability Engine: Using template-based explanations")

    async def process_logs(self, logs: List[Dict]):
        """Process logs and generate explanations"""
        for log in logs:
            explanation = self._generate_explanation(log)
            self._store_explanation(explanation)

    def _generate_explanation(self, log: Dict) -> Dict:
        """Generate explanation for a single request"""
        request_path = log.get("request_path", "")
        cache_status = log.get("cache_status", "MISS")
        edge_server = log.get("edge_server", "unknown")
        ttl = log.get("ttl", 0)
        client_ip = log.get("client_ip", "unknown")
        timestamp = log.get("timestamp", datetime.utcnow().isoformat())

        if self.use_genai:
            return self._generate_explanation_with_genai(log)
        else:
            return self._generate_explanation_template_based(log)

    def _generate_explanation_with_genai(self, log: Dict) -> Dict:
        """Generate natural language explanation using OpenAI GPT"""
        try:
            request_path = log.get("request_path", "")
            cache_status = log.get("cache_status", "MISS")
            edge_server = log.get("edge_server", "unknown")
            ttl = log.get("ttl", 0)
            client_ip = log.get("client_ip", "unknown")
            timestamp = log.get("timestamp", datetime.utcnow().isoformat())

            is_first_request = request_path not in self.seen_files
            if is_first_request:
                self.seen_files.add(request_path)

            prompt = f"""Explain this CDN request to a technical user in simple terms:

File: {request_path}
Cache Status: {cache_status}
Edge Server: {edge_server}
TTL: {ttl} seconds ({self._format_ttl(ttl)})
Client IP: {client_ip}
First Request: {is_first_request}

Provide 3 concise explanations:
1. Cache behavior (why HIT/MISS)
2. Routing decision (why this edge server)
3. TTL reasoning (why this cache duration)

Respond ONLY with valid JSON:
{{
  "cache": "<explanation>",
  "routing": "<explanation>",
  "ttl": "<explanation>",
  "summary": "<one-line overall summary>"
}}"""

            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a CDN expert explaining cache behavior. Keep explanations concise and technical but clear. Always respond with valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=300,
            )

            # Parse GPT response
            response_text = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            explanations = json.loads(response_text)

            return {
                "request_id": log.get("request_id", ""),
                "request_path": request_path,
                "timestamp": timestamp,
                "edge_server": edge_server,
                "cache_status": cache_status,
                "ttl": ttl,
                "ttl_human": self._format_ttl(ttl),
                "explanations": {
                    "cache": explanations.get("cache", "") + " 🤖",
                    "routing": explanations.get("routing", "") + " 🤖",
                    "ttl": explanations.get("ttl", "") + " 🤖",
                },
                "summary": explanations.get("summary", "") + " 🤖 (AI-generated)",
                "generation_method": "genai",
            }

        except Exception as e:
            logger.error(
                f"❌ GenAI explanation failed: {e}. Falling back to template-based."
            )
            return self._generate_explanation_template_based(log)

    def _generate_explanation_template_based(self, log: Dict) -> Dict:
        """Generate explanation using templates (fallback method)"""
        request_path = log.get("request_path", "")
        cache_status = log.get("cache_status", "MISS")
        edge_server = log.get("edge_server", "unknown")
        ttl = log.get("ttl", 0)
        client_ip = log.get("client_ip", "unknown")
        timestamp = log.get("timestamp", datetime.utcnow().isoformat())

        # Generate cache status explanation
        cache_explanation = self._explain_cache_status(request_path, cache_status)

        # Generate routing explanation
        routing_explanation = self._explain_routing(edge_server, client_ip)

        # Generate TTL explanation
        ttl_explanation = self._explain_ttl(request_path, ttl, cache_status)

        return {
            "request_id": log.get("request_id", ""),
            "request_path": request_path,
            "timestamp": timestamp,
            "edge_server": edge_server,
            "cache_status": cache_status,
            "ttl": ttl,
            "ttl_human": self._format_ttl(ttl),
            "explanations": {
                "cache": cache_explanation,
                "routing": routing_explanation,
                "ttl": ttl_explanation,
            },
            "summary": cache_explanation,  # Main explanation
            "generation_method": "template-based",
        }

    def _explain_cache_status(self, request_path: str, cache_status: str) -> str:
        """Explain why cache HIT or MISS occurred"""
        if cache_status == "HIT":
            return f"Cache HIT: File '{request_path}' was found in edge cache, served from memory (fast!)"

        elif cache_status == "MISS":
            if request_path not in self.seen_files:
                self.seen_files.add(request_path)
                return f"Cache MISS: File '{request_path}' requested for the first time in this region, fetched from origin"
            else:
                return f"Cache MISS: File '{request_path}' not in cache (expired or invalidated), fetched from origin"

        elif cache_status == "EXPIRED":
            return f"Cache EXPIRED: File '{request_path}' was cached but TTL expired, revalidating with origin"

        elif cache_status == "BYPASS":
            return f"Cache BYPASS: File '{request_path}' is marked as non-cacheable, always fetched from origin"

        else:
            return f"Unknown cache status: {cache_status}"

    def _explain_routing(self, edge_server: str, client_ip: str) -> str:
        """Explain why this edge server was selected"""
        explanations = {
            "edge1": "Routed to Edge Server 1 (US East region) - closest to your location",
            "edge2": "Routed to Edge Server 2 (EU West region) - load balanced for optimal performance",
            "edge-us": "Routed to US Edge - geographical routing based on client location",
            "edge-eu": "Routed to EU Edge - geographical routing based on client location",
            "edge-asia": "Routed to Asia Edge - geographical routing based on client location",
        }

        return explanations.get(
            edge_server,
            f"Routed to {edge_server} - load balancer selected based on current traffic",
        )

    def _explain_ttl(self, request_path: str, ttl: int, cache_status: str) -> str:
        """Explain the TTL value"""
        if ttl == 0:
            return "TTL is 0 - file is not cached"

        ttl_human = self._format_ttl(ttl)

        # Determine file type
        file_type = self._detect_file_type(request_path)

        explanations = {
            "image": f"TTL set to {ttl_human} - images are static and safe to cache longer",
            "css": f"TTL set to {ttl_human} - stylesheets change infrequently",
            "js": f"TTL set to {ttl_human} - scripts are versioned and safe to cache",
            "html": f"TTL set to {ttl_human} - HTML may update frequently, shorter cache",
            "font": f"TTL set to {ttl_human} - fonts rarely change, long cache duration",
            "video": f"TTL set to {ttl_human} - video files are large and static",
        }

        base_explanation = explanations.get(
            file_type,
            f"TTL set to {ttl_human} - standard cache duration for this file type",
        )

        # Add AI optimization note if applicable
        if ttl > 3600:  # More than 1 hour
            base_explanation += " (AI-optimized: increased due to high traffic)"

        return base_explanation

    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type from path"""
        ext_map = {
            ".jpg": "image",
            ".jpeg": "image",
            ".png": "image",
            ".gif": "image",
            ".css": "css",
            ".js": "js",
            ".html": "html",
            ".woff": "font",
            ".woff2": "font",
            ".mp4": "video",
            ".webm": "video",
        }

        for ext, file_type in ext_map.items():
            if file_path.endswith(ext):
                return file_type

        return "default"

    def _format_ttl(self, seconds: int) -> str:
        """Format TTL in human-readable form"""
        if seconds >= 86400:
            return f"{seconds // 86400} day(s)"
        elif seconds >= 3600:
            return f"{seconds // 3600} hour(s)"
        elif seconds >= 60:
            return f"{seconds // 60} minute(s)"
        else:
            return f"{seconds} second(s)"

    def _store_explanation(self, explanation: Dict):
        """Store explanation for API access"""
        self.explanations.append(explanation)

        # Keep only recent explanations
        if len(self.explanations) > self.max_explanations:
            self.explanations = self.explanations[-self.max_explanations :]

    def get_explanation(self, request_id: str) -> Optional[Dict]:
        """Retrieve explanation for a specific request"""
        for exp in reversed(self.explanations):
            if exp["request_id"] == request_id:
                return exp
        return None

    def get_recent_explanations(self, limit: int = 10) -> List[Dict]:
        """Get recent explanations"""
        return self.explanations[-limit:]
