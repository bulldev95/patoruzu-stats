"""
Mock data seed — 2 partidos completos ficticios.
Usa los jugadores y IDs ya existentes en la base.
"""
import sqlite3
import uuid

DB = "patoruzu.db"

# ── Player IDs ─────────────────────────────────────────────────────────────
P = {
    "roldan":     "7c123f35-a25e-4bf2-9651-eedfe60b89d0",   #  1 Prop
    "barrera":    "91971593-2eeb-4b00-a4be-892f5a7c862c",   #  2 Hooker
    "ramos":      "031e8eef-1288-4699-86ca-0a3f628988c5",   #  3 Prop
    "portillo":   "7b52d739-19aa-4506-a808-9d8c089ef67e",   #  4 Lock
    "apraiz_v":   "39425dcf-3a79-4a04-825c-fe4cc7e2e02e",   #  5 Lock
    "murillo":    "a2e253f9-cbc2-496e-b088-6b754000aaed",   #  6 Flanker
    "bellido":    "ad8e6b70-e488-4b51-a0e5-87a67931e203",   #  7 Flanker
    "achigar":    "79cfe046-e1a1-4379-a367-2015ef823c41",   #  8 N8
    "ortiz":      "e3c1a461-d0da-4c3d-8cdc-f9e4db04c8f8",   #  9 SH
    "cardoso":    "ec2a6b26-32a4-444d-bed1-935cafa77938",   # 10 FH
    "sanmartin":  "b785bdc5-e002-4f30-aba1-fafb8ccc2cc5",   # 11 Wing
    "fernandez":  "17b21696-6f50-4ea2-a9c0-339dc642a97f",   # 12 Centre
    "keller":     "769d8cf2-6d68-41e8-a9cc-18706cd19713",   # 13 Centre
    "velazquez":  "87fe7050-1983-4627-b087-ea4591d5bb99",   # 14 Wing
    "lanus_c":    "e4e1e0e2-212b-47d1-9509-752717596ebe",   # 15 FB
    "apraiz_a":   "a3ff3745-cfc5-456e-ac5e-4cfd6ccdc569",   # 16 bench
    "salmeri":    "a559f62f-55e4-43ee-9dfd-6afec7d2ec2f",   # 17 bench
    "striglio":   "762ce667-b9e2-4fee-ac57-81663be67f86",   # 18 bench
    "chludil":    "ba4eb4f7-bbec-47f4-a26e-6cd820ea03e4",   # 19 bench
    "aguilar":    "3832bded-9e79-48e5-a712-4d1d1ccdf890",   # 20 bench
    "griffiths":  "0c5ccb00-600c-4c70-8d19-e0af54f4469b",   # 21 bench
    "ortega":     "3b03d98f-4330-456e-824a-7be4b258b34e",   # 22 bench
    "lanus_w":    "8e786981-6892-49c8-99db-276bf953a21d",   # 23 bench
}

STARTERS = [
    (1, "Prop",      "roldan"),
    (2, "Hooker",    "barrera"),
    (3, "Prop",      "ramos"),
    (4, "Lock",      "portillo"),
    (5, "Lock",      "apraiz_v"),
    (6, "Flanker",   "murillo"),
    (7, "Flanker",   "bellido"),
    (8, "Number 8",  "achigar"),
    (9, "Scrum-half","ortiz"),
    (10,"Fly-half",  "cardoso"),
    (11,"Wing",      "sanmartin"),
    (12,"Centre",    "fernandez"),
    (13,"Centre",    "keller"),
    (14,"Wing",      "velazquez"),
    (15,"Fullback",  "lanus_c"),
]
BENCH = [
    (16, "apraiz_a"),
    (17, "salmeri"),
    (18, "striglio"),
    (19, "chludil"),
    (20, "aguilar"),
    (21, "griffiths"),
    (22, "ortega"),
    (23, "lanus_w"),
]

def ev(match_id, minute, team, type_, result, player_key=None):
    return (str(uuid.uuid4()), match_id, minute, 1, team, type_, result, None,
            P[player_key] if player_key else None, None)

def sub(match_id, minute, out_key, in_key, position):
    return (str(uuid.uuid4()), match_id, minute, P[out_key], P[in_key], position)

def match_players(match_id, minute_outs=None, minute_ins=None):
    """
    minute_outs: {player_key: minute} para titulares que salen
    minute_ins:  {player_key: minute} para suplentes que entran
    """
    minute_outs = minute_outs or {}
    minute_ins  = minute_ins or {}
    rows = []
    for num, pos, key in STARTERS:
        rows.append((str(uuid.uuid4()), match_id, P[key], num, pos, 1, 0, minute_outs.get(key)))
    for num, key in BENCH:
        rows.append((str(uuid.uuid4()), match_id, P[key], num, None, 0, minute_ins.get(key, -1), None))
    return rows


# ═══════════════════════════════════════════════════════════════════════════
# MATCH A: vs Club Atlético del Rosario — 2026-08-22 — Win 34-7
# ═══════════════════════════════════════════════════════════════════════════
MA = str(uuid.uuid4())

events_a = [
    # Patoruzú — tries + conversiones
    ev(MA, 15, "own", "try",        "scored",  "sanmartin"),
    ev(MA, 16, "own", "conversion", "scored",  "cardoso"),
    ev(MA, 28, "own", "try",        "scored",  "keller"),
    ev(MA, 29, "own", "conversion", "scored",  "cardoso"),
    ev(MA, 35, "own", "penal",      "kicked",  "cardoso"),
    ev(MA, 52, "own", "try",        "scored",  "velazquez"),
    ev(MA, 53, "own", "conversion", "scored",  "cardoso"),
    ev(MA, 61, "own", "penal",      "kicked",  "cardoso"),
    ev(MA, 68, "own", "try",        "scored",  "fernandez"),
    ev(MA, 69, "own", "conversion", "scored",  "cardoso"),
    # Patoruzú — tackles
    ev(MA,  7, "own", "tackle",     "positive","barrera"),
    ev(MA, 10, "own", "tackle",     "positive","bellido"),
    ev(MA, 15, "own", "tackle",     "negative","murillo"),
    ev(MA, 18, "own", "tackle",     "positive","achigar"),
    ev(MA, 22, "own", "tackle",     "missed",  "roldan"),
    ev(MA, 23, "own", "tackle",     "positive","bellido"),
    ev(MA, 28, "own", "tackle",     "negative","bellido"),
    ev(MA, 33, "own", "tackle",     "positive","achigar"),
    ev(MA, 40, "own", "tackle",     "positive","murillo"),
    ev(MA, 45, "own", "tackle",     "positive","bellido"),
    ev(MA, 52, "own", "tackle",     "negative","portillo"),
    ev(MA, 58, "own", "tackle",     "positive","murillo"),
    ev(MA, 74, "own", "tackle",     "positive","murillo"),
    ev(MA, 77, "own", "tackle",     "positive","portillo"),
    # Patoruzú — scrums
    ev(MA,  5, "own", "scrum",      "won"),
    ev(MA, 42, "own", "scrum",      "won"),
    ev(MA, 60, "own", "scrum",      "won"),
    ev(MA, 75, "own", "scrum",      "lost"),
    # Patoruzú — lineouts
    ev(MA,  8, "own", "lineout",    "won"),
    ev(MA, 30, "own", "lineout",    "won"),
    ev(MA, 55, "own", "lineout",    "won"),
    ev(MA, 72, "own", "lineout",    "lost"),
    # Patoruzú — kicks
    ev(MA, 20, "own", "kick",       "recovered",    "lanus_c"),
    ev(MA, 38, "own", "kick",       "not_recovered","cardoso"),
    ev(MA, 48, "own", "kick",       "not_recovered","lanus_c"),
    # Patoruzú — perdidas
    ev(MA, 36, "own", "perdida",    "perdida",  "velazquez"),
    # Rival
    ev(MA, 44, "rival", "try",        "scored"),
    ev(MA, 45, "rival", "conversion", "scored"),
]

subs_a = [
    sub(MA, 58, "roldan",  "aguilar",  "Prop"),
    sub(MA, 65, "barrera", "salmeri",  "Hooker"),
]

mplayers_a = match_players(
    MA,
    minute_outs={"roldan": 58, "barrera": 65},
    minute_ins={"aguilar": 58, "salmeri": 65},
)

# ═══════════════════════════════════════════════════════════════════════════
# MATCH B: vs Tala RC Córdoba — 2026-09-05 — Win 21-17 (sufrida)
# ═══════════════════════════════════════════════════════════════════════════
MB = str(uuid.uuid4())

events_b = [
    # Patoruzú — tries + conversiones
    ev(MB,  8, "own", "try",        "scored",  "achigar"),
    ev(MB,  9, "own", "conversion", "scored",  "cardoso"),
    ev(MB, 41, "own", "try",        "scored",  "sanmartin"),
    ev(MB, 42, "own", "conversion", "scored",  "cardoso"),
    ev(MB, 76, "own", "try",        "scored",  "bellido"),   # try ganador
    ev(MB, 77, "own", "conversion", "scored",  "cardoso"),
    # Patoruzú — tackles (partido físico)
    ev(MB,  6, "own", "tackle",     "positive","achigar"),
    ev(MB, 12, "own", "tackle",     "positive","bellido"),
    ev(MB, 14, "own", "tackle",     "negative","murillo"),
    ev(MB, 16, "own", "tackle",     "positive","apraiz_v"),
    ev(MB, 18, "own", "tackle",     "positive","murillo"),
    ev(MB, 21, "own", "tackle",     "positive","portillo"),
    ev(MB, 25, "own", "tackle",     "positive","bellido"),
    ev(MB, 28, "own", "tackle",     "negative","achigar"),
    ev(MB, 30, "own", "tackle",     "missed",  "ramos"),
    ev(MB, 33, "own", "tackle",     "positive","achigar"),
    ev(MB, 38, "own", "tackle",     "positive","velazquez"),
    ev(MB, 40, "own", "tackle",     "negative","bellido"),
    ev(MB, 44, "own", "tackle",     "positive","murillo"),
    ev(MB, 49, "own", "tackle",     "positive","apraiz_v"),
    ev(MB, 53, "own", "tackle",     "positive","bellido"),
    ev(MB, 55, "own", "tackle",     "negative","velazquez"),
    ev(MB, 58, "own", "tackle",     "positive","portillo"),
    ev(MB, 62, "own", "tackle",     "positive","murillo"),
    ev(MB, 69, "own", "tackle",     "positive","bellido"),
    ev(MB, 71, "own", "tackle",     "positive","velazquez"),
    ev(MB, 78, "own", "tackle",     "positive","striglio"),
    # Patoruzú — scrums
    ev(MB,  4, "own", "scrum",      "won"),
    ev(MB, 31, "own", "scrum",      "won"),
    ev(MB, 50, "own", "scrum",      "lost"),
    ev(MB, 72, "own", "scrum",      "won"),
    # Patoruzú — lineouts
    ev(MB, 14, "own", "lineout",    "won"),
    ev(MB, 37, "own", "lineout",    "won"),
    ev(MB, 55, "own", "lineout",    "penal_favor"),
    ev(MB, 68, "own", "lineout",    "won"),
    # Patoruzú — kicks
    ev(MB, 20, "own", "kick",       "not_recovered","cardoso"),
    ev(MB, 45, "own", "kick",       "recovered",    "lanus_c"),
    # Patoruzú — perdidas
    ev(MB, 65, "own", "perdida",    "perdida",  "fernandez"),
    # Rival (penales + try)
    ev(MB, 22, "rival", "penal",      "kicked"),
    ev(MB, 34, "rival", "penal",      "kicked"),
    ev(MB, 47, "rival", "try",        "scored"),
    ev(MB, 57, "rival", "penal",      "kicked"),
    ev(MB, 70, "rival", "penal",      "kicked"),
]

subs_b = [
    sub(MB, 55, "ramos",  "griffiths", "Prop"),
    sub(MB, 60, "murillo","striglio",  "Flanker"),
]

mplayers_b = match_players(
    MB,
    minute_outs={"ramos": 55, "murillo": 60},
    minute_ins={"griffiths": 55, "striglio": 60},
)


# ═══════════════════════════════════════════════════════════════════════════
# CALCULAR STATS DE JUGADORES (incrementales sobre lo que ya hay)
# ═══════════════════════════════════════════════════════════════════════════
def calc_player_deltas(all_events, all_mplayers, final_minute=80):
    """Returns {player_id: {stat: delta}}"""
    from collections import defaultdict
    deltas = defaultdict(lambda: defaultdict(int))

    # Tiempo en cancha
    for row in all_mplayers:
        _id, match_id, player_id, num, pos, is_starter, minute_in, minute_out = row
        if minute_in < 0:
            continue
        out = minute_out if minute_out is not None else final_minute
        minutes = max(0, out - minute_in)
        deltas[player_id]["games_played"] += 1
        deltas[player_id]["minutes_played"] += minutes

    # Eventos propios
    for ev_row in all_events:
        _id, match_id, minute, period, team, type_, result, zone, player_id, notes = ev_row
        if team != "own" or player_id is None:
            continue
        d = deltas[player_id]
        if type_ == "try":
            d["tries"] += 1
        elif type_ == "conversion":
            d["conversions_attempts"] += 1
            if result == "scored":
                d["conversions_scored"] += 1
        elif type_ == "drop":
            d["drops_attempts"] += 1
            if result == "scored":
                d["drops_scored"] += 1
        elif type_ == "penal":
            if result == "kicked":
                d["penals_scored"] += 1
        elif type_ == "tackle":
            d["tackles_total"] += 1
            if result == "positive":
                d["tackles_positive"] += 1
            else:
                d["tackles_missed"] += 1
        elif type_ == "kick":
            d["kicks"] += 1
        elif type_ == "perdida":
            d["turnovers"] += 1
        elif type_ == "lineout":
            d["lineouts"] += 1
        elif type_ == "tarjeta":
            if result == "yellow":
                d["yellow_cards"] += 1
            elif result in ("red", "red_20"):
                d["red_cards"] += 1

    return deltas


# ═══════════════════════════════════════════════════════════════════════════
# INSERT
# ═══════════════════════════════════════════════════════════════════════════
conn = sqlite3.connect(DB)
c = conn.cursor()

# Matches
c.execute("""
    INSERT INTO matches (id, date, rival, competition, venue, score_own, score_rival,
                         period, start_timestamp, accumulated_time, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (MA, "2026-08-22", "Club Atlético del Rosario",
      "Torneo Austral 2026 (Primera División)", "Cancha de Patoruzú",
      34, 7, 2, None, 4800000, "finished"))

c.execute("""
    INSERT INTO matches (id, date, rival, competition, venue, score_own, score_rival,
                         period, start_timestamp, accumulated_time, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (MB, "2026-09-05", "Tala RC Córdoba",
      "Torneo Austral 2026 (Primera División)", "Cancha de Tala",
      21, 17, 2, None, 4800000, "finished"))

# Match players
c.executemany("""
    INSERT INTO match_players (id, match_id, player_id, number, position, is_starter, minute_in, minute_out)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", mplayers_a + mplayers_b)

# Events
c.executemany("""
    INSERT INTO events (id, match_id, minute, period, team, type, result, zone, player_id, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", events_a + events_b)

# Substitutions
c.executemany("""
    INSERT INTO substitutions (id, match_id, minute, player_out_id, player_in_id, position)
    VALUES (?, ?, ?, ?, ?, ?)
""", subs_a + subs_b)

# Player stats
all_events   = events_a + events_b
all_mplayers = mplayers_a + mplayers_b
deltas = calc_player_deltas(all_events, all_mplayers, final_minute=80)

STAT_COLS = [
    "games_played", "minutes_played", "tries", "conversions_attempts", "conversions_scored",
    "drops_attempts", "drops_scored", "penals_scored", "tackles_total", "tackles_positive",
    "tackles_missed", "kicks", "turnovers", "lineouts", "yellow_cards", "red_cards",
]
for player_id, d in deltas.items():
    sets = ", ".join(f"{col} = {col} + ?" for col in STAT_COLS)
    vals = [d.get(col, 0) for col in STAT_COLS] + [player_id]
    c.execute(f"UPDATE players SET {sets} WHERE id = ?", vals)

conn.commit()
conn.close()

print("✓ Mock data insertado:")
print(f"  Match A ({MA[:8]}…): vs Club Atlético del Rosario — 34-7")
print(f"  Match B ({MB[:8]}…): vs Tala RC Córdoba — 21-17")
print(f"  Eventos A: {len(events_a)}, Eventos B: {len(events_b)}")
print(f"  Jugadores con stats actualizados: {len(deltas)}")
