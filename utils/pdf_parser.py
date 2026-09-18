import os
import re
import tempfile
import pdfplumber

OWN_TEAM = "PATORUZU R.C. - Chubut"
OWN_TEAM_KEYWORD = "PATORUZU"


def parse_team_sheet(pdf_path: str) -> dict:
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Determine if our team is LOCAL or VISITANTE
    sheet_type = "LOCAL" if "LOCAL" in lines[0] else "VISITANTE"

    # Match info: the line containing the date
    info_line = next(l for l in lines if re.search(r"\d{4}-\d{2}-\d{2}", l))
    date_m = re.search(r"\d{4}-\d{2}-\d{2}", info_line)
    date = date_m.group()
    venue = info_line[: date_m.start()].strip()
    rest = info_line[date_m.end() :].strip()
    rest = re.sub(r"^\d{2}:\d{2}\s+", "", rest)  # strip time "HH:MM "

    # Competition: tournament name ends at the first closing paren
    paren_pos = rest.find(")")
    competition = rest[: paren_pos + 1].strip() if paren_pos != -1 else rest.split("  ")[0].strip()

    # Rival: the teams line contains both team names on one line
    teams_line = next(l for l in lines if OWN_TEAM_KEYWORD in l and "Planilla" not in l)
    rival = teams_line.replace(OWN_TEAM, "").strip()

    # Players: rows matching "{pos} {number} {name} {personal_id}"
    player_re = re.compile(r"^(\d{2})\s+(\d{1,2})\s+(.+?)\s+(\d{7,8})\s*$")
    players = []
    for line in lines:
        m = player_re.match(line)
        if m:
            _, number, name, personal_id = m.groups()
            players.append({
                "number": int(number),
                "name": name.strip(),
                "personal_id": personal_id,
            })

    return {
        "date": date,
        "rival": rival,
        "competition": competition,
        "venue": venue,
        "players": players,
    }


async def save_upload_to_tempfile(file) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        contents = await file.read()
        tmp.write(contents)
        return tmp.name
