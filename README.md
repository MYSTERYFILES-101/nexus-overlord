# NEXUS OVERLORD v2.0

KI-Orchestrierungs-Tool für Projektplanung mit Multi-Agent System

## Status
- **Phase:** 1 von 7 - Basis-Struktur
- **Auftrag:** 1.2 - Ordner-Struktur ✅
- **Version:** 2.0.0

## Beschreibung

NEXUS OVERLORD ist ein KI-Orchestrierungs-Tool das:
- Projektpläne erstellt (Multi-Agent mit Gemini 3 Pro + Sonnet 4.5)
- Aufträge generiert für Claude Code
- Fehler löst mit intelligenter Datenbank
- Lückenlose Dokumentation führt
- PDF-Export für komplette Projekt-Dokumentation

## Features

### 3 Hauptkacheln
1. **Neues Projekt** - 6-Phasen Multi-Agent Workflow
2. **Phasen & Aufträge** - Enterprise-Plan in Aufträge aufteilen
3. **Projekt öffnen** - Projekte verwalten und steuern

### 5 Funktions-Buttons
- **Auftrag** - Nächsten Auftrag generieren
- **Fehler** - Fehler analysieren und lösen
- **Analysieren** - Projekt-Status aktualisieren
- **Übergaben** - Dokumentation hochladen
- **Export PDF** - Komplette Dokumentation exportieren

### 2 KI-Modelle
- **Gemini 3 Pro** - Stratege, Feedback, Qualitätsprüfung
- **Sonnet 4.5** - Detailarbeiter, Aufträge, Code-Analyse

## Projektstruktur

```
/home/nexus/nexus-overlord/
├── app/                      # Haupt-Anwendung
│   ├── __init__.py
│   ├── main.py               # Flask Entry Point
│   ├── routes/               # API Routes
│   │   └── __init__.py
│   ├── services/             # KI-Services (Gemini, Sonnet)
│   │   └── __init__.py
│   ├── models/               # Datenbank-Models
│   │   └── __init__.py
│   └── templates/            # HTML Templates
│       └── index.html
├── database/                 # Datenbank
│   ├── schema.sql            # Schema mit 6 Tabellen
│   ├── migrate.py            # Migrations-Script
│   └── nexus.db              # SQLite Datenbank
├── projekt/                  # Projekt-Daten
│   ├── auftraege/            # Generierte Aufträge
│   ├── rueckmeldungen/       # Claude Code Antworten
│   ├── fehler/               # Fehler + Lösungen
│   └── uebergaben/           # Übergabe-Dokumentation
├── static/                   # Frontend Assets
│   ├── css/                  # Stylesheets
│   ├── js/                   # JavaScript
│   └── img/                  # Bilder
├── config/                   # Konfiguration
│   └── settings.py           # App-Einstellungen
├── tests/                    # Tests
│   └── __init__.py
├── docs/                     # Dokumentation
├── .env.example              # Umgebungsvariablen Vorlage
├── requirements.txt          # Python Dependencies
├── .gitignore                # Git Ignore
└── README.md                 # Diese Datei
```

## Installation

### 1. Repository klonen
```bash
git clone https://github.com/MYSTERYFILES-101/nexus-overlord.git
cd nexus-overlord
```

### 2. Virtual Environment erstellen
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows
```

### 3. Dependencies installieren
```bash
pip install -r requirements.txt
```

### 4. Umgebungsvariablen einrichten
```bash
cp .env.example .env
# Bearbeite .env und füge deinen OPENROUTER_API_KEY ein
```

### 5. Datenbank erstellen
```bash
python3 database/migrate.py
```

### 6. Server starten
```bash
python3 app/main.py
```

Die Anwendung ist dann erreichbar unter: `http://localhost:5000`

## Entwicklung

### Datenbank-Schema
6 Tabellen:
- **projekte** - Projekt-Verwaltung
- **phasen** - Phasen-Struktur
- **auftraege** - Auftrags-Verwaltung
- **rueckmeldungen** - Rückmeldungen
- **fehler** - Fehler-Datenbank
- **uebergaben** - Übergabe-Dokumentation

### API-Endpunkte
- `GET /` - Startseite mit 3 Kacheln
- `GET /health` - Health Check

### Tests ausführen
```bash
pytest
```

## Phasenplan

7 Phasen mit insgesamt 27 Aufträgen:

1. **Phase 1: Basis-Struktur** (4 Aufträge) ← Aktuell
2. **Phase 2: Kachel 1 - Projekt erstellen** (5 Aufträge)
3. **Phase 3: Kachel 2 - Phasen & Aufträge** (4 Aufträge)
4. **Phase 4: Kachel 3 - Projekt steuern** (6 Aufträge)
5. **Phase 5: Fehler-Datenbank** (3 Aufträge)
6. **Phase 6: PDF Export** (2 Aufträge)
7. **Phase 7: Testing & Feinschliff** (3 Aufträge)

## Technologie-Stack

- **Backend:** Flask 3.0+
- **Datenbank:** SQLite 3
- **KI APIs:** OpenRouter (Gemini 3 Pro + Sonnet 4.5)
- **Frontend:** HTML, CSS, JavaScript
- **PDF Export:** ReportLab

## Repository

https://github.com/MYSTERYFILES-101/nexus-overlord.git

## Lizenz

Dieses Projekt wurde mit Claude Code erstellt.

---

**NEXUS OVERLORD v2.0** - KI-Orchestrierung auf Enterprise-Niveau
