import json
import uuid
import time
import os
from datetime import datetime
from collections import deque
from heuristics import analyze_quality

# Simple in-memory storage for the last 10 requests' error status
_recent_errors = deque(maxlen=10)

class LLMOpsLogger:
    def __init__(self, log_file="logs.jsonl"):
        self.log_file = log_file

    def log(self, log_data: dict):
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_data) + "\n")

# Model pricing mapping (per 1 token)
PRICING = {
    "claude-sonnet-4-20250514": {"prompt": 0.000003, "completion": 0.000015},
    "gpt-4o": {"prompt": 0.000005, "completion": 0.000015},
    "gpt-3.5-turbo": {"prompt": 0.0000005, "completion": 0.0000015}
}

class LLMCallWrapper:
    def __init__(self, client, logger: LLMOpsLogger):
        self.client = client  # The underlying LLM client (mocked or real)
        self.logger = logger
        
    def _check_alert(self):
        """Check if error rate in last 10 requests exceeds 20%."""
        if len(_recent_errors) == 10:
            error_count = sum(_recent_errors)
            error_rate = error_count / 10.0
            if error_rate > 0.20:
                print(f"⚠️ ALERT: High Error Rate Detected! Current rate: {error_rate*100:.1f}%")

    def generate(self, prompt: str, model: str = "gpt-3.5-turbo", user_id: str = "anonymous", route: str = "general", **kwargs):
        """
        Wraps the underlying LLM call to capture observability metrics.
        """
        request_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        start_time = time.time()
        
        # We assume the mock client returns a dict with 'content', 'prompt_tokens', 'completion_tokens', 'time_to_first_token'
        # Or raises an Exception on error.
        response_text = ""
        prompt_tokens = 0
        completion_tokens = 0
        time_to_first_token_ms = 0
        error_msg = None
        quality_flags = []
        
        try:
            # CALL UNDERLYING LLM
            response = self.client.complete(prompt=prompt, model=model, **kwargs)
            
            response_text = response.get("content", "")
            prompt_tokens = response.get("prompt_tokens", len(prompt.split()))
            completion_tokens = response.get("completion_tokens", len(response_text.split()))
            time_to_first_token_ms = response.get("time_to_first_token_ms", 100)
            
            # Apply quality heuristics
            quality_flags = analyze_quality(response_text)
            
            # Record success
            _recent_errors.append(0)
            
        except Exception as e:
            error_msg = str(e)
            # Record failure
            _recent_errors.append(1)
            
        # Stop timer
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Calculate cost
        total_tokens = prompt_tokens + completion_tokens
        
        estimated_cost_usd = 0.0
        if model in PRICING:
            rates = PRICING[model]
            estimated_cost_usd = (prompt_tokens * rates["prompt"]) + (completion_tokens * rates["completion"])

        # Construct log entry
        log_entry = {
            "timestamp": timestamp,
            "request_id": request_id,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost_usd,
            "latency_ms": latency_ms,
            "time_to_first_token_ms": time_to_first_token_ms,
            "error": error_msg,
            "quality_flags": quality_flags,
            "user_id": user_id,
            "route": route
        }
        
        # Write to structured log
        self.logger.log(log_entry)
        
        # Check alerts
        self._check_alert()
        
        if error_msg:
            raise Exception(f"LLM Call Failed: {error_msg}")
            
        return response_text


# --- MOCK CLIENT FOR OFFLINE DEVELOPMENT ---

class MockLLMClient:
    """A minimal mock client for simulating LLM responses without API keys."""
    
    def complete(self, prompt: str, model: str, force_error: bool = False, force_short: bool = False, force_refusal: bool = False, force_repetition: bool = False, force_latency: float = 0.5):
        time.sleep(force_latency)  # Simulate network latency
        
        if force_error:
            raise ValueError("Simulated API Timeout/HTTP 500 Error")
            
        time_to_first_token_ms = int((force_latency * 0.3) * 1000) # Roughly 1/3 of total latency
        
        if force_short:
            content = "OK."
        elif force_refusal:
            content = "I'm sorry, I can't fulfill this request as it goes against my safety guidelines."
        elif force_repetition:
            content = "This is a great idea! This is a great idea! This is a great idea!"
        else:
            content = "This is a comprehensive response simulating a real LLM generation. It contains enough words to pass the too_short heuristic, and does not repeat aggressively. It also does not contain refusal words. It seems that this is working nicely."
            
        # Simplified token counter (1 token ≈ 1 word for mock purposes)
        prompt_tokens = len(prompt.split())
        completion_tokens = len(content.split())
        
        return {
            "content": content,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "time_to_first_token_ms": time_to_first_token_ms
        }
