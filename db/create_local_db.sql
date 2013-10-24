CREATE TABLE adult_noun_verb_judgements
(
    key INTEGER,
    word_1 TEXT,
    word_2 TEXT,
    similarity REAL,
    revision INTEGER
);

CREATE TABLE "api_keys" ("user_id" INTEGER, "api_key" TEXT);

CREATE TABLE behavior_info 
(
    visit INTEGER,
    code TEXT,
    birthday TEXT,
    age REAL,
    gender INTEGER,
    mcdi_num_words INTEGER,
    mcdi_percentile INTEGER,
    exemplar_solids INTEGER,
    shape_1_green INTEGER,
    shape_2_gray INTEGER,
    color INTEGER,
    material INTEGER,
    color_plus_material INTEGER,
    exemplar_nonsolids INTEGER,
    shape INTEGER,
    color_2 INTEGER,
    material_1_green INTEGER,
    material_2_orange INTEGER,
    color_plus_shape INTEGER,
    shape_matches_nonlinguistic INTEGER,
    notes TEXT,
    coding INTEGER,
    sol_shape_pref INTEGER,
    sol_shape_excl INTEGER,
    sol_shape_pref_plus_excl INTEGER,
    sol_material_pref INTEGER,
    ns_material_pref INTEGER,
    ns_material_excl INTEGER,
    ns_material_pref_plus_excl INTEGER,
    solsh_code INTEGER,
    nonsolmat_code INTEGER,
    liz_method_coding INTEGER,
    solids_shape_1_choice INTEGER,
    solids_shape_2_choice INTEGER,
    solids_color_choice INTEGER,
    solids_material_choice INTEGER,
    solids_color_plus_material_choice INTEGER,
    solid_attention_score INTEGER,
    solid_exclusivity_score INTEGER,
    solid_bias_score INTEGER,
    nonsolid_attention_score INTEGER,
    nonsolid_exclusivity_score INTEGER,
    nonsolid_bias_score INTEGER,
    nonsolid_shape_attention_score INTEGER,
    nonsolid_shape_exclusivity_score INTEGER,
    nonsolid_shape_bias_score INTEGER,
    nonsolids_shape_choice INTEGER,
    nonsolids_color_choice INTEGER,
    nonsolids_material_1_choice INTEGER,
    nonsolids_material_2_choice INTEGER,
    nonsolids_color_plus_shape_choice INTEGER,
    revision INTEGER
);

CREATE TABLE howell_noun_distance
(
    word_1 TEXT,
    word_2 TEXT,
    similarity REAL,
    revision INTEGER
);

CREATE TABLE howell_verb_distance
(
    word_1 TEXT,
    word_2 TEXT,
    similarity REAL,
    revision INTEGER
);

CREATE TABLE ipa_phoneme_distance
(
    word_1 TEXT,
    word_2 TEXT,
    similarity REAL,
    revision INTEGER
);

CREATE TABLE mcdi_formats (human_name TEXT, safe_name TEXT, filename TEXT);

CREATE TABLE parent_forms 
(
    form_id TEXT,
    child_name TEXT,
    parent_email TEXT,
    mcdi_type TEXT,
    child_id INTEGER,
    study_id TEXT,
    study TEXT,
    gender INTEGER,
    birthday TEXT,
    items_excluded INTEGER,
    extra_categories INTEGER,
    languages TEXT,
    num_languages INTEGER,
    hard_of_hearing INTEGER
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
    mcdi_type TEXT,
    hard_of_hearing INTEGER
);

CREATE TABLE "users"
(
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "email" TEXT,
    "password_hash" TEXT,
    "can_enter_data" INTEGER,
    "can_edit_parents" INTEGER,
    "can_access_data" INTEGER,
    "can_change_formats" INTEGER,
    "can_use_api_key" INTEGER,
    "can_admin" INTEGER
);

CREATE TABLE word_grammer_features 
(
    word TEXT,
    count INTEGER,
    mass INTEGER,
    no_grammar_agree INTEGER,
    shape INTEGER,
    mat INTEGER,
    both INTEGER,
    no_dimension_agree INTEGER,
    solid_rigid INTEGER,
    nonsolid INTEGER,
    no_solidity_agree INTEGER,
    revision INTEGER
);

CREATE TABLE word_howell_features 
(
    word TEXT,
    is_large REAL,
    is_heavy REAL,
    is_strong REAL,
    is_fast REAL,
    is_hot REAL,
    is_clean REAL,
    is_tidy REAL,
    is_light REAL,
    is_noisy REAL,
    is_smart REAL,
    is_good REAL,
    is_beautiful REAL,
    is_thick REAL,
    is_hard REAL,
    is_rough REAL,
    is_tall REAL,
    is_long REAL,
    is_scary REAL,
    is_colorful REAL,
    is_black REAL,
    is_blue REAL,
    is_brown REAL,
    is_gold REAL,
    is_green REAL,
    is_grey REAL,
    is_orange REAL,
    is_pink REAL,
    is_purple REAL,
    is_red REAL,
    is_silver REAL,
    is_white REAL,
    is_yellow REAL,
    is_conical REAL,
    is_crooked REAL,
    is_curved REAL,
    is_cylindrical REAL,
    is_flat REAL,
    is_liquid REAL,
    is_rectangular REAL,
    is_round REAL,
    is_solid REAL,
    is_square REAL,
    is_straight REAL,
    is_triangular REAL,
    has_feathers REAL,
    has_scales REAL,
    has_fur_or_hair REAL,
    is_prickly REAL,
    is_sharp REAL,
    is_breakable REAL,
    made_of_china REAL,
    made_of_cloth REAL,
    made_of_leather REAL,
    made_of_metal REAL,
    made_of_plastic REAL,
    made_of_stone REAL,
    made_of_wood REAL,
    climbs REAL,
    crawls REAL,
    flies REAL,
    leaps REAL,
    runs REAL,
    swims REAL,
    breathes REAL,
    drinks REAL,
    eats REAL,
    makes_animal_noise REAL,
    sings REAL,
    talks REAL,
    has_4_legs REAL,
    has_a_beak REAL,
    has_a_door REAL,
    has_a_shell REAL,
    has_eyes REAL,
    has_face REAL,
    has_fins REAL,
    has_handle REAL,
    has_leaves REAL,
    has_legs REAL,
    has_paws REAL,
    has_tail REAL,
    has_teeth REAL,
    has_wheels REAL,
    has_whiskers REAL,
    has_wings REAL,
    is_annoying REAL,
    is_comfortable REAL,
    is_fun REAL,
    is_musical REAL,
    is_scary_2 REAL,
    is_strong_smelling REAL,
    is_young REAL,
    is_old REAL,
    is_comforting REAL,
    is_lovable REAL,
    is_edible REAL,
    is_delicious REAL,
    revision INTEGER
);

CREATE INDEX `snapshot_id_index` ON `snapshot_content` (`snapshot_id` ASC);
