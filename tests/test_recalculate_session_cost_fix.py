"""
Test for Session Cost Recalculation UI Fix.

This test validates that the recalculateSessionCost() function properly
updates the UI display in all scenarios, including when tokens are 0.
"""

import pytest
import re
from pathlib import Path


class TestRecalculateSessionCostFix:
    """Test the session cost recalculation UI fix"""

    def test_recalculate_always_updates_ui(self):
        """Test that recalculateSessionCost always calls updateSessionTracking"""
        
        js_file = Path(__file__).parent.parent / "ui" / "static" / "js" / "app.js"
        content = js_file.read_text()
        
        # Find the recalculateSessionCost function
        function_match = re.search(
            r'function recalculateSessionCost\(\s*\)\s*\{(.*?)^\}',
            content,
            re.MULTILINE | re.DOTALL
        )
        
        assert function_match, "recalculateSessionCost function should exist"
        function_body = function_match.group(1)
        
        # Check that updateSessionTracking is called
        assert "updateSessionTracking()" in function_body, \
            "recalculateSessionCost should call updateSessionTracking()"
        
        # Parse the function to check the structure
        lines = [line.strip() for line in function_body.strip().split('\n') if line.strip()]
        
        # Find critical lines
        conditional_lines = [i for i, line in enumerate(lines) if 'if (sessionTokens > 0)' in line]
        update_tracking_lines = [i for i, line in enumerate(lines) if 'updateSessionTracking()' in line]
        refresh_tracking_lines = [i for i, line in enumerate(lines) if 'refreshTokenTracking()' in line]
        
        assert len(conditional_lines) == 1, "Should have exactly one sessionTokens > 0 conditional"
        assert len(update_tracking_lines) >= 1, "Should call updateSessionTracking at least once"
        assert len(refresh_tracking_lines) == 1, "Should call refreshTokenTracking exactly once"
        
        conditional_start = conditional_lines[0]
        
        # Find the end of the conditional block
        conditional_end = None
        brace_count = 0
        for i in range(conditional_start, len(lines)):
            line = lines[i]
            if '{' in line:
                brace_count += line.count('{')
            if '}' in line:
                brace_count -= line.count('}')
                if brace_count == 0:
                    conditional_end = i
                    break
        
        assert conditional_end is not None, "Should find end of conditional block"
        
        # Check that updateSessionTracking is called outside the conditional
        outside_update_calls = [line_num for line_num in update_tracking_lines 
                               if line_num < conditional_start or line_num > conditional_end]
        
        assert len(outside_update_calls) >= 1, \
            "updateSessionTracking should be called outside the conditional to always update UI"
        
        print("✅ recalculateSessionCost correctly calls updateSessionTracking outside conditional")

    def test_recalculate_function_structure(self):
        """Test that the recalculateSessionCost function has the correct structure"""
        
        js_file = Path(__file__).parent.parent / "ui" / "static" / "js" / "app.js"
        content = js_file.read_text()
        
        # Find the function
        function_match = re.search(
            r'function recalculateSessionCost\(\s*\)\s*\{(.*?)^\}',
            content,
            re.MULTILINE | re.DOTALL
        )
        
        assert function_match, "recalculateSessionCost function should exist"
        function_body = function_match.group(1)
        
        # Expected structure:
        # 1. Conditional calculation when sessionTokens > 0
        # 2. Always call updateSessionTracking()
        # 3. Always call refreshTokenTracking()
        
        # Check for proper comments
        assert "// Always update the UI display" in function_body or \
               "updateSessionTracking()" in function_body, \
               "Should have updateSessionTracking call"
        
        # Check proper ordering: updateSessionTracking should come before refreshTokenTracking
        update_pos = function_body.find("updateSessionTracking()")
        refresh_pos = function_body.find("refreshTokenTracking()")
        
        assert update_pos != -1, "Should call updateSessionTracking"
        assert refresh_pos != -1, "Should call refreshTokenTracking"
        assert update_pos < refresh_pos, "updateSessionTracking should be called before refreshTokenTracking"
        
        print("✅ recalculateSessionCost has correct structure")

    def test_fix_addresses_issue_scenario(self):
        """Test that the fix addresses the specific issue scenario"""
        
        # The issue scenario:
        # - sessionTokens = 0
        # - sessionApiCalls = 1 (from API call made)
        # - User clicks "Recalculate cost" button
        # - Expected: UI should refresh to show current state
        
        js_file = Path(__file__).parent.parent / "ui" / "static" / "js" / "app.js"
        content = js_file.read_text()
        
        # Find the recalculateSessionCost function
        function_match = re.search(
            r'function recalculateSessionCost\(\s*\)\s*\{(.*?)^\}',
            content,
            re.MULTILINE | re.DOTALL
        )
        
        function_body = function_match.group(1)
        
        # Simulate the scenario: sessionTokens = 0
        # With the OLD code, updateSessionTracking would only be called inside the if block
        # With the NEW code, updateSessionTracking should be called regardless
        
        # Check that updateSessionTracking is not ONLY inside the conditional
        lines = function_body.split('\n')
        
        inside_conditional = False
        update_tracking_outside_conditional = False
        
        for line in lines:
            line = line.strip()
            if 'if (sessionTokens > 0)' in line:
                inside_conditional = True
            elif line == '}' and inside_conditional:
                inside_conditional = False
            elif 'updateSessionTracking()' in line and not inside_conditional:
                update_tracking_outside_conditional = True
        
        assert update_tracking_outside_conditional, \
            "updateSessionTracking should be called outside the conditional to handle the issue scenario"
        
        print("✅ Fix correctly addresses the issue scenario (sessionTokens=0, API calls exist)")


if __name__ == "__main__":
    test = TestRecalculateSessionCostFix()
    test.test_recalculate_always_updates_ui()
    test.test_recalculate_function_structure()
    test.test_fix_addresses_issue_scenario()
    print("All recalculateSessionCost fix tests passed!")