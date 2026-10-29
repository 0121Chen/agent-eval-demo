# Agent 评估与标注工作流 Demo

基于开源 LLM 工程平台 **Langfuse** 搭建的最小可用 Agent 评估链路：
小米智能家居客服 Agent → 全链路追踪 → LLM-as-judge + 规则评分 → 人工标注规范。

> 项目初衷：对应「生态链软件产品经理 - Agent 方向」实习 JD 的核心工作内容——
> 评估 Agent 输出、沉淀标注规范、分析评估数据。

## 文件结构

```
agent-eval-demo/
├── kb.py            # FAQ 知识库 + 关键词检索
├── agent.py         # 客服 Agent（检索 → 生成，全程 Langfuse 追踪）
├── eval.py          # 测试集 + LLM-as-judge + 关键词命中评分
├── 标注规范.md       # 人工标注规范（产品经理的核心交付物）
├── requirements.txt
└── .env.example     # 复制为 .env 并填写密钥
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置密钥

```bash
cp .env.example .env   # Windows 下直接复制改名为 .env
```

- `DEEPSEEK_API_KEY`：[platform.deepseek.com](https://platform.deepseek.com) → API Keys
- Langfuse 密钥（二选一）：
  - **云版（最快）**：[cloud.langfuse.com](https://cloud.langfuse.com) 注册 → 创建项目 → Settings → API Keys
  - **本地版（进阶）**：Docker 部署后 `LANGFUSE_HOST=http://localhost:3000`

### 3. 跑一次 Agent

```bash
python agent.py "小爱同学没反应了怎么办"
```

### 4. 跑评估

```bash
python eval.py
```

### 5. 看结果

打开 Langfuse 面板 → 项目 → Traces：每条调用有完整链路（客服Agent → 检索知识库/生成回答），
Scores 里能看到 `judge_score`（LLM 裁判分）和 `keyword_hit`（规则分）。

## 本地部署 Langfuse（可选进阶）

```bash
# 在 langfuse 仓库目录（已 clone 到 Downloads\langfuse）
docker compose up -d
# 浏览器打开 http://localhost:3000，注册管理员账号
```

## 后续可以做的（写进简历的素材）

- [ ] 扩充 FAQ 知识库到 20+ 条，观察检索命中率变化
- [ ] 增加「反问澄清」分支（模糊问题不直接回答）
- [ ] 对比不同提示词版本下的 judge_score 变化，写一份对比报告
- [ ] 按《标注规范.md》人工标注一批样本，与 LLM-as-judge 结果做一致性分析
- [ ] 从 Dashboard 导出评估数据，用 Python 做失败模式分析（哪个 FAQ 类目失分最多）
