"""Database schema definitions for the keiba project."""

RACES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS races (
    race_id VARCHAR(12) NOT NULL UNIQUE,
    place_num VARCHAR(50),
    race_name VARCHAR(100),
    race_condition VARCHAR(50),
    grade VARCHAR(20),
    `rank` INT,
    tousu INT,
    track VARCHAR(10),
    distance INT,
    `condition` VARCHAR(20),
    bias VARCHAR(50),
    ichinuke VARCHAR(20),
    jitenn VARCHAR(20),
    staus VARCHAR(50),
    pace VARCHAR(10),

    PRIMARY KEY (race_id)
);
"""

HORSE_RACE_RESULTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS horse_race_results (
    id INT AUTO_INCREMENT PRIMARY KEY,

    race_id VARCHAR(12) NOT NULL,
    horse_id VARCHAR(20),
    horse_name VARCHAR(100) NOT NULL,

    jockey VARCHAR(100),
    post INT,
    popularity INT,
    tyakujun INT,
    time VARCHAR(20),
    margin VARCHAR(30),
    weight DECIMAL(5,1),
    horse_weight INT,
    weight_change INT,
    first_half DECIMAL(5,2),
    second_half DECIMAL(5,2),
    corners VARCHAR(20),
    huri1 VARCHAR(20),
    corner1 VARCHAR(10),
    corner2 VARCHAR(10),
    corner3 VARCHAR(10),
    corner4 VARCHAR(10),
    corner_position VARCHAR(20),
    time_index_total INT,
    time_index_start INT,
    time_index_run INT,
    time_index_finish INT,
    ana04 VARCHAR(50),
    running_type VARCHAR(50),

    INDEX idx_horse_name (horse_name),
    INDEX idx_race_id (race_id)
);
"""

RACE_FETCH_STATUS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS race_fetch_status (
    id INT AUTO_INCREMENT PRIMARY KEY,

    race_id VARCHAR(12) NOT NULL UNIQUE,
    race_date DATE NOT NULL,

    html_fetched BOOLEAN NOT NULL DEFAULT FALSE,
    parsed BOOLEAN NOT NULL DEFAULT FALSE,
    registered BOOLEAN NOT NULL DEFAULT FALSE,

    error_message TEXT,

    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_status_date (race_date),
    INDEX idx_registered (registered)
);
"""

RACE_CARD_ENTRIES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS race_card_entries (
    race_id VARCHAR(12) NOT NULL,
    race_date DATE NOT NULL,
    frame_number INT,
    horse_number INT NOT NULL,
    horse_id VARCHAR(20),
    horse_name VARCHAR(100) NOT NULL,
    sex_age VARCHAR(20),
    carried_weight DECIMAL(4,1),
    jockey VARCHAR(100),
    trainer_area VARCHAR(30),
    trainer VARCHAR(100),
    horse_weight INT,
    weight_change INT,
    win_odds DECIMAL(7,1),
    popularity INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (race_id, horse_number),
    INDEX idx_race_card_date (race_date),
    INDEX idx_race_card_horse (horse_id)
);
"""