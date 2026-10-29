# -*- coding: utf-8 -*-
"""评估脚本：跑测试集 -> LLM-as-judge 打分 + 关键词自动打分 -> 写入 Langfuse

用法:
    python eval.py
"""
import json

from openai import OpenAI
from langfuse import Langfuse, observe

from agent import agent_answer, load_env, LLM

load_env()
lf = Langfuse()  # 自动读 LANGFUSE_PUBLIC_KEY / SECRET_KEY / HOST

# 测试集：库内问题 + 库外问题 + 混淆用例（关键词重叠，考察"不编造"）
TEST_CASES = [
    {"question": "怎么把智能灯泡连上米家App？", "expected_keywords": ["配网", "2.4G"]},
    {"question": "网关一直闪红灯，设备都掉线了", "expected_keywords": ["重启", "电源"]},
    {"question": "小爱同学叫了没反应", "expected_keywords": ["静音", "重启"]},
    {"question": "帮我设置插座每天早上7点自动开灯", "expected_keywords": ["定时"]},
    {"question": "摄像头画面黑屏了", "expected_keywords": ["重启", "Wi-Fi"]},
    {"question": "明天武汉天气怎么样？", "expected_keywords": ["人工客服"]},
    # ---- v2 新增：新 FAQ 覆盖 ----
    {"question": "指纹锁突然开不了门了", "expected_keywords": ["电池", "密码"]},
    {"question": "空气净化器一直提示要换滤芯", "expected_keywords": ["滤芯", "重置"]},
    {"question": "扫地机器人回不去充电桩了", "expected_keywords": ["触点", "回充"]},
    {"question": "小爱控制不了空调了", "expected_keywords": ["绑定", "房间"]},
    {"question": "电动窗帘卡住不动了", "expected_keywords": ["异物", "复位"]},
    # ---- v2 新增：混淆用例 ----
    {"question": "扫地机器人的定时清扫怎么设置？", "expected_keywords": ["定时", "App"]},
    {"question": "我家路由器坏了上不了网怎么办？", "expected_keywords": ["人工客服"]},
]

JUDGE_PROMPT = """你是 Agent 输出评估员。请按以下标准给客服回答打分（1-5 的整数）：
- 相关性：是否直接解决用户问题；出现知识库之外的编造内容（如编造不存在的设置项）直接记 1 分
- 步骤清晰：是否 ≤3 步、每步可执行；超过 3 步最多记 3 分
- 语言平实：无术语堆砌、无编造
- 拒绝类回答单独口径：明确说"不确定 + 建议人工客服"，若完整说明拒绝原因与服务范围记 4-5 分，仅说"不知道"记 3 分，拒绝后仍给出无关步骤记 1 分
只输出 JSON，格式：{{"score": 整数, "reason": "一句话理由"}}

用户问题：{q}
客服回答：{a}"""


@observe(name="LLM-as-judge")
def judge(question: str, answer: str) -> dict:
    """让另一个 LLM 按评分标准打分（LLM-as-judge）"""
    resp = LLM.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(q=question, a=answer)}],
        temperature=0,
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {"score": -1, "reason": "judge 输出解析失败"}


def run_eval():
    for i, tc in enumerate(TEST_CASES, 1):
        result = agent_answer(tc["question"])  # 每次调用生成一条 trace

        j = judge(tc["question"], result["answer"])

        # 自动规则分：期望关键词是否出现在回答里（0/1）
        hit = sum(1 for k in tc["expected_keywords"] if k in result["answer"])
        auto = 1.0 if hit >= 1 else 0.0

        # 两个指标都挂到这条 trace 上
        if result.get("trace_id"):
            lf.create_score(trace_id=result["trace_id"], name="judge_score",
                            value=float(j["score"]), comment=j["reason"])
            lf.create_score(trace_id=result["trace_id"], name="keyword_hit",
                            value=auto, comment=f"命中 {hit} 个期望关键词")
        print(f"[case{i}] {tc['question']}")
        print(f"   回答: {result['answer'][:60]}...")
        print(f"   judge={j['score']}  keyword_hit={auto}  | {j['reason']}")
    lf.flush()
    print("评估完成，打开 Langfuse 面板查看 traces 与 scores")


if __name__ == "__main__":
    run_eval()