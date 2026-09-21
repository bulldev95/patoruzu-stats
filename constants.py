"""Application-wide constants: scoring rules, valid actions, and stat mapping tables."""

SCORE_DELTA: dict[str, dict[str, int]] = {
    "try":        {"any": 5},
    "conversion": {"scored": 2},
    "drop":       {"scored": 3},
    "penal":      {"kicked": 3},
}

VALID_ACTIONS: set[str] = {
    "tackle", "try", "conversion", "drop", "scrum", "lineout",
    "ruck", "maul", "penal", "kick", "perdida", "salida", "tarjeta", "knock_on",
}

PLAYER_STAT_BY_TYPE: dict[str, list[str]] = {
    "try":        ["tries"],
    "conversion": ["conversions_attempts"],
    "drop":       ["drops_attempts"],
    "tackle":     ["tackles_total"],
    "kick":       ["kicks"],
    "perdida":    ["turnovers"],
    "knock_on":   ["knock_ons"],
}

PLAYER_STAT_BY_TYPE_AND_RESULT: dict[tuple[str, str], list[str]] = {
    ("conversion", "scored"):   ["conversions_scored"],
    ("drop",       "scored"):   ["drops_scored"],
    ("penal",      "kicked"):   ["penals_scored"],
    ("tackle",     "positive"): ["tackles_positive"],
    ("tackle",     "negative"): ["tackles_negative"],
    ("tackle",     "missed"):   ["tackles_missed"],
    ("tarjeta",    "yellow"):   ["yellow_cards"],
    ("tarjeta",    "red"):      ["red_cards"],
    ("tarjeta",    "red_20"):   ["red_cards_20min"],
}

TEAM_STAT_BY_TYPE: dict[str, list[str]] = {
    "scrum":   ["scrums"],
    "lineout": ["lineouts"],
    "ruck":    ["rucks"],
    "maul":    ["mauls"],
}

TEAM_STAT_BY_TYPE_AND_RESULT: dict[tuple[str, str], list[str]] = {
    ("scrum",    "won"):    ["scrums_won"],
    ("lineout",  "won"):    ["lineouts_won"],
    ("lineout",  "stolen"): ["lineouts_won"],
    ("ruck",     "won"):    ["rucks_won"],
    ("maul",     "won"):    ["mauls_won"],
}
