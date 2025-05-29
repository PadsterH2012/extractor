#!/usr/bin/env python3
"""
Token Usage Tracking Module
Tracks API calls and token usage across all AI providers during extraction
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import threading

@dataclass
class APICallRecord:
    """Record of a single API call"""
    timestamp: str
    provider: str
    model: str
    operation: str  # 'analyze', 'categorize', 'enhance', etc.
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float = 0.0
    session_id: Optional[str] = None

@dataclass
class SessionUsage:
    """Aggregated usage for a session"""
    session_id: str
    start_time: str
    api_calls: List[APICallRecord] = field(default_factory=list)
    total_tokens: int = 0
    total_cost: float = 0.0
    total_api_calls: int = 0

class TokenUsageTracker:
    """Thread-safe token usage tracker"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._sessions: Dict[str, SessionUsage] = {}
        self._lock = threading.Lock()
    
    def start_session(self, session_id: str) -> None:
        """Start tracking a new session"""
        with self._lock:
            self._sessions[session_id] = SessionUsage(
                session_id=session_id,
                start_time=datetime.now().isoformat()
            )
            self.logger.info(f"📊 Started token tracking for session: {session_id[:8]}")
    
    def record_api_call(self, session_id: str, provider: str, model: str, 
                       operation: str, prompt_tokens: int, completion_tokens: int,
                       cost: float = 0.0) -> None:
        """Record an API call with token usage"""
        total_tokens = prompt_tokens + completion_tokens
        
        record = APICallRecord(
            timestamp=datetime.now().isoformat(),
            provider=provider,
            model=model,
            operation=operation,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            session_id=session_id
        )
        
        with self._lock:
            if session_id not in self._sessions:
                self.start_session(session_id)
            
            session = self._sessions[session_id]
            session.api_calls.append(record)
            session.total_tokens += total_tokens
            session.total_cost += cost
            session.total_api_calls += 1
            
            self.logger.info(f"📊 API call recorded - {provider}/{model}: {total_tokens} tokens (prompt: {prompt_tokens}, completion: {completion_tokens})")
            self.logger.info(f"📊 Session {session_id[:8]} totals: {session.total_api_calls} calls, {session.total_tokens} tokens, ${session.total_cost:.4f}")
    
    def get_session_usage(self, session_id: str) -> Optional[SessionUsage]:
        """Get usage data for a session"""
        with self._lock:
            return self._sessions.get(session_id)
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of session usage"""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return {
                    'session_id': session_id,
                    'found': False,
                    'total_tokens': 0,
                    'total_cost': 0.0,
                    'total_api_calls': 0,
                    'api_calls': []
                }
            
            return {
                'session_id': session_id,
                'found': True,
                'start_time': session.start_time,
                'total_tokens': session.total_tokens,
                'total_cost': session.total_cost,
                'total_api_calls': session.total_api_calls,
                'api_calls': [
                    {
                        'timestamp': call.timestamp,
                        'provider': call.provider,
                        'model': call.model,
                        'operation': call.operation,
                        'tokens': call.total_tokens,
                        'cost': call.cost
                    }
                    for call in session.api_calls
                ]
            }
    
    def clear_session(self, session_id: str) -> None:
        """Clear session data"""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                self.logger.info(f"📊 Cleared token tracking for session: {session_id[:8]}")

    def list_active_sessions(self) -> List[str]:
        """List all active session IDs for debugging"""
        with self._lock:
            return list(self._sessions.keys())

# Global tracker instance
_global_tracker = TokenUsageTracker()

def get_tracker() -> TokenUsageTracker:
    """Get the global token usage tracker"""
    return _global_tracker

def record_openrouter_usage(session_id: str, model: str, operation: str, 
                           response: Any, pricing_data: Optional[Dict] = None) -> None:
    """Helper function to record OpenRouter API usage"""
    if not hasattr(response, 'usage') or not response.usage:
        return
    
    usage = response.usage
    prompt_tokens = usage.prompt_tokens
    completion_tokens = usage.completion_tokens
    
    # Calculate cost if pricing data is available
    cost = 0.0
    if pricing_data and 'prompt' in pricing_data and 'completion' in pricing_data:
        prompt_cost_per_token = float(pricing_data['prompt'])
        completion_cost_per_token = float(pricing_data['completion'])
        cost = (prompt_tokens * prompt_cost_per_token) + (completion_tokens * completion_cost_per_token)
    
    get_tracker().record_api_call(
        session_id=session_id,
        provider='openrouter',
        model=model,
        operation=operation,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost=cost
    )
