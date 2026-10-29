# -*- coding: utf-8 -*-
"""小米智能家居客服小助手 Agent —— 带 Langfuse 全链路追踪

用法:
    python agent.py "小爱同学没反应了怎么办"
"""
import os
import sys

from openai import OpenAI
from langfuse import Langfuse, observe

from kb import FAQ_KB, match_kb


def load_env():
    """简易 .env 加载（避免额外依赖）"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


load_env()

_key = os.environ.get("DEEPSEEK_API_KEY", "")
try:
    LLM = OpenAI(api_key=_key or "sk-placeholder", base_url="https://api.deepseek.com")
    if not _key:
        raise ValueError("未配置 DEEPSEEK_API_KEY")
except Exception as e:  # 没配 key 时给出友好提示，而不是 import 就崩
    LLM = None
    _LLM_ERROR = "未配置 DEEPSEEK_API_KEY，请复制 .env.example 为 .env 并填写密钥"

# Langfuse 客户端：没配密钥时跳过（不记录 trace，也不打扰）
lf = None
if os.environ.get("LANGFUSE_PUBLIC_KEY"):
    try:
        lf = Langfuse()
    except Exception:
        lf = None

SYSTEM_PROMPT = """你是米家智能家居的客服小助手。回答要求：
1. 最多 3 步，步骤清晰、可执行；
2. 语言平实，不堆术语；
3. 优先依据知识库检索结果回答；
4. 知识库里没有相关内容时，只明确说「这个我不太确定，建议联系人工客服」，不要再给出任何排查步骤，不要编造。"""


@observe(name="检索知识库")
def retrieve(question: str) -> str:
    """知识库检索环节：命中 FAQ 则返回标准答案片段"""
    hits = match_kb(question)
    if not hits:
        return "(未命中)"
    return "\n".join(f"[FAQ-{fid}] {ans}" for fid, ans in hits)


@observe(name="生成回答")
def generate(question: str, context: str) -> str:
    """生成环节：调用 DeepSeek，按系统提示词生成客服回复"""
    if LLM is None:
        raise RuntimeError(_LLM_ERROR)
    resp = LLM.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"知识库检索结果：\n{context}\n\n用户问题：{question}"},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content


@observe(name="客服Agent")
def agent_answer(question: str) -> dict:
    """Agent 主流程：检索 -> 生成，两个子环节都会出现在 Langfuse 链路里"""
    ctx = retrieve(question)
    ans = generate(question, ctx)
    trace_id = None
    if lf is not None:
        try:
            trace_id = lf.get_current_trace_id()
        except Exception:
            pass
    return {"question": question, "context": ctx, "answer": ans, "trace_id": trace_id}


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "小爱同学没反应了怎么办"
    r = agent_answer(q)
    print("问题:", r["question"])
    print("检索:", r["context"].replace("\n", " / ")[:100])
    print("回答:", r["answer"])
    print("trace:", r["trace_id"])