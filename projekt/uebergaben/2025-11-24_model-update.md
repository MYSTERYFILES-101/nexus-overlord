# ÜBERGABE - Model-Update (Zwischen-Auftrag 4.2.1)

## Datum & Uhrzeit
**2025-11-24**

## Was wurde gemacht

### Alle KI-Modelle auf neueste Versionen aktualisiert

| Alt | Neu |
|-----|-----|
| google/gemini-2.5-pro-preview-05-06 | google/gemini-3-pro-preview |
| anthropic/claude-sonnet-4-5-20250514 | anthropic/claude-opus-4-5-20251101 |

### Vorteile der neuen Modelle:
- **Gemini 3 Pro**: Verbesserte Reasoning-Fähigkeiten
- **Opus 4.5**: Stärkstes Claude-Modell, bessere Code-Qualität

## Geänderte Dateien

1. **app/services/ai_models.py**
   - MODEL_GEMINI → google/gemini-3-pro-preview
   - MODEL_OPUS (neu) → anthropic/claude-opus-4-5-20251101
   - MODEL_SONNET = Alias für MODEL_OPUS

2. **app/services/openrouter.py**
   - call_sonnet() → ruft jetzt Opus auf
   - call_opus() (neu) → direkter Opus-Aufruf
   - call_gemini() → bereits korrekt

3. **config/settings.py**
   - GEMINI_MODEL aktualisiert
   - OPUS_MODEL (neu)
   - SONNET_MODEL = Alias

4. **.env.example**
   - Kommentare aktualisiert
   - OPUS_MODEL statt SONNET_MODEL

## Abwärtskompatibilität

- `call_sonnet()` funktioniert weiterhin (ruft Opus auf)
- `MODEL_SONNET` ist Alias für `MODEL_OPUS`
- Bestehender Code muss nicht geändert werden

## GitHub Commit

**Commit:** `[4.2.1] Model-IDs auf Gemini 3 Pro + Opus 4.5 aktualisiert`
**Status:** gepusht

## Server

**Status:** Deployed und läuft

## Nächster Auftrag

**4.3 - Button "Fehler"**
