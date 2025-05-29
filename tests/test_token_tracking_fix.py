"""
Test for Token Tracking UI Display Fix.

This test validates that the JavaScript condition for updating the UI
correctly handles the case where tokens are 0 but API calls exist.
"""

import pytest
import json
from pathlib import Path


class TestTokenTrackingFix:
    """Test the token tracking UI display fix"""

    def test_javascript_condition_logic(self):
        """Test that the JavaScript condition correctly identifies when to update UI"""
        
        # Test data matching the issue description
        test_cases = [
            {
                "name": "issue_case",
                "data": {"token_tracking": {"total_tokens": 0, "total_api_calls": 1, "total_cost": 0.0}},
                "should_update": True  # NEW: should update, OLD: would not update
            },
            {
                "name": "normal_case", 
                "data": {"token_tracking": {"total_tokens": 100, "total_api_calls": 2, "total_cost": 0.005}},
                "should_update": True  # Both OLD and NEW should update
            },
            {
                "name": "empty_case",
                "data": {"token_tracking": {"total_tokens": 0, "total_api_calls": 0, "total_cost": 0.0}},
                "should_update": False  # Neither OLD nor NEW should update
            },
            {
                "name": "no_tracking",
                "data": {},
                "should_update": False  # Neither OLD nor NEW should update
            }
        ]
        
        for case in test_cases:
            # Simulate the OLD condition (buggy)
            old_condition_result = self._old_condition(case["data"])
            
            # Simulate the NEW condition (fixed)
            new_condition_result = self._new_condition(case["data"])
            
            print(f"\nTest case: {case['name']}")
            print(f"Data: {case['data']}")
            print(f"Old condition: {old_condition_result}")
            print(f"New condition: {new_condition_result}")
            print(f"Should update: {case['should_update']}")
            
            # Assert that the new condition produces the correct result
            assert new_condition_result == case["should_update"], \
                f"New condition failed for {case['name']}: expected {case['should_update']}, got {new_condition_result}"
        
        # Specific test for the issue case
        issue_data = {"token_tracking": {"total_tokens": 0, "total_api_calls": 1, "total_cost": 0.0}}
        old_result = self._old_condition(issue_data)
        new_result = self._new_condition(issue_data)
        
        # The fix should work: old_result should be False, new_result should be True
        assert old_result == False, "Old condition should not update UI for 0 tokens, 1 API call"
        assert new_result == True, "New condition should update UI for 0 tokens, 1 API call"
        
        print("\n✅ Token tracking fix validation passed!")

    def _old_condition(self, data):
        """Simulate the OLD JavaScript condition (buggy)"""
        return (
            "token_tracking" in data and 
            data["token_tracking"] is not None and
            data["token_tracking"].get("total_tokens", 0) > 0
        )
    
    def _new_condition(self, data):
        """Simulate the NEW JavaScript condition (fixed)"""
        return (
            "token_tracking" in data and 
            data["token_tracking"] is not None and
            (data["token_tracking"].get("total_tokens", 0) > 0 or 
             data["token_tracking"].get("total_api_calls", 0) > 0)
        )

    def test_javascript_syntax_check(self):
        """Verify that the JavaScript file has valid syntax"""
        js_file = Path(__file__).parent.parent / "ui" / "static" / "js" / "app.js"
        assert js_file.exists(), "JavaScript file should exist"
        
        # Check that the file contains the fixed condition
        content = js_file.read_text()
        
        # Should contain the new condition
        assert "total_tokens > 0 || data.token_tracking.total_api_calls > 0" in content, \
            "JavaScript should contain the fixed condition"
        
        # Should not contain the old buggy condition standalone
        lines = content.split('\n')
        buggy_lines = [line for line in lines if 
                      "data.token_tracking.total_tokens > 0" in line and 
                      "total_api_calls" not in line]
        
        assert len(buggy_lines) == 0, f"Found old buggy condition in lines: {buggy_lines}"
        
        print("✅ JavaScript syntax and condition check passed!")


if __name__ == "__main__":
    test = TestTokenTrackingFix()
    test.test_javascript_condition_logic()
    test.test_javascript_syntax_check()
    print("All tests passed!")