CREATE TABLE "api_keys" ("user_id" INTEGER, "api_key" TEXT);

CREATE TABLE cdi_formats (human_name TEXT, safe_name TEXT, filename TEXT);

CREATE TABLE parent_forms
(
    form_id TEXT,
    child_name TEXT,
    parent_email TEXT,
    cdi_type TEXT,
    child_id INTEGER,
    study_id TEXT,
    study TEXT,
    gender INTEGER,
    birthday TEXT,
    items_excluded INTEGER,
    extra_categories INTEGER,
    languages TEXT,
    num_languages INTEGER,
    hard_of_hearing INTEGER,
    total_num_sessions INTEGER
);

CREATE TABLE percentile_tables
(
    human_name TEXT,
    safe_name TEXT,
    filename TEXT
);

CREATE TABLE presentation_formats
(
    human_name TEXT,
    safe_name TEXT,
    filename TEXT
);

CREATE TABLE snapshot_content
(
    snapshot_id INTEGER,
    word TEXT,
    value INTEGER,
    revision INTEGER
);

CREATE TABLE snapshots
(
    id INTEGER PRIMARY KEY,
    child_id INTEGER,
    study_id TEXT,
    study TEXT,
    gender INTEGER,
    age REAL,
    birthday TEXT,
    session_date TEXT,
    session_num INTEGER,
    total_num_sessions INTEGER,
    words_spoken INTEGER,
    items_excluded INTEGER,
    percentile REAL,
    extra_categories INTEGER,
    revision INTEGER,
    languages TEXT,
    num_languages INTEGER,
    cdi_type TEXT,
    hard_of_hearing INTEGER,
    deleted INTEGER
);

CREATE TABLE users
(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    email TEXT,
    password_hash TEXT,
    can_enter_data INTEGER,
    can_import_data INTEGER,
    can_edit_parents INTEGER,
    can_access_data INTEGER,
    can_change_formats INTEGER,
    can_use_api_key INTEGER,
    can_delete_data INTEGER,
    can_admin INTEGER
);

CREATE INDEX `snapshot_id_index` ON `snapshot_content` (`snapshot_id` ASC);

CREATE TABLE reservation
(
    timestamp TEXT
);

CREATE TABLE consent_settings (
    study TEXT,
    requirement_type INTEGER,
    form_content TEXT,
    other_options TEXT,
    epoch_updated INTEGER
);

CREATE INDEX `consent_settings_study_index` ON `consent_settings` (`study` ASC);

CREATE TABLE consent_filings (
    study TEXT,
    name TEXT,
    child_id TEXT,
    completed TEXT,
    other_options TEXT,
    email TEXT
);

CREATE INDEX `consent_filings_study_index` ON `consent_filings` (`study` ASC);
CREATE INDEX `consent_filings_email_index` ON `consent_filings` (`email` ASC);
