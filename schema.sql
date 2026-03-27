-- ═══════════════════════════════════════════════════════════════
--  CyberSentinel — Database Schema
--  Engine: SQLite 3
-- ═══════════════════════════════════════════════════════════════

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ─── USERS / ANALYSTS ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT    NOT NULL,
    initials      TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT,
    role          TEXT    NOT NULL DEFAULT 'analyst',   -- analyst | senior_analyst | admin | viewer
    department    TEXT,
    is_active     BOOLEAN NOT NULL DEFAULT 1,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login    DATETIME
);

-- ─── INCIDENTS ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS incidents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_ref    TEXT    NOT NULL UNIQUE,            -- INC-XXXX
    title           TEXT    NOT NULL,
    type            TEXT    NOT NULL,                  -- apt | phishing | malware | insider | ransomware | data_exfil | credential_leak | other
    severity        TEXT    NOT NULL,                  -- critical | high | medium | low | info
    status          TEXT    NOT NULL DEFAULT 'open',   -- open | triage | active | contained | under_review | resolved | closed
    source          TEXT,                              -- IDS, Email Gateway, UEBA, etc.
    assigned_to     INTEGER REFERENCES users(id),
    description     TEXT,
    ai_confidence   REAL,                              -- 0.0–1.0
    source_ip       TEXT,
    dest_ip         TEXT,
    affected_host   TEXT,
    tags            TEXT,                              -- JSON array stored as text
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at     DATETIME
);

CREATE INDEX IF NOT EXISTS idx_incidents_severity  ON incidents(severity);
CREATE INDEX IF NOT EXISTS idx_incidents_status    ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_created   ON incidents(created_at);
CREATE INDEX IF NOT EXISTS idx_incidents_assigned  ON incidents(assigned_to);

-- ─── THREAT EVENTS (live feed) ──────────────────────────────────
CREATE TABLE IF NOT EXISTS threat_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id     INTEGER REFERENCES incidents(id) ON DELETE SET NULL,
    event_type      TEXT    NOT NULL,
    severity        TEXT    NOT NULL,
    description     TEXT    NOT NULL,
    source_layer    TEXT,                              -- IDS | Dark Web | NLP | Endpoint | UEBA | SIEM
    source_ip       TEXT,
    dest_ip         TEXT,
    affected_entity TEXT,
    raw_payload     TEXT,                              -- JSON blob
    is_acknowledged BOOLEAN NOT NULL DEFAULT 0,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_severity  ON threat_events(severity);
CREATE INDEX IF NOT EXISTS idx_events_created   ON threat_events(created_at);

-- ─── IOCS (Indicators of Compromise) ────────────────────────────
CREATE TABLE IF NOT EXISTS iocs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id     INTEGER REFERENCES incidents(id) ON DELETE SET NULL,
    ioc_type        TEXT    NOT NULL,                  -- ip | domain | hash | email | url | cve
    value           TEXT    NOT NULL,
    confidence      REAL    DEFAULT 1.0,               -- 0.0–1.0
    threat_actor    TEXT,
    first_seen      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active       BOOLEAN NOT NULL DEFAULT 1,
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_iocs_type  ON iocs(ioc_type);
CREATE INDEX IF NOT EXISTS idx_iocs_value ON iocs(value);

-- ─── DARK WEB LEAKS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dark_web_leaks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id     INTEGER REFERENCES incidents(id) ON DELETE SET NULL,
    source_site     TEXT    NOT NULL,                  -- RaidForums, BreachForums, etc.
    leak_type       TEXT    NOT NULL,                  -- credentials | pii | documents | source_code
    records_count   INTEGER DEFAULT 0,
    severity        TEXT    NOT NULL DEFAULT 'high',
    summary         TEXT,
    tor_url         TEXT,
    is_verified     BOOLEAN NOT NULL DEFAULT 0,
    detected_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ─── CITIZEN COMPLAINTS ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS complaints (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_ref   TEXT    NOT NULL UNIQUE,           -- CNF-YYYY-XXXX
    complainant_name    TEXT NOT NULL,
    complainant_phone   TEXT,
    complainant_email   TEXT,
    description     TEXT    NOT NULL,
    incident_date   DATE,
    ai_category     TEXT,                              -- upi_fraud | phishing | identity_theft | ransomware | social_engineering | other
    ai_severity     TEXT,                              -- critical | high | medium | low
    ai_confidence   REAL,
    submitted_by_user INTEGER REFERENCES users(id),
    linked_incident INTEGER REFERENCES incidents(id),
    assigned_to     INTEGER REFERENCES users(id),
    status          TEXT    NOT NULL DEFAULT 'received', -- received | triaged | investigating | resolved | closed
    resolution_notes TEXT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_complaints_status   ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_category ON complaints(ai_category);

-- ─── AUTH SESSIONS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS auth_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token           TEXT    NOT NULL UNIQUE,
    is_active       BOOLEAN NOT NULL DEFAULT 1,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at      DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_token   ON auth_sessions(token);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id);

-- ─── PLAYBOOKS / SOAR ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS playbooks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    description     TEXT,
    trigger_type    TEXT    NOT NULL,                  -- manual | auto | scheduled
    threat_type     TEXT,
    severity_min    TEXT    DEFAULT 'medium',
    steps           TEXT    NOT NULL,                  -- JSON array of step objects
    is_active       BOOLEAN NOT NULL DEFAULT 1,
    created_by      INTEGER REFERENCES users(id),
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ─── PLAYBOOK EXECUTIONS ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS playbook_executions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    playbook_id     INTEGER NOT NULL REFERENCES playbooks(id),
    incident_id     INTEGER REFERENCES incidents(id),
    triggered_by    TEXT    NOT NULL DEFAULT 'auto',   -- auto | user_id
    status          TEXT    NOT NULL DEFAULT 'running', -- running | success | failed | partial
    steps_completed INTEGER DEFAULT 0,
    steps_total     INTEGER DEFAULT 0,
    log             TEXT,                              -- JSON execution log
    started_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME
);

-- ─── ACTIVITY LOG ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS activity_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_type      TEXT    NOT NULL DEFAULT 'user',   -- user | ai_bot | system
    actor_id        INTEGER,                           -- user id or NULL for bots
    actor_label     TEXT    NOT NULL,                  -- display name
    action          TEXT    NOT NULL,
    entity_type     TEXT,                              -- incident | complaint | ioc | playbook
    entity_id       INTEGER,
    detail          TEXT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_log(created_at);

-- ─── SYSTEM HEALTH METRICS ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS system_health (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    component       TEXT    NOT NULL,                  -- ai_classifier | dark_web_crawler | remediation | forensics | siem
    status          TEXT    NOT NULL DEFAULT 'online', -- online | degraded | offline | busy
    uptime_pct      REAL,
    avg_latency_ms  REAL,
    active_jobs     INTEGER DEFAULT 0,
    events_ingested INTEGER DEFAULT 0,
    recorded_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ─── KPI SNAPSHOTS ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS kpi_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    active_threats  INTEGER DEFAULT 0,
    open_incidents  INTEGER DEFAULT 0,
    systems_healthy_pct REAL DEFAULT 0,
    events_analysed INTEGER DEFAULT 0,
    risk_score      INTEGER DEFAULT 0,
    phishing_risk   REAL DEFAULT 0,
    malware_risk    REAL DEFAULT 0,
    insider_risk    REAL DEFAULT 0,
    ransomware_risk REAL DEFAULT 0,
    snapped_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ─── THREAT VOLUME HOURLY ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS threat_volume_hourly (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    hour_label      TEXT    NOT NULL,                  -- "12am", "2am" etc.
    hour_value      INTEGER NOT NULL,                  -- 0..23
    critical_high   INTEGER DEFAULT 0,
    medium          INTEGER DEFAULT 0,
    low             INTEGER DEFAULT 0,
    recorded_date   DATE    NOT NULL DEFAULT (date('now'))
);

-- ─── TRIGGERS: auto-update updated_at ───────────────────────────
CREATE TRIGGER IF NOT EXISTS trg_incidents_updated
AFTER UPDATE ON incidents
BEGIN
    UPDATE incidents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_complaints_updated
AFTER UPDATE ON complaints
BEGIN
    UPDATE complaints SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
