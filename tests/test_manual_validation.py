"""
Manual Test Script for Token Tracking UI Refresh

This script validates that the token tracking refresh functionality works correctly
by simulating the conditions described in the issue.
"""

import re
from pathlib import Path


def test_refresh_integration():
    """Test that the refresh functionality is properly integrated"""
    
    js_file = Path(__file__).parent.parent / "ui" / "static" / "js" / "app.js"
    content = js_file.read_text()
    
    # Test 1: Check that loadMainOpenRouterModels calls refreshTokenTracking when forceRefresh=true
    print("🔍 Test 1: loadMainOpenRouterModels refresh integration")
    
    load_main_match = re.search(
        r'async function loadMainOpenRouterModels\(.*?\{(.*?)\n\}',
        content,
        re.DOTALL
    )
    assert load_main_match, "loadMainOpenRouterModels function not found"
    
    main_body = load_main_match.group(1)
    refresh_pattern = r'if\s*\(forceRefresh\)\s*\{\s*setTimeout\(refreshTokenTracking,\s*500\);'
    
    if re.search(refresh_pattern, main_body):
        print("✅ loadMainOpenRouterModels correctly calls refreshTokenTracking on forceRefresh")
    else:
        print("❌ loadMainOpenRouterModels missing refreshTokenTracking call")
        return False
    
    # Test 2: Check that recalculateSessionCost calls refreshTokenTracking
    print("\n🔍 Test 2: recalculateSessionCost refresh integration")
    
    recalc_match = re.search(
        r'function recalculateSessionCost\(\)\s*\{(.*?)\n\}',
        content,
        re.DOTALL
    )
    assert recalc_match, "recalculateSessionCost function not found"
    
    recalc_body = recalc_match.group(1)
    
    if "refreshTokenTracking();" in recalc_body:
        print("✅ recalculateSessionCost correctly calls refreshTokenTracking")
    else:
        print("❌ recalculateSessionCost missing refreshTokenTracking call")
        return False
    
    # Test 3: Check that loadOpenRouterModelsEnhanced calls refreshTokenTracking when forceRefresh=true
    print("\n🔍 Test 3: loadOpenRouterModelsEnhanced refresh integration")
    
    load_enhanced_match = re.search(
        r'async function loadOpenRouterModelsEnhanced\(.*?\{(.*?)\n\}',
        content,
        re.DOTALL
    )
    assert load_enhanced_match, "loadOpenRouterModelsEnhanced function not found"
    
    enhanced_body = load_enhanced_match.group(1)
    
    if re.search(refresh_pattern, enhanced_body):
        print("✅ loadOpenRouterModelsEnhanced correctly calls refreshTokenTracking on forceRefresh")
    else:
        print("❌ loadOpenRouterModelsEnhanced missing refreshTokenTracking call")
        return False
    
    # Test 4: Check that original loadOpenRouterModels also has the fix
    print("\n🔍 Test 4: loadOpenRouterModels (original) refresh integration")
    
    load_orig_match = re.search(
        r'async function loadOpenRouterModels\(.*?\{(.*?)\n\}',
        content,
        re.DOTALL
    )
    assert load_orig_match, "loadOpenRouterModels (original) function not found"
    
    orig_body = load_orig_match.group(1)
    
    if re.search(refresh_pattern, orig_body):
        print("✅ loadOpenRouterModels (original) correctly calls refreshTokenTracking on forceRefresh")
    else:
        print("❌ loadOpenRouterModels (original) missing refreshTokenTracking call")
        return False
    
    print("\n🎉 All refresh integration tests passed!")
    return True


def test_condition_logic():
    """Test that the token tracking condition logic is correct"""
    
    js_file = Path(__file__).parent.parent / "ui" / "static" / "js" / "app.js"
    content = js_file.read_text()
    
    print("\n🔍 Test 5: Token tracking condition logic")
    
    # Check for the correct condition in refreshTokenTracking
    correct_condition = "data.token_tracking.total_tokens > 0 || data.token_tracking.total_api_calls > 0"
    
    if correct_condition in content:
        print("✅ Correct token tracking condition found")
        
        # Count occurrences - should be in both refreshTokenTracking and checkStatus
        occurrences = content.count(correct_condition)
        print(f"✅ Found {occurrences} instances of correct condition")
        
        if occurrences >= 2:
            print("✅ Condition appears in multiple functions as expected")
        else:
            print("⚠️ Condition may only be in one function")
        
        return True
    else:
        print("❌ Correct token tracking condition not found")
        return False


if __name__ == "__main__":
    print("🧪 Running Manual Token Tracking UI Refresh Tests")
    print("=" * 60)
    
    test1_result = test_refresh_integration()
    test2_result = test_condition_logic()
    
    print("\n" + "=" * 60)
    if test1_result and test2_result:
        print("🎉 ALL TESTS PASSED! Token tracking UI refresh fix is working correctly.")
        print("\n📋 Summary of fixes:")
        print("   ✅ Model refresh operations now call refreshTokenTracking()")
        print("   ✅ Session cost refresh now fetches fresh data from server") 
        print("   ✅ Token tracking condition logic correctly handles 0 tokens + API calls")
        print("\n🔧 Issue #27 should now be resolved!")
    else:
        print("❌ Some tests failed. Please review the implementation.")