-- Migration 002: Add updated_at column to auftraege table
-- Date: 2025-11-25
-- Auftrag: 7.2 - Bugs beheben
-- Description: Fixes BUG #1 and BUG #2 from Phase 7.1 test

-- Add updated_at column
ALTER TABLE auftraege ADD COLUMN updated_at DATETIME;

-- Initialize with created_at for existing rows
UPDATE auftraege SET updated_at = created_at WHERE updated_at IS NULL;

-- Note: The application code in database.py already sets updated_at = datetime('now')
-- on status updates, so no trigger is needed.
