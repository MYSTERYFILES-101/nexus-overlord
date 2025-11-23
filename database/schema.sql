-- NEXUS OVERLORD v2.0 - Datenbank Schema
-- Erstellt: 2025-11-23
-- 6 Tabellen: projekte, phasen, auftraege, rueckmeldungen, fehler, uebergaben

-- Foreign Keys aktivieren
PRAGMA foreign_keys = ON;

-- ========================================
-- TABELLE: projekte
-- ========================================
CREATE TABLE IF NOT EXISTS projekte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    original_plan TEXT,
    enterprise_plan TEXT,
    bewertung TEXT,
    status TEXT DEFAULT 'erstellt' CHECK(status IN ('erstellt', 'in_arbeit', 'fertig')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- TABELLE: phasen
-- ========================================
CREATE TABLE IF NOT EXISTS phasen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projekt_id INTEGER NOT NULL,
    nummer INTEGER NOT NULL,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'offen' CHECK(status IN ('offen', 'in_arbeit', 'fertig')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (projekt_id) REFERENCES projekte(id) ON DELETE CASCADE
);

-- ========================================
-- TABELLE: auftraege
-- ========================================
CREATE TABLE IF NOT EXISTS auftraege (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id INTEGER NOT NULL,
    nummer TEXT NOT NULL,
    name TEXT NOT NULL,
    beschreibung TEXT,
    status TEXT DEFAULT 'offen' CHECK(status IN ('offen', 'in_arbeit', 'fertig', 'fehler')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (phase_id) REFERENCES phasen(id) ON DELETE CASCADE
);

-- ========================================
-- TABELLE: rueckmeldungen
-- ========================================
CREATE TABLE IF NOT EXISTS rueckmeldungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    auftrag_id INTEGER NOT NULL,
    inhalt TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (auftrag_id) REFERENCES auftraege(id) ON DELETE CASCADE
);

-- ========================================
-- TABELLE: fehler
-- ========================================
CREATE TABLE IF NOT EXISTS fehler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    muster TEXT NOT NULL,
    kategorie TEXT,
    loesung TEXT NOT NULL,
    erfolgsrate REAL DEFAULT 0 CHECK(erfolgsrate >= 0 AND erfolgsrate <= 100),
    anzahl INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- TABELLE: uebergaben
-- ========================================
CREATE TABLE IF NOT EXISTS uebergaben (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    auftrag_id INTEGER,
    datei_pfad TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (auftrag_id) REFERENCES auftraege(id) ON DELETE SET NULL
);

-- ========================================
-- INDICES für Performance
-- ========================================
CREATE INDEX IF NOT EXISTS idx_phasen_projekt ON phasen(projekt_id);
CREATE INDEX IF NOT EXISTS idx_auftraege_phase ON auftraege(phase_id);
CREATE INDEX IF NOT EXISTS idx_rueckmeldungen_auftrag ON rueckmeldungen(auftrag_id);
CREATE INDEX IF NOT EXISTS idx_uebergaben_auftrag ON uebergaben(auftrag_id);
CREATE INDEX IF NOT EXISTS idx_fehler_kategorie ON fehler(kategorie);

-- ========================================
-- TRIGGER für updated_at bei projekte
-- ========================================
CREATE TRIGGER IF NOT EXISTS update_projekte_timestamp
AFTER UPDATE ON projekte
BEGIN
    UPDATE projekte SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
