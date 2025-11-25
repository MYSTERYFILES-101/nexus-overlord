# NEXUS OVERLORD v2.0 - Bug-Liste

**Erstellt:** 2025-11-25
**Phase:** 7.1 - Komplett-Test
**Tester:** Claude Code (Automatisiert)

---

## Gefundene Bugs

### BUG #1 - MITTEL

**Beschreibung:** Analysieren-Button gibt "Projekt nicht gefunden" zurück, obwohl Projekt existiert

**Ort:** `/projekt/<id>/analysieren` (Route)

**Fehlerursache:**
```
app.services.database - ERROR - Fehler bei Projekt-Analyse fuer 1: no such column: a.updated_at
```

**Problem:** Die `auftraege` Tabelle hat keine `updated_at` Spalte, aber der Code versucht darauf zuzugreifen.

**Schema aktuell:**
```sql
CREATE TABLE auftraege (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id INTEGER NOT NULL,
    nummer TEXT NOT NULL,
    name TEXT NOT NULL,
    beschreibung TEXT,
    status TEXT DEFAULT 'offen',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    schritte TEXT,
    dateien TEXT,
    technische_details TEXT,
    erfolgs_kriterien TEXT,
    regelwerk TEXT,
    FOREIGN KEY (phase_id) REFERENCES phasen(id)
);
```

**Fix erforderlich:**
- Option A: `updated_at` Spalte zur `auftraege` Tabelle hinzufuegen
- Option B: Query in `get_projekt_analyse()` anpassen (a.updated_at entfernen)

**Schwere:** MITTEL (Feature funktioniert nicht)

**Reproduzierbar:** Ja (100%)

---

### BUG #2 - KLEIN

**Beschreibung:** Auftrag-Status Update gibt Fehler wegen fehlender `updated_at` Spalte

**Ort:** Auftrag-Status Update

**Fehlermeldung:**
```
app.services.database - ERROR - Fehler beim Aktualisieren von Auftrag 2: no such column: updated_at
```

**Problem:** Gleiche Ursache wie BUG #1 - fehlende Spalte

**Schwere:** KLEIN (Auftrag-Status kann nicht aktualisiert werden)

**Reproduzierbar:** Ja

---

## Zusammenfassung

| Bug # | Beschreibung | Schwere | Status |
|-------|--------------|---------|--------|
| 1 | Analysieren-Button fehlerhaft (missing column) | MITTEL | OFFEN |
| 2 | Auftrag-Status Update fehlerhaft | KLEIN | OFFEN |

**Gesamt:** 2 Bugs gefunden
- Kritisch: 0
- Mittel: 1
- Klein: 1

---

## Empfohlener Fix

Eine Migration durchfuehren um `updated_at` zur `auftraege` Tabelle hinzuzufuegen:

```sql
ALTER TABLE auftraege ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;
```

Und einen Trigger erstellen:

```sql
CREATE TRIGGER update_auftraege_timestamp
AFTER UPDATE ON auftraege
BEGIN
    UPDATE auftraege SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```
