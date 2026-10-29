# -*- coding: utf-8 -*-
"""收集评估数据：跑测试集，保存完整回答/trace_id/裁判分到 eval_results.json"""
import json

from agent import agent_answer, load_env
from eval import judge, TEST_CASES, lf

load_env()

results = []
for i, tc in enumerate(TEST_CASES, 1):
    r = agent_answer(tc["question"])
    j = judge(tc["question"], r["answer"])
    hit = sum(1 for k in tc["expected_keywords"] if k in r["answer"])
    item = {
        "case": i,
        "question": tc["question"],
        "answer": r["answer"],
        "trace_id": r.get("trace_id"),
        "judge_score": j["score"],
        "judge_reason": j["reason"],
        "keyword_hit": 1.0 if hit >= 1 else 0.0,
    }
    results.append(item)
    if r.get("trace_id"):
        lf.create_score(trace_id=r["trace_id"], name="judge_score",
                        value=float(j["score"]), comment=j["reason"])
        lf.create_score(trace_id=r["trace_id"], name="keyword_hit",
                        value=item["keyword_hit"], comment=f"命中 {hit} 个期望关键词")
    print(f"[case{i}] judge={j['score']} kw={item['keyword_hit']} trace={r.get('trace_id')}")

lf.flush()
with open("eval_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("已保存 eval_results.json")
