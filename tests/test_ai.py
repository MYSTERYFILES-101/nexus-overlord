"""
NEXUS OVERLORD v2.0 - AI Models Test
Test-Script für Gemini 3 Pro und Claude Opus 4.5
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.ai_models import call_gemini, call_sonnet, MODEL_GEMINI, MODEL_SONNET
from app.services.openrouter import test_connection


def test_openrouter_connection():
    """Test 1: OpenRouter API Connection"""
    print("=" * 60)
    print("TEST 1: OpenRouter API Connection")
    print("=" * 60)

    try:
        result = test_connection()
        if result:
            print("✅ Connection successful!")
            return True
        else:
            print("❌ Connection failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_gemini():
    """Test 2: Gemini 3 Pro"""
    print("\n" + "=" * 60)
    print("TEST 2: Gemini 3 Pro (Stratege)")
    print("=" * 60)
    print(f"Model: {MODEL_GEMINI}")
    print()

    try:
        prompt = "Sage 'Hallo von Gemini 3 Pro!' und erkläre in einem Satz deine Rolle als Stratege."

        print("Prompt:", prompt)
        print("\nWarte auf Antwort...")

        response = call_gemini(prompt, max_tokens=100)

        print("\n✅ Antwort von Gemini 3 Pro:")
        print("-" * 60)
        print(response)
        print("-" * 60)
        return True

    except Exception as e:
        print(f"\n❌ Fehler bei Gemini: {str(e)}")
        return False


def test_sonnet():
    """Test 3: Claude Opus 4.5"""
    print("\n" + "=" * 60)
    print("TEST 3: Claude Opus 4.5 (Detailarbeiter)")
    print("=" * 60)
    print(f"Model: {MODEL_SONNET}")
    print()

    try:
        prompt = "Sage 'Hallo von Opus 4.5!' und erkläre in einem Satz deine Rolle als Detailarbeiter."

        print("Prompt:", prompt)
        print("\nWarte auf Antwort...")

        response = call_sonnet(prompt, max_tokens=100)

        print("\n✅ Antwort von Opus 4.5:")
        print("-" * 60)
        print(response)
        print("-" * 60)
        return True

    except Exception as e:
        print(f"\n❌ Fehler bei Opus: {str(e)}")
        return False


def test_with_system_prompt():
    """Test 4: Mit System-Prompt"""
    print("\n" + "=" * 60)
    print("TEST 4: System-Prompt Test (Gemini)")
    print("=" * 60)

    try:
        system = "Du bist ein kritischer Reviewer. Gib konstruktives Feedback."
        prompt = "Was hältst du von diesem Test-Setup?"

        print(f"System: {system}")
        print(f"Prompt: {prompt}")
        print("\nWarte auf Antwort...")

        response = call_gemini(prompt, system=system, max_tokens=150)

        print("\n✅ Antwort mit System-Prompt:")
        print("-" * 60)
        print(response)
        print("-" * 60)
        return True

    except Exception as e:
        print(f"\n❌ Fehler: {str(e)}")
        return False


def main():
    """Führe alle Tests aus"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "NEXUS OVERLORD v2.0 - AI TESTS" + " " * 17 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    results = []

    # Test 1: Connection
    results.append(("Connection Test", test_openrouter_connection()))

    # Test 2: Gemini
    results.append(("Gemini 3 Pro", test_gemini()))

    # Test 3: Opus
    results.append(("Opus 4.5", test_sonnet()))

    # Test 4: System Prompt
    results.append(("System Prompt", test_with_system_prompt()))

    # Ergebnisse
    print("\n" + "=" * 60)
    print("TEST ERGEBNISSE")
    print("=" * 60)

    passed = 0
    failed = 0

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:30s} {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"Gesamt: {len(results)} Tests | ✅ {passed} Passed | ❌ {failed} Failed")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 Alle Tests bestanden!")
        return 0
    else:
        print(f"\n⚠️  {failed} Test(s) fehlgeschlagen!")
        return 1


if __name__ == "__main__":
    exit(main())
