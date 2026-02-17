"""
Smart Prefetching Analyzer
Detects patterns in asset requests and recommends prefetch rules
"""
import logging
from typing import List, Dict, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import os
import json
from openai import OpenAI

logger = logging.getLogger(__name__)

class PrefetchAnalyzer:
    """
    Analyzes request sequences to identify prefetch opportunities
    
    Example pattern:
    /index.html → /style.css → /main.js
    
    Recommendation: When /index.html is requested, prefetch /style.css and /main.js
    """
    
    def __init__(self):
        # Track request sequences by client
        self.client_sequences = defaultdict(list)
        
        # Track common patterns
        self.pattern_counts = defaultdict(int)
        
        # Current prefetch rules
        self.prefetch_rules = {}
        
        # Window for sequence analysis (5 seconds)
        self.sequence_window = timedelta(seconds=5)
        
        # Initialize OpenAI client
        self.use_genai = os.getenv('USE_GENAI_PREFETCH', 'true').lower() == 'true'
        api_key = os.getenv('OPENAI_API_KEY')
        
        if self.use_genai and api_key:
            try:
                self.openai_client = OpenAI(api_key=api_key)
                self.model = os.getenv('GENAI_MODEL', 'gpt-3.5-turbo')
                logger.info(f"🤖 Prefetch Analyzer: OpenAI integration enabled with model {self.model}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize OpenAI: {e}. Falling back to rule-based.")
                self.use_genai = False
        else:
            self.use_genai = False
            logger.info("📊 Prefetch Analyzer: Using rule-based analysis")
    
    async def analyze(self, logs: List[Dict]) -> List[Dict]:
        """
        Analyze request logs to detect prefetch patterns
        Uses OpenAI if enabled, otherwise falls back to rule-based
        """
        # Update sequences from logs
        self._update_sequences(logs)
        
        # Detect patterns
        patterns = self._detect_patterns()
        
        if not patterns:
            return []
        
        # Generate prefetch recommendations
        if self.use_genai and len(patterns) > 0:
            return await self._analyze_with_genai(patterns)
        else:
            return self._analyze_rule_based(patterns)
    
    async def _analyze_with_genai(self, patterns: Dict[str, Counter]) -> List[Dict]:
        """
        Use OpenAI GPT to analyze patterns and recommend prefetch rules
        """
        try:
            # Prepare pattern summary for GPT
            pattern_summary = []
            for trigger_file, related_files in list(patterns.items())[:10]:  # Limit to top 10
                if len(related_files) >= 2:
                    pattern_summary.append({
                        'trigger': trigger_file,
                        'followed_by': dict(related_files.most_common(5))
                    })
            
            if not pattern_summary:
                return []
            
            prompt = f"""You are a CDN prefetching expert. Analyze these request patterns and recommend prefetch rules.

Request Patterns (trigger file → frequently requested next):
{json.dumps(pattern_summary, indent=2)}

For each pattern, determine:
1. Which files should be prefetched when the trigger is requested
2. Confidence level (0.0-1.0) based on pattern strength
3. Brief reasoning

Respond ONLY with valid JSON array in this exact format:
[
  {{
    "trigger_file": "<file path>",
    "prefetch_files": ["<file1>", "<file2>"],
    "confidence": <0.0-1.0>,
    "reason": "<concise explanation>"
  }}
]"""

            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a CDN prefetching expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse GPT response
            response_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            recommendations = json.loads(response_text)
            
            # Add metadata
            for rec in recommendations:
                rec['timestamp'] = datetime.utcnow().isoformat()
                rec['reason'] += " 🤖 (AI-optimized)"
                rec['optimization_method'] = 'genai'
            
            logger.info(f"🤖 Generated {len(recommendations)} AI-powered prefetch recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ GenAI prefetch analysis failed: {e}. Falling back to rule-based.")
            return self._analyze_rule_based(patterns)
    
    def _analyze_rule_based(self, patterns: Dict[str, Counter]) -> List[Dict]:
        """
        Rule-based prefetch analysis (fallback method)
        """
        recommendations = []
        
        for trigger_file, related_files in patterns.items():
            if len(related_files) >= 2:  # Need at least 2 related files
                recommendation = {
                    'trigger_file': trigger_file,
                    'prefetch_files': list(related_files.keys())[:5],  # Top 5
                    'confidence': self._calculate_confidence(trigger_file, related_files),
                    'reason': f"Pattern detected: {trigger_file} is frequently followed by {len(related_files)} assets 📊 (Rule-based)",
                    'timestamp': datetime.utcnow().isoformat(),
                    'optimization_method': 'rule-based'
                }
                recommendations.append(recommendation)
        
        return recommendations
    
    def _update_sequences(self, logs: List[Dict]):
        """Track request sequences by client"""
        # Group logs by client IP
        client_logs = defaultdict(list)
        
        for log in logs:
            client_ip = log.get('client_ip', 'unknown')
            client_logs[client_ip].append(log)
        
        # Analyze each client's request sequence
        for client_ip, client_log_list in client_logs.items():
            # Sort by timestamp
            sorted_logs = sorted(client_log_list, key=lambda x: x.get('timestamp', ''))
            
            # Track sequences within time window
            for i in range(len(sorted_logs) - 1):
                current_log = sorted_logs[i]
                next_log = sorted_logs[i + 1]
                
                try:
                    current_time = datetime.fromisoformat(current_log['timestamp'].replace('Z', ''))
                    next_time = datetime.fromisoformat(next_log['timestamp'].replace('Z', ''))
                    
                    # If within window, record the sequence
                    if next_time - current_time <= self.sequence_window:
                        current_path = current_log.get('request_path', '')
                        next_path = next_log.get('request_path', '')
                        
                        if current_path and next_path:
                            pattern = (current_path, next_path)
                            self.pattern_counts[pattern] += 1
                except:
                    continue
    
    def _detect_patterns(self) -> Dict[str, Counter]:
        """
        Detect common request patterns
        Returns: {trigger_file: {related_file: count}}
        """
        patterns = defaultdict(Counter)
        
        # Aggregate patterns
        for (trigger, related), count in self.pattern_counts.items():
            # Only consider patterns seen multiple times
            if count >= 3:
                patterns[trigger][related] = count
        
        return patterns
    
    def _calculate_confidence(self, trigger_file: str, related_files: Counter) -> float:
        """
        Calculate confidence score for prefetch recommendation
        Based on frequency and consistency of pattern
        """
        total_occurrences = sum(related_files.values())
        
        if total_occurrences >= 10:
            confidence = 0.9
        elif total_occurrences >= 5:
            confidence = 0.7
        else:
            confidence = 0.5
        
        return confidence

