-- AEA-10: staff sessions and flags, exactly stage7/staff.md section 3 (repository body: AEA-44).
CREATE TABLE IF NOT EXISTS staff_sessions (
  token_hash TEXT PRIMARY KEY,
  session_id TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('customer','representative','supervisor','owner')),
  role_reset_pending INTEGER NOT NULL DEFAULT 0,
  signed_in_demo TEXT,
  created_real TEXT,
  expires_real TEXT
);
CREATE TABLE IF NOT EXISTS flags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_ref TEXT,
  target TEXT CHECK (target IN ('answer','brief','escalation')),
  message_id TEXT NULL, note TEXT NULL, reason TEXT NULL,
  flagged_by_role TEXT, flagged_at TEXT,
  status TEXT CHECK (status IN ('new','reviewed')),
  reviewed_by_role TEXT NULL, reviewed_note TEXT NULL, reviewed_at TEXT NULL
);
