#!/usr/bin/env python3
"""
Final Integration Test - Verify all group posting features
"""
import sys
import os

print("\n" + "="*70)
print("🔍 FINAL INTEGRATION TEST - GROUP POSTING & BUY BUTTON")
print("="*70 + "\n")

tests_passed = 0
tests_failed = 0

# Test 1: Verify group_poster.py exists and imports
print("TEST 1: Group Poster Module")
print("-" * 70)
try:
    from group_poster import GroupPoster
    print("  ✅ group_poster.py imported successfully")
    print("  ✅ GroupPoster class available")
    tests_passed += 1
except Exception as e:
    print(f"  ❌ Failed to import GroupPoster: {e}")
    tests_failed += 1

# Test 2: Verify sniper_bot integration
print("\nTEST 2: Sniper Bot Integration")
print("-" * 70)
try:
    # Check if sniper_bot has group_poster import
    with open('sniper_bot.py', 'r') as f:
        content = f.read()
        if 'from group_poster import GroupPoster' in content:
            print("  ✅ GroupPoster imported in sniper_bot.py")
            tests_passed += 1
        else:
            print("  ❌ GroupPoster not imported in sniper_bot.py")
            tests_failed += 1
        
        if 'group_poster = GroupPoster(w3)' in content:
            print("  ✅ GroupPoster initialized in sniper_bot.py")
            tests_passed += 1
        else:
            print("  ❌ GroupPoster not initialized")
            tests_failed += 1
        
        if 'group_poster.handle_buy_button_click' in content:
            print("  ✅ Buy button handler registered")
            tests_passed += 1
        else:
            print("  ❌ Buy button handler not registered")
            tests_failed += 1
        
        if 'post_to_group_with_buy_button' in content:
            print("  ✅ Group posting function integrated")
            tests_passed += 1
        else:
            print("  ❌ Group posting function not found")
            tests_failed += 1
except Exception as e:
    print(f"  ❌ Error checking sniper_bot.py: {e}")
    tests_failed += 4

# Test 3: Check environment configuration
print("\nTEST 3: Environment Configuration")
print("-" * 70)
try:
    # Load .env
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
        
        if 'GROUP_CHAT_ID' in env_content:
            print("  ✅ GROUP_CHAT_ID added to .env")
            tests_passed += 1
        else:
            print("  ⚠️  GROUP_CHAT_ID not in .env (add to enable group posting)")
            tests_failed += 1
        
        if 'PRIVATE_KEY' in env_content:
            print("  ✅ PRIVATE_KEY added to .env")
            tests_passed += 1
        else:
            print("  ⚠️  PRIVATE_KEY not in .env (add to enable buy button)")
            tests_failed += 1
    else:
        print("  ❌ .env file not found")
        tests_failed += 2
except Exception as e:
    print(f"  ❌ Error checking .env: {e}")
    tests_failed += 2

# Test 4: Verify GroupPoster methods
print("\nTEST 4: GroupPoster Methods")
print("-" * 70)
try:
    from group_poster import GroupPoster
    gp = GroupPoster()
    
    methods = [
        'format_project_message',
        'get_buy_button',
        'should_post_project',
        'post_to_group',
        'handle_buy_button_click'
    ]
    
    for method in methods:
        if hasattr(gp, method):
            print(f"  ✅ {method}()")
            tests_passed += 1
        else:
            print(f"  ❌ {method}() not found")
            tests_failed += 1
except Exception as e:
    print(f"  ❌ Error checking GroupPoster methods: {e}")
    tests_failed += len(methods)

# Test 5: Security features
print("\nTEST 5: Security Features")
print("-" * 70)
try:
    from group_poster import GroupPoster
    gp = GroupPoster()
    
    if hasattr(gp, 'min_rating_score'):
        score = gp.min_rating_score
        if score >= 70:
            print(f"  ✅ Security filter enabled (minimum score: {score}/100)")
            tests_passed += 1
        else:
            print(f"  ⚠️  Low security filter (score: {score})")
            tests_failed += 1
    else:
        print("  ❌ min_rating_score not found")
        tests_failed += 1
except Exception as e:
    print(f"  ❌ Error checking security features: {e}")
    tests_failed += 1

# Summary
print("\n" + "="*70)
print("📊 TEST RESULTS")
print("="*70)
print(f"✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"📈 Success Rate: {tests_passed}/{tests_passed + tests_failed}")

if tests_failed == 0:
    print("\n✨ ALL INTEGRATION TESTS PASSED! ✨")
    print("\n🚀 Your bot is ready to:")
    print("   1. Scan for new token launches on Base")
    print("   2. Rate projects with security analysis (75+ = post)")
    print("   3. Post good projects to your group")
    print("   4. Execute buys with one click")
    print("   5. Send transaction confirmations")
    print("\n💡 Next step: Add GROUP_CHAT_ID and PRIVATE_KEY to .env")
    print("   Then run: python sniper_bot.py")
    sys.exit(0)
else:
    print("\n⚠️  Some tests failed. Please review the errors above.")
    sys.exit(1)
