"""
Test for UI Token Tracking Refresh Fix.

This test validates that token tracking is properly refreshed after:
1. OpenRouter model refresh operations
2. Session cost refresh button clicks
"""

import pytest
from pathlib import Path
import re


class TestUIRefreshFix:
    """Test the UI refresh functionality for token tracking"""
    
    def test_model_refresh_calls_token_tracking(self):
        """Test that model refresh operations call refreshTokenTracking()"""
        js_file = Path(__file__).parent.parent / "ui" / "static" / "js" / "app.js"
        content = js_file.read_text()
        
        # Find the loadMainOpenRouterModels function
        function_match = re.search(
            r'async function loadMainOpenRouterModels\(.*?\{(.*?)\n\}',
            content,
            re.DOTALL
        )
        
        assert function_match, "loadMainOpenRouterModels function should exist"
        function_body = function_match.group(1)
        
        # Check that it calls refreshTokenTracking when forceRefresh is true
        # It should call refreshTokenTracking() after successful model loading
        assert "refreshTokenTracking" in function_body, \
            "loadMainOpenRouterModels should call refreshTokenTracking() after successful model load"
    
    def test_session_cost_refresh_calls_token_tracking(self):
        """Test that session cost refresh calls refreshTokenTracking()"""
        js_file = Path(__file__).parent.parent / "ui" / "static" / "js" / "app.js"
        content = js_file.read_text()
        
        # Find the recalculateSessionCost function
        function_match = re.search(
            r'function recalculateSessionCost\(\)\s*\{(.*?)\n\}',
            content,
            re.DOTALL
        )
        
        assert function_match, "recalculateSessionCost function should exist"
        function_body = function_match.group(1)
        
        # Check that it calls refreshTokenTracking to get fresh data from server
        assert "refreshTokenTracking" in function_body, \
            "recalculateSessionCost should call refreshTokenTracking() to get fresh data from server"

    def test_loadOpenRouterModelsEnhanced_refresh_fix(self):
        """Test that loadOpenRouterModelsEnhanced also calls refreshTokenTracking when needed"""
        js_file = Path(__file__).parent.parent / "ui" / "static" / "js" / "app.js"
        content = js_file.read_text()
        
        # Find the loadOpenRouterModelsEnhanced function
        function_match = re.search(
            r'async function loadOpenRouterModelsEnhanced\(.*?\{(.*?)\n\}',
            content,
            re.DOTALL
        )
        
        assert function_match, "loadOpenRouterModelsEnhanced function should exist"
        function_body = function_match.group(1)
        
        # Check that it calls refreshTokenTracking when forceRefresh is true
        assert "refreshTokenTracking" in function_body, \
            "loadOpenRouterModelsEnhanced should call refreshTokenTracking() after successful model load"

if __name__ == "__main__":
    test = TestUIRefreshFix()
    test.test_model_refresh_calls_token_tracking()
    test.test_session_cost_refresh_calls_token_tracking()
    test.test_loadOpenRouterModelsEnhanced_refresh_fix()
    print("All UI refresh tests passed!")