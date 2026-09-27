-- Wet Wicket match database. Built from Cricsheet by pipeline/ingest.py; the same schema runs in
-- local SQLite and in Cloudflare D1. Ball-by-ball detail is pre-aggregated into JSON columns.

CREATE TABLE IF NOT EXISTS matches (
  id TEXT PRIMARY KEY,               -- Cricsheet match id
  date TEXT NOT NULL,                -- first day
  end_date TEXT,
  season TEXT,
  match_type TEXT NOT NULL,          -- Cricsheet: Test, ODI, T20, IT20, ODM, MDM
  fmt TEXT NOT NULL,                 -- Test, ODI, T20I, T20 league, One-day (other), First-class
  gender TEXT NOT NULL,
  team_type TEXT NOT NULL,
  competition_id TEXT,               -- slug of the event name
  event_name TEXT,
  event_detail TEXT,                 -- "3rd ODI", "Final", "Group B, match 12"
  team1 TEXT NOT NULL,               -- batted first
  team2 TEXT NOT NULL,
  toss_winner TEXT,
  toss_decision TEXT,
  winner TEXT,
  result TEXT,                       -- draw, tie, no result
  method TEXT,                       -- D/L, VJD, Awarded, ...
  margin TEXT,                       -- "6 wickets", "45 runs", "innings and 12 runs"
  outcome_text TEXT,
  venue_id TEXT,
  venue TEXT,                        -- full venue string as Cricsheet gives it
  city TEXT,
  city_known INTEGER,                -- 0 when Cricsheet gave no city and we inferred it
  country TEXT,
  overs INTEGER,
  balls_per_over INTEGER,
  player_of_match TEXT,              -- JSON array of player ids
  rain TEXT,                         -- confirmed, likely, or ''
  rain_reason TEXT,
  rain_stage TEXT,                   -- when rain struck, e.g. 'between/during 2nd innings'
  summary TEXT,                      -- JSON: [{team, runs, wkts, overs, declared}] per innings
  officials TEXT,                    -- JSON
  updated_at TEXT
);
CREATE INDEX IF NOT EXISTS matches_date ON matches (date DESC);
CREATE INDEX IF NOT EXISTS matches_comp ON matches (competition_id, season);
CREATE INDEX IF NOT EXISTS matches_venue ON matches (venue_id, date DESC);
CREATE INDEX IF NOT EXISTS matches_fmt ON matches (fmt, gender, date DESC);

CREATE TABLE IF NOT EXISTS innings (
  match_id TEXT NOT NULL,
  inn INTEGER NOT NULL,              -- 1-based; super overs follow the main innings
  team TEXT NOT NULL,
  runs INTEGER, wkts INTEGER, balls INTEGER,
  extras INTEGER,
  declared INTEGER DEFAULT 0, forfeited INTEGER DEFAULT 0, super_over INTEGER DEFAULT 0,
  target_runs INTEGER, target_overs REAL,
  overs_json TEXT,                   -- JSON: [[over, runs, wkts, cum_runs, cum_wkts], ...]
  fow_json TEXT,                     -- JSON: [[wkt_no, score, over_ball, player_id, player_name], ...]
  partnerships_json TEXT,            -- JSON: [[wkt, runs, balls, bat1_id, bat1_runs, bat2_id, bat2_runs], ...]
  PRIMARY KEY (match_id, inn)
);

CREATE TABLE IF NOT EXISTS batting (
  match_id TEXT NOT NULL, inn INTEGER NOT NULL, pos INTEGER NOT NULL,
  player_id TEXT, name TEXT NOT NULL, team TEXT,
  runs INTEGER, balls INTEGER, fours INTEGER, sixes INTEGER,
  out INTEGER,                        -- 1 dismissed, 0 not out
  how TEXT,                           -- "c Smith b Jones", "not out"
  kind TEXT,
  PRIMARY KEY (match_id, inn, pos)
);
CREATE INDEX IF NOT EXISTS batting_player ON batting (player_id);

CREATE TABLE IF NOT EXISTS bowling (
  match_id TEXT NOT NULL, inn INTEGER NOT NULL, pos INTEGER NOT NULL,
  player_id TEXT, name TEXT NOT NULL, team TEXT,
  balls INTEGER, maidens INTEGER, runs INTEGER, wkts INTEGER,
  wides INTEGER, noballs INTEGER, dots INTEGER,
  PRIMARY KEY (match_id, inn, pos)
);
CREATE INDEX IF NOT EXISTS bowling_player ON bowling (player_id);

CREATE TABLE IF NOT EXISTS match_players (
  match_id TEXT NOT NULL, team TEXT NOT NULL, player_id TEXT NOT NULL, name TEXT NOT NULL,
  PRIMARY KEY (match_id, player_id)
);
CREATE INDEX IF NOT EXISTS match_players_player ON match_players (player_id);

-- From the Cricsheet Register (people.csv, names.csv).
CREATE TABLE IF NOT EXISTS people (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  unique_name TEXT,
  key_cricinfo TEXT,
  key_cricketarchive TEXT,
  key_bcci TEXT,
  key_cricbuzz TEXT,
  keys_json TEXT                      -- every other identifier
);
CREATE TABLE IF NOT EXISTS people_names (
  id TEXT NOT NULL, name TEXT NOT NULL,
  PRIMARY KEY (id, name)
);
CREATE INDEX IF NOT EXISTS people_name ON people (name);

CREATE TABLE IF NOT EXISTS venues (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, city TEXT, country TEXT
);

CREATE TABLE IF NOT EXISTS competitions (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, team_type TEXT, gender TEXT, fmt TEXT
);

CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY, value TEXT
);
