import os
import json
import pandas as pd
import re
import math

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(BASE_DIR, "demo-nfl-test_all (10).json")

with open(path, "r") as f:
    data = json.load(f)

participants = data if isinstance(data, list) else data.get("participants") or [data]

def normalize_qname(component_name: str):
    if not component_name or component_name in ("introduction", "end"):
        return None
    return component_name

def parse_qname(qname: str):
    m = re.match(r"^(pie-chart|horizontal-bar-chart|vertical-bar-chart)-(\d+)$", qname or "")
    if not m:
        return (qname or "", math.inf)
    return (m.group(1), int(m.group(2)))

def extract_answer_value(answer_obj):
    if not isinstance(answer_obj, dict) or not answer_obj:
        return None
    for k in ["pieChart", "horizontalBarChart", "verticalBarChart"]:
        if k in answer_obj:
            return answer_obj.get(k)
    for _, v in answer_obj.items():
        if isinstance(v, (int, float, str, bool)) or v is None:
            return v
    return None

def extract_correct_value(correct_obj):
    if isinstance(correct_obj, list) and correct_obj and isinstance(correct_obj[0], dict):
        return correct_obj[0].get("answer")
    return None

all_qnames = set()
correct_map = {}
rows = []

for p in participants:
    pid = p.get("participantId") or p.get("id")
    answers = p.get("answers", {})
    p_row = {"participantId": pid}

    for _, ans_payload in answers.items():
        cname = normalize_qname(ans_payload.get("componentName"))
        if not cname:
            continue

        all_qnames.add(cname)
        p_row[cname] = extract_answer_value(ans_payload.get("answer"))

        if cname not in correct_map:
            cval = extract_correct_value(ans_payload.get("correctAnswer"))
            if cval is not None:
                correct_map[cname] = cval

    rows.append(p_row)

qcols = sorted(all_qnames, key=parse_qname)
cols = ["participantId"] + qcols

correct_row = {"participantId": "CORRECT", **{c: correct_map.get(c) for c in qcols}}

df = pd.DataFrame([correct_row] + rows, columns=cols)
df.insert(1, "participantShort", df["participantId"].astype(str).str[:8])

df.to_csv("participants_answers_table.csv", index=False)
print("Wrote participants_answers_table.csv", df.shape)