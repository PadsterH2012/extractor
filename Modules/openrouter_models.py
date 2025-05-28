"""
OpenRouter Models Utility

This module provides functionality to fetch and manage OpenRouter model lists
for use in dropdown selections and AI provider configuration.
"""

import json
import logging
import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class OpenRouterModels:
    """Utility class for fetching and managing OpenRouter models"""

    def __init__(self, api_key: Optional[str] = None, cache_duration: int = 3600):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.cache_duration = cache_duration  # Cache for 1 hour by default
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://openrouter.ai/api/v1"
        
        # Cache for models
        self._models_cache = None
        self._cache_timestamp = None

    def get_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of available OpenRouter models
        
        Args:
            force_refresh: Force refresh of cached models
            
        Returns:
            List of model dictionaries with id, name, description, etc.
        """
        
        # Check cache first
        if not force_refresh and self._is_cache_valid():
            self.logger.info("📋 Using cached OpenRouter models")
            return self._models_cache

        try:
            self.logger.info("🌐 Fetching OpenRouter models from API")
            models = self._fetch_models_from_api()
            
            # Cache the results
            self._models_cache = models
            self._cache_timestamp = datetime.now()
            
            self.logger.info(f"📋 Fetched {len(models)} OpenRouter models")
            return models
            
        except Exception as e:
            self.logger.error(f"Failed to fetch OpenRouter models: {e}")
            
            # Return cached models if available, otherwise fallback
            if self._models_cache:
                self.logger.warning("Using cached models due to API error")
                return self._models_cache
            else:
                self.logger.warning("Using fallback model list")
                return self._get_fallback_models()

    def _fetch_models_from_api(self) -> List[Dict[str, Any]]:
        """Fetch models from OpenRouter API"""
        
        url = f"{self.base_url}/models"
        headers = {}
        
        # Add API key if available (not required for model listing)
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        models = data.get("data", [])
        
        # Filter and format models for UI use
        formatted_models = []
        for model in models:
            formatted_model = {
                "id": model.get("id", ""),
                "name": model.get("name", model.get("id", "")),
                "description": model.get("description", ""),
                "context_length": model.get("context_length", 0),
                "max_completion_tokens": model.get("max_completion_tokens"),
                "pricing": model.get("pricing", {}),
                "created": model.get("created"),
                "provider": self._extract_provider(model.get("id", "")),
                "model_type": self._determine_model_type(model)
            }
            formatted_models.append(formatted_model)
        
        # Sort models by provider and name
        formatted_models.sort(key=lambda x: (x["provider"], x["name"]))
        
        return formatted_models

    def _extract_provider(self, model_id: str) -> str:
        """Extract provider name from model ID"""
        if "/" in model_id:
            return model_id.split("/")[0]
        return "unknown"

    def _determine_model_type(self, model: Dict[str, Any]) -> str:
        """Determine model type based on model information"""
        model_id = model.get("id", "").lower()
        name = model.get("name", "").lower()
        
        if any(term in model_id or term in name for term in ["gpt-4", "claude-3", "gemini-pro"]):
            return "premium"
        elif any(term in model_id or term in name for term in ["gpt-3.5", "claude-instant"]):
            return "standard"
        else:
            return "basic"

    def _is_cache_valid(self) -> bool:
        """Check if cached models are still valid"""
        if not self._models_cache or not self._cache_timestamp:
            return False
        
        age = datetime.now() - self._cache_timestamp
        return age.total_seconds() < self.cache_duration

    def _get_fallback_models(self) -> List[Dict[str, Any]]:
        """Get fallback model list when API is unavailable"""
        return [
            {
                "id": "anthropic/claude-3.5-sonnet",
                "name": "Claude 3.5 Sonnet",
                "description": "Anthropic's most capable model",
                "context_length": 200000,
                "provider": "anthropic",
                "model_type": "premium"
            },
            {
                "id": "openai/gpt-4o",
                "name": "GPT-4o",
                "description": "OpenAI's flagship multimodal model",
                "context_length": 128000,
                "provider": "openai",
                "model_type": "premium"
            },
            {
                "id": "openai/gpt-4o-mini",
                "name": "GPT-4o Mini",
                "description": "Faster, cheaper GPT-4o",
                "context_length": 128000,
                "provider": "openai",
                "model_type": "standard"
            },
            {
                "id": "google/gemini-pro-1.5",
                "name": "Gemini Pro 1.5",
                "description": "Google's advanced AI model",
                "context_length": 1000000,
                "provider": "google",
                "model_type": "premium"
            },
            {
                "id": "meta-llama/llama-3.1-70b-instruct",
                "name": "Llama 3.1 70B Instruct",
                "description": "Meta's open-source model",
                "context_length": 131072,
                "provider": "meta-llama",
                "model_type": "standard"
            }
        ]

    def get_models_by_provider(self, force_refresh: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """Get models grouped by provider"""
        models = self.get_models(force_refresh)
        
        grouped = {}
        for model in models:
            provider = model["provider"]
            if provider not in grouped:
                grouped[provider] = []
            grouped[provider].append(model)
        
        return grouped

    def get_model_by_id(self, model_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Get specific model by ID"""
        models = self.get_models(force_refresh)
        
        for model in models:
            if model["id"] == model_id:
                return model
        
        return None

    def get_recommended_models(self, use_case: str = "general") -> List[Dict[str, Any]]:
        """Get recommended models for specific use cases"""
        models = self.get_models()
        
        if use_case == "character_identification":
            # Prefer models good at text analysis and JSON output
            preferred_ids = [
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4o",
                "openai/gpt-4o-mini",
                "anthropic/claude-3-haiku"
            ]
        elif use_case == "creative_writing":
            # Prefer models good at creative tasks
            preferred_ids = [
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4o",
                "google/gemini-pro-1.5"
            ]
        else:
            # General use case
            preferred_ids = [
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4o",
                "openai/gpt-4o-mini"
            ]
        
        recommended = []
        for model_id in preferred_ids:
            model = self.get_model_by_id(model_id)
            if model:
                recommended.append(model)
        
        return recommended

    def format_model_for_dropdown(self, model: Dict[str, Any]) -> Dict[str, str]:
        """Format model for UI dropdown display"""
        return {
            "value": model["id"],
            "label": f"{model['name']} ({model['provider']})",
            "description": model.get("description", "")[:100] + "..." if len(model.get("description", "")) > 100 else model.get("description", ""),
            "provider": model["provider"],
            "type": model.get("model_type", "basic")
        }

    def get_dropdown_options(self, group_by_provider: bool = True) -> List[Dict[str, Any]]:
        """Get formatted options for UI dropdown"""
        models = self.get_models()
        
        if group_by_provider:
            grouped = self.get_models_by_provider()
            options = []
            
            for provider, provider_models in grouped.items():
                # Add provider header
                options.append({
                    "type": "header",
                    "label": provider.title(),
                    "value": f"header_{provider}"
                })
                
                # Add models for this provider
                for model in provider_models:
                    formatted = self.format_model_for_dropdown(model)
                    formatted["type"] = "option"
                    options.append(formatted)
            
            return options
        else:
            return [
                {**self.format_model_for_dropdown(model), "type": "option"}
                for model in models
            ]


# Global instance for easy access
openrouter_models = OpenRouterModels()
