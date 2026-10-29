# -*- coding: utf-8 -*-
"""把人工标注结果写入 Langfuse（按标注规范.md 的三个维度 + 综合结论）"""
import json

from agent import load_env
from langfuse import Langfuse

load_env()
lf = Langfuse()

# 人工标注结果（依标注规范.md 判例逐条评定）
HUMAN = [
    {"case": 1, "rel": 5, "steps": 5, "lang": 5, "overall": "通过",
     "note": "三步完整含2.4G前提，无冗余"},
    {"case": 2, "rel": 5, "steps": 5, "lang": 5, "overall": "通过",
     "note": "排查顺序合理，结尾引导人工客服得当"},
    {"case": 3, "rel": 5, "steps": 5, "lang": 5, "overall": "通过",
     "note": "静音→麦克风→重启，与FAQ一致"},
    {"case": 4, "rel": 5, "steps": 5, "lang": 5, "overall": "通过",
     "note": "定时设置三步入径正确"},
    {"case": 5, "rel": 5, "steps": 5, "lang": 5, "overall": "通过",
     "note": "重启→信号→存储卡，覆盖主要故障点"},
    {"case": 6, "rel": 4, "steps": 4, "lang": 5, "overall": "通过",
     "note": "拒绝得当且说明服务范围；无需步骤故按表述完整性给4"},
]

data = json.load(open("eval_results.json", encoding="utf-8"))
by_case = {d["case"]: d for d in data}

for h in HUMAN:
    d = by_case[h["case"]]
    tid = d["trace_id"]
    if not tid:
        continue
    lf.create_score(trace_id=tid, name="human_relevance", value=float(h["rel"]), comment=h["note"])
    lf.create_score(trace_id=tid, name="human_steps", value=float(h["steps"]), comment="人工标注")
    lf.create_score(trace_id=tid, name="human_language", value=float(h["lang"]), comment="人工标注")
    lf.create_score(trace_id=tid, name="human_overall", value=h["overall"],
                    data_type="CATEGORICAL", comment=h["note"])
    print(f"case{h['case']} 人工标注已写入: {h['rel']}/{h['steps']}/{h['lang']} -> {h['overall']}")

lf.flush()

# 一致性计算
agree_exact = 0
pairs = []
for h in HUMAN:
    d = by_case[h["case"]]
    human_mean = round((h["rel"] + h["steps"] + h["lang"]) / 3)
    diff = abs(human_mean - d["judge_score"])
    agree_exact += 1 if diff == 0 else 0
    pairs.append((h["case"], d["judge_score"], human_mean, diff))
print("\n一致性: 精确一致 %d/6, 全部在±1内: %s" % (agree_exact, all(d[3] <= 1 for d in pairs)))
