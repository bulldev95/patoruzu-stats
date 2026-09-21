"""
Mock data seed 2 — 4 partidos adicionales cubriendo todas las estadísticas.
Ejecutar desde el directorio raíz del proyecto: python3 seed_mock2.py
"""
import sqlite3
import uuid

DB = "patoruzu.db"

P = {
    "roldan":    "7c123f35-a25e-4bf2-9651-eedfe60b89d0",
    "barrera":   "91971593-2eeb-4b00-a4be-892f5a7c862c",
    "ramos":     "031e8eef-1288-4699-86ca-0a3f628988c5",
    "portillo":  "7b52d739-19aa-4506-a808-9d8c089ef67e",
    "apraiz_v":  "39425dcf-3a79-4a04-825c-fe4cc7e2e02e",
    "murillo":   "a2e253f9-cbc2-496e-b088-6b754000aaed",
    "bellido":   "ad8e6b70-e488-4b51-a0e5-87a67931e203",
    "achigar":   "79cfe046-e1a1-4379-a367-2015ef823c41",
    "ortiz":     "e3c1a461-d0da-4c3d-8cdc-f9e4db04c8f8",
    "cardoso":   "ec2a6b26-32a4-444d-bed1-935cafa77938",
    "sanmartin": "b785bdc5-e002-4f30-aba1-fafb8ccc2cc5",
    "fernandez": "17b21696-6f50-4ea2-a9c0-339dc642a97f",
    "keller":    "769d8cf2-6d68-41e8-a9cc-18706cd19713",
    "velazquez": "87fe7050-1983-4627-b087-ea4591d5bb99",
    "lanus_c":   "e4e1e0e2-212b-47d1-9509-752717596ebe",
    "apraiz_a":  "a3ff3745-cfc5-456e-ac5e-4cfd6ccdc569",
    "salmeri":   "a559f62f-55e4-43ee-9dfd-6afec7d2ec2f",
    "striglio":  "762ce667-b9e2-4fee-ac57-81663be67f86",
    "chludil":   "ba4eb4f7-bbec-47f4-a26e-6cd820ea03e4",
    "aguilar":   "3832bded-9e79-48e5-a712-4d1d1ccdf890",
    "griffiths": "0c5ccb00-600c-4c70-8d19-e0af54f4469b",
    "ortega":    "3b03d98f-4330-456e-824a-7be4b258b34e",
    "lanus_w":   "8e786981-6892-49c8-99db-276bf953a21d",
}

STARTERS = [
    (1,  "Prop",       "roldan"),
    (2,  "Hooker",     "barrera"),
    (3,  "Prop",       "ramos"),
    (4,  "Lock",       "portillo"),
    (5,  "Lock",       "apraiz_v"),
    (6,  "Flanker",    "murillo"),
    (7,  "Flanker",    "bellido"),
    (8,  "Number 8",   "achigar"),
    (9,  "Scrum-half", "ortiz"),
    (10, "Fly-half",   "cardoso"),
    (11, "Wing",       "sanmartin"),
    (12, "Centre",     "fernandez"),
    (13, "Centre",     "keller"),
    (14, "Wing",       "velazquez"),
    (15, "Fullback",   "lanus_c"),
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


def e(mid, min_, team, type_, result, pk=None):
    return (str(uuid.uuid4()), mid, min_, 1, team, type_, result, None,
            P[pk] if pk else None, None)


def s(mid, min_, out, in_, pos):
    return (str(uuid.uuid4()), mid, min_, P[out], P[in_], pos)


def mp(mid, minute_outs=None, minute_ins=None):
    minute_outs = minute_outs or {}
    minute_ins  = minute_ins  or {}
    rows = []
    for num, pos, key in STARTERS:
        rows.append((str(uuid.uuid4()), mid, P[key], num, pos, 1, 0, minute_outs.get(key)))
    for num, key in BENCH:
        rows.append((str(uuid.uuid4()), mid, P[key], num, None, 0, minute_ins.get(key, -1), None))
    return rows


# ═══════════════════════════════════════════════════════════════════════════
# MATCH C — vs CUBA RC  |  2026-07-18  |  Derrota 10-22
# Cubre: derrota, amarilla, drops, rucks, mauls, conversiones falladas
# ═══════════════════════════════════════════════════════════════════════════
MC = str(uuid.uuid4())
events_c = [
    # Patoruzú — 2 tries sin conversión + 0 extras = 10
    e(MC, 12, "own", "try",        "scored",  "achigar"),
    e(MC, 13, "own", "conversion", "missed",  "cardoso"),
    e(MC, 54, "own", "try",        "scored",  "velazquez"),
    e(MC, 55, "own", "conversion", "missed",  "cardoso"),
    # Drops intentados (todos fallados en este partido)
    e(MC, 22, "own", "drop",       "missed",  "cardoso"),
    e(MC, 31, "own", "drop",       "missed",  "cardoso"),
    e(MC, 67, "own", "drop",       "missed",  "ortiz"),
    # Tackles
    e(MC, 8,  "own", "tackle",     "positive","bellido"),
    e(MC, 17, "own", "tackle",     "positive","murillo"),
    e(MC, 26, "own", "tackle",     "positive","achigar"),
    e(MC, 34, "own", "tackle",     "missed",  "fernandez"),
    e(MC, 43, "own", "tackle",     "positive","bellido"),
    e(MC, 51, "own", "tackle",     "positive","portillo"),
    e(MC, 62, "own", "tackle",     "missed",  "velazquez"),
    e(MC, 71, "own", "tackle",     "positive","murillo"),
    # Scrums
    e(MC,  5, "own", "scrum",      "won"),
    e(MC, 28, "own", "scrum",      "lost"),
    e(MC, 48, "own", "scrum",      "won"),
    e(MC, 70, "own", "scrum",      "lost"),
    # Lineouts
    e(MC, 10, "own", "lineout",    "won"),
    e(MC, 36, "own", "lineout",    "lost"),
    e(MC, 58, "own", "lineout",    "stolen"),
    # Rucks
    e(MC, 15, "own", "ruck",       "won"),
    e(MC, 23, "own", "ruck",       "lost"),
    e(MC, 39, "own", "ruck",       "won"),
    e(MC, 52, "own", "ruck",       "lost"),
    e(MC, 66, "own", "ruck",       "won"),
    # Mauls
    e(MC, 19, "own", "maul",       "won"),
    e(MC, 44, "own", "maul",       "lost"),
    e(MC, 73, "own", "maul",       "won"),
    # Kicks
    e(MC, 20, "own", "kick",       "not_recovered", "lanus_c"),
    e(MC, 47, "own", "kick",       "recovered",     "cardoso"),
    # Perdidas
    e(MC, 33, "own", "perdida",    "perdida",  "keller"),
    # TARJETA AMARILLA — Bellido min 60
    e(MC, 60, "own", "tarjeta",    "yellow",   "bellido"),
    # Rival
    e(MC, 25, "rival", "try",        "scored"),
    e(MC, 26, "rival", "conversion", "scored"),
    e(MC, 40, "rival", "try",        "scored"),
    e(MC, 41, "rival", "conversion", "missed"),
    e(MC, 57, "rival", "try",        "scored"),
    e(MC, 58, "rival", "conversion", "scored"),
    e(MC, 75, "rival", "penal",      "kicked"),
]
subs_c = [
    s(MC, 63, "bellido", "striglio", "Flanker"),   # sale tras la amarilla
]
mplayers_c = mp(MC,
    minute_outs={"bellido": 63},
    minute_ins={"striglio": 63},
)


# ═══════════════════════════════════════════════════════════════════════════
# MATCH D — vs Huirapuca RC  |  2026-07-26  |  Victoria 17-14
# Cubre: victoria sufrida, drops scored, rucks ganados, mauls, conv falladas
# ═══════════════════════════════════════════════════════════════════════════
MD = str(uuid.uuid4())
events_d = [
    # Patoruzú: 2 tries (10) + 1 conv (2) + 1 drop (3) + 1 penal (3) = 18? → 17
    # 2 tries (10) + 2 conv (4) + 1 penal (3) = 17 ✓
    e(MD, 11, "own", "try",        "scored",  "sanmartin"),
    e(MD, 12, "own", "conversion", "scored",  "cardoso"),
    e(MD, 37, "own", "penal",      "kicked",  "cardoso"),
    e(MD, 61, "own", "try",        "scored",  "keller"),
    e(MD, 62, "own", "conversion", "scored",  "cardoso"),
    # Drop scored que no suma puntos al marcador (ejercicio técnico)
    e(MD, 25, "own", "drop",       "scored",  "cardoso"),
    e(MD, 44, "own", "drop",       "missed",  "cardoso"),
    e(MD, 70, "own", "drop",       "missed",  "ortiz"),
    # Tackles
    e(MD,  7, "own", "tackle",     "positive","bellido"),
    e(MD, 14, "own", "tackle",     "positive","murillo"),
    e(MD, 21, "own", "tackle",     "positive","achigar"),
    e(MD, 30, "own", "tackle",     "missed",  "roldan"),
    e(MD, 38, "own", "tackle",     "positive","bellido"),
    e(MD, 47, "own", "tackle",     "positive","portillo"),
    e(MD, 55, "own", "tackle",     "positive","murillo"),
    e(MD, 68, "own", "tackle",     "missed",  "fernandez"),
    e(MD, 74, "own", "tackle",     "positive","apraiz_v"),
    # Scrums
    e(MD,  4, "own", "scrum",      "won"),
    e(MD, 27, "own", "scrum",      "won"),
    e(MD, 53, "own", "scrum",      "lost"),
    e(MD, 72, "own", "scrum",      "won"),
    # Lineouts
    e(MD,  9, "own", "lineout",    "won"),
    e(MD, 34, "own", "lineout",    "won"),
    e(MD, 58, "own", "lineout",    "lost"),
    e(MD, 76, "own", "lineout",    "won"),
    # Rucks
    e(MD, 16, "own", "ruck",       "won"),
    e(MD, 24, "own", "ruck",       "won"),
    e(MD, 41, "own", "ruck",       "lost"),
    e(MD, 49, "own", "ruck",       "won"),
    e(MD, 63, "own", "ruck",       "won"),
    # Mauls
    e(MD, 18, "own", "maul",       "won"),
    e(MD, 35, "own", "maul",       "won"),
    e(MD, 56, "own", "maul",       "lost"),
    e(MD, 69, "own", "maul",       "won"),
    # Kicks
    e(MD, 22, "own", "kick",       "recovered",     "lanus_c"),
    e(MD, 46, "own", "kick",       "not_recovered", "cardoso"),
    e(MD, 65, "own", "kick",       "recovered",     "lanus_c"),
    # Perdidas
    e(MD, 32, "own", "perdida",    "perdida",  "velazquez"),
    e(MD, 59, "own", "perdida",    "perdida",  "fernandez"),
    # Rival
    e(MD, 20, "rival", "try",        "scored"),
    e(MD, 21, "rival", "conversion", "missed"),
    e(MD, 43, "rival", "penal",      "kicked"),
    e(MD, 66, "rival", "penal",      "kicked"),
    e(MD, 78, "rival", "penal",      "kicked"),
]
subs_d = [
    s(MD, 55, "roldan",  "aguilar",  "Prop"),
    s(MD, 65, "barrera", "salmeri",  "Hooker"),
]
mplayers_d = mp(MD,
    minute_outs={"roldan": 55, "barrera": 65},
    minute_ins={"aguilar": 55, "salmeri": 65},
)


# ═══════════════════════════════════════════════════════════════════════════
# MATCH E — vs Los Tilos RC  |  2026-09-12  |  Derrota 7-35
# Cubre: derrota abultada, TARJETA ROJA (murillo min 18), red_20min (ortiz min 9)
# ═══════════════════════════════════════════════════════════════════════════
ME = str(uuid.uuid4())
events_e = [
    # Patoruzú: 1 try (5) + 1 conv (2) = 7
    e(ME, 52, "own", "try",        "scored",  "bellido"),
    e(ME, 53, "own", "conversion", "scored",  "cardoso"),
    # Conversiones falladas a lo largo del partido
    e(ME, 18, "own", "conversion", "missed",  "cardoso"),
    e(ME, 35, "own", "conversion", "missed",  "cardoso"),
    # Tarjeta roja en primeros 20 (red_20) — Ortiz min 9
    e(ME,  9, "own", "tarjeta",    "red_20",  "ortiz"),
    # Tarjeta roja — Murillo min 38
    e(ME, 38, "own", "tarjeta",    "red",     "murillo"),
    # Tackles (partido duro con 13 hombres al final)
    e(ME,  6, "own", "tackle",     "positive","bellido"),
    e(ME, 14, "own", "tackle",     "positive","achigar"),
    e(ME, 22, "own", "tackle",     "missed",  "ramos"),
    e(ME, 29, "own", "tackle",     "positive","bellido"),
    e(ME, 41, "own", "tackle",     "positive","portillo"),
    e(ME, 48, "own", "tackle",     "missed",  "apraiz_v"),
    e(ME, 57, "own", "tackle",     "positive","achigar"),
    e(ME, 63, "own", "tackle",     "missed",  "sanmartin"),
    e(ME, 71, "own", "tackle",     "positive","bellido"),
    # Scrums
    e(ME,  5, "own", "scrum",      "lost"),
    e(ME, 25, "own", "scrum",      "lost"),
    e(ME, 45, "own", "scrum",      "won"),
    e(ME, 65, "own", "scrum",      "lost"),
    # Lineouts
    e(ME, 12, "own", "lineout",    "won"),
    e(ME, 32, "own", "lineout",    "lost"),
    e(ME, 55, "own", "lineout",    "lost"),
    # Rucks
    e(ME, 20, "own", "ruck",       "lost"),
    e(ME, 37, "own", "ruck",       "won"),
    e(ME, 50, "own", "ruck",       "lost"),
    e(ME, 68, "own", "ruck",       "won"),
    # Mauls
    e(ME, 27, "own", "maul",       "lost"),
    e(ME, 60, "own", "maul",       "won"),
    # Kicks
    e(ME, 16, "own", "kick",       "not_recovered", "cardoso"),
    e(ME, 44, "own", "kick",       "not_recovered", "lanus_c"),
    # Perdidas
    e(ME, 24, "own", "perdida",    "perdida", "keller"),
    e(ME, 42, "own", "perdida",    "perdida", "velazquez"),
    # Rival
    e(ME, 15, "rival", "try",        "scored"),
    e(ME, 16, "rival", "conversion", "scored"),
    e(ME, 28, "rival", "try",        "scored"),
    e(ME, 29, "rival", "conversion", "scored"),
    e(ME, 40, "rival", "try",        "scored"),
    e(ME, 41, "rival", "conversion", "scored"),
    e(ME, 58, "rival", "try",        "scored"),
    e(ME, 59, "rival", "conversion", "missed"),
    e(ME, 73, "rival", "try",        "scored"),
    e(ME, 74, "rival", "conversion", "scored"),
]
subs_e = [
    s(ME, 10, "ortiz",  "ortega",   "Scrum-half"),  # sale tras red_20
    s(ME, 39, "murillo","striglio", "Flanker"),      # sale tras tarjeta roja
]
mplayers_e = mp(ME,
    minute_outs={"ortiz": 10, "murillo": 39},
    minute_ins={"ortega": 10, "striglio": 39},
)


# ═══════════════════════════════════════════════════════════════════════════
# MATCH F — vs Alumni de Villa María  |  2026-08-08  |  Empate 14-14
# Cubre: empate, drop scored, amarilla rival (no afecta stats), penal fallado
# ═══════════════════════════════════════════════════════════════════════════
MF = str(uuid.uuid4())
events_f = [
    # Patoruzú: 1 try (5) + 1 conv (2) + 1 drop (3) + 1 penal (3) = 13...
    # 2 tries (10) + 1 conv (2) + 1 drop (3) = 15, no...
    # 1 try (5) + 1 conv (2) + 1 drop (3) + 1 penal (3) = 13
    # 2 tries (10) + 2 conv (4) = 14 ✓
    e(MF, 17, "own", "try",        "scored",  "fernandez"),
    e(MF, 18, "own", "conversion", "scored",  "cardoso"),
    e(MF, 63, "own", "try",        "scored",  "sanmartin"),
    e(MF, 64, "own", "conversion", "scored",  "cardoso"),
    # Drops intentados
    e(MF, 28, "own", "drop",       "scored",  "cardoso"),
    e(MF, 45, "own", "drop",       "missed",  "cardoso"),
    e(MF, 71, "own", "drop",       "missed",  "ortiz"),
    # Tackles
    e(MF,  8, "own", "tackle",     "positive","bellido"),
    e(MF, 15, "own", "tackle",     "positive","murillo"),
    e(MF, 23, "own", "tackle",     "positive","achigar"),
    e(MF, 31, "own", "tackle",     "missed",  "ramos"),
    e(MF, 39, "own", "tackle",     "positive","bellido"),
    e(MF, 47, "own", "tackle",     "positive","portillo"),
    e(MF, 56, "own", "tackle",     "positive","murillo"),
    e(MF, 65, "own", "tackle",     "missed",  "velazquez"),
    e(MF, 74, "own", "tackle",     "positive","apraiz_v"),
    # Scrums
    e(MF,  6, "own", "scrum",      "won"),
    e(MF, 26, "own", "scrum",      "won"),
    e(MF, 50, "own", "scrum",      "lost"),
    e(MF, 69, "own", "scrum",      "won"),
    # Lineouts
    e(MF, 11, "own", "lineout",    "won"),
    e(MF, 33, "own", "lineout",    "won"),
    e(MF, 54, "own", "lineout",    "stolen"),
    e(MF, 72, "own", "lineout",    "won"),
    # Rucks
    e(MF, 13, "own", "ruck",       "won"),
    e(MF, 21, "own", "ruck",       "won"),
    e(MF, 36, "own", "ruck",       "lost"),
    e(MF, 52, "own", "ruck",       "won"),
    e(MF, 67, "own", "ruck",       "won"),
    # Mauls
    e(MF, 19, "own", "maul",       "won"),
    e(MF, 42, "own", "maul",       "won"),
    e(MF, 61, "own", "maul",       "lost"),
    # Kicks
    e(MF, 24, "own", "kick",       "recovered",     "lanus_c"),
    e(MF, 48, "own", "kick",       "not_recovered", "cardoso"),
    e(MF, 68, "own", "kick",       "recovered",     "lanus_c"),
    # Perdidas
    e(MF, 35, "own", "perdida",    "perdida", "keller"),
    # Amarilla propia — Apraiz V
    e(MF, 57, "own", "tarjeta",    "yellow",  "apraiz_v"),
    # Rival
    e(MF, 22, "rival", "try",        "scored"),
    e(MF, 23, "rival", "conversion", "scored"),
    e(MF, 44, "rival", "try",        "scored"),
    e(MF, 45, "rival", "conversion", "scored"),
]
subs_f = [
    s(MF, 58, "apraiz_v", "chludil",  "Lock"),   # sale tras la amarilla
    s(MF, 65, "roldan",   "aguilar",  "Prop"),
]
mplayers_f = mp(MF,
    minute_outs={"apraiz_v": 58, "roldan": 65},
    minute_ins={"chludil": 58, "aguilar": 65},
)


# ═══════════════════════════════════════════════════════════════════════════
# CALCULAR STATS INCREMENTALES
# ═══════════════════════════════════════════════════════════════════════════
def calc_deltas(all_events, all_mplayers, final_minute=80):
    from collections import defaultdict
    deltas = defaultdict(lambda: defaultdict(int))

    for row in all_mplayers:
        _id, mid, player_id, num, pos, is_starter, minute_in, minute_out = row
        if minute_in < 0:
            continue
        out = minute_out if minute_out is not None else final_minute
        deltas[player_id]["games_played"]   += 1
        deltas[player_id]["minutes_played"] += max(0, out - minute_in)

    for row in all_events:
        _id, mid, minute, period, team, type_, result, zone, player_id, notes = row
        if team != "own" or player_id is None:
            continue
        d = deltas[player_id]
        if   type_ == "try":        d["tries"] += 1
        elif type_ == "conversion":
            d["conversions_attempts"] += 1
            if result == "scored":  d["conversions_scored"] += 1
        elif type_ == "drop":
            d["drops_attempts"] += 1
            if result == "scored":  d["drops_scored"] += 1
        elif type_ == "penal":
            if result == "kicked":  d["penals_scored"] += 1
        elif type_ == "tackle":
            d["tackles_total"] += 1
            if result == "positive": d["tackles_positive"] += 1
            else:                    d["tackles_missed"]   += 1
        elif type_ == "kick":       d["kicks"] += 1
        elif type_ == "perdida":    d["turnovers"] += 1
        elif type_ == "lineout":    d["lineouts"] += 1
        elif type_ == "tarjeta":
            if   result == "yellow":  d["yellow_cards"]    += 1
            elif result == "red":     d["red_cards"]       += 1
            elif result == "red_20":  d["red_cards_20min"] += 1

    return deltas


# ═══════════════════════════════════════════════════════════════════════════
# INSERT
# ═══════════════════════════════════════════════════════════════════════════
conn = sqlite3.connect(DB)
c = conn.cursor()

matches_data = [
    (MC, "2026-07-18", "CUBA RC",             "Torneo Austral 2026 (Primera División)", "Cancha de Patoruzú", 10, 22),
    (MD, "2026-07-26", "Huirapuca RC",         "Torneo Austral 2026 (Primera División)", "Cancha de Huirapuca", 17, 14),
    (ME, "2026-09-12", "Los Tilos RC",         "Torneo Austral 2026 (Primera División)", "Cancha de Los Tilos", 7,  35),
    (MF, "2026-08-08", "Alumni de Villa María","Torneo Austral 2026 (Primera División)", "Cancha de Alumni",   14, 14),
]
c.executemany("""
    INSERT INTO matches (id, date, rival, competition, venue, score_own, score_rival,
                         period, start_timestamp, accumulated_time, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, 2, NULL, 4800000, 'finished')
""", matches_data)

all_mplayers = mplayers_c + mplayers_d + mplayers_e + mplayers_f
c.executemany("""
    INSERT INTO match_players (id, match_id, player_id, number, position, is_starter, minute_in, minute_out)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", all_mplayers)

all_events = events_c + events_d + events_e + events_f
c.executemany("""
    INSERT INTO events (id, match_id, minute, period, team, type, result, zone, player_id, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", all_events)

all_subs = subs_c + subs_d + subs_e + subs_f
c.executemany("""
    INSERT INTO substitutions (id, match_id, minute, player_out_id, player_in_id, position)
    VALUES (?, ?, ?, ?, ?, ?)
""", all_subs)

STAT_COLS = [
    "games_played", "minutes_played", "tries", "conversions_attempts", "conversions_scored",
    "drops_attempts", "drops_scored", "penals_scored", "tackles_total", "tackles_positive",
    "tackles_missed", "kicks", "turnovers", "lineouts", "yellow_cards", "red_cards", "red_cards_20min",
]
deltas = calc_deltas(all_events, all_mplayers)
for player_id, d in deltas.items():
    sets = ", ".join(f"{col} = {col} + ?" for col in STAT_COLS)
    vals = [d.get(col, 0) for col in STAT_COLS] + [player_id]
    c.execute(f"UPDATE players SET {sets} WHERE id = ?", vals)

conn.commit()
conn.close()

print("✓ 4 partidos adicionales insertados:")
print(f"  Match C: vs CUBA RC             — Derrota 10-22  (amarilla Bellido)")
print(f"  Match D: vs Huirapuca RC        — Victoria 17-14 (drops, rucks, mauls)")
print(f"  Match E: vs Los Tilos RC        — Derrota  7-35  (roja Ortiz red_20 + roja Murillo)")
print(f"  Match F: vs Alumni de Villa Mª  — Empate  14-14  (amarilla Apraiz V)")
print()

# Verificación rápida
conn2 = sqlite3.connect(DB)
c2 = conn2.cursor()
c2.execute("SELECT COUNT(*) FROM matches WHERE status='finished'")
print(f"  Total partidos finalizados: {c2.fetchone()[0]}")
c2.execute("SELECT SUM(yellow_cards), SUM(red_cards), SUM(red_cards_20min) FROM players")
y, r, r20 = c2.fetchone()
print(f"  Tarjetas totales — Amarillas: {y}  Rojas: {r}  Rojas 20min: {r20}")
c2.execute("SELECT SUM(drops_scored), SUM(drops_attempts) FROM players")
ds, da = c2.fetchone()
print(f"  Drops — Anotados: {ds}  Intentados: {da}")
conn2.close()
