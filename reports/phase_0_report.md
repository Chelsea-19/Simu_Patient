# Phase 0 Report

## Status

PASS

Phase 0 的仓库审计、独立升级分支、依赖安装、测试/评测、Streamlit 启动、动态泄露探针、持久化检查与升级文件规划均已完成。未修改核心功能。

重要保留意见：用户提供的工作区是缺少 `.git` 的源码快照，因此原默认分支、提交历史和远端来源无法审计。Phase 0 在本地初始化 `main` 并提交原始快照，再建立目标分支；这保证后续本地改动可回退，但不能恢复或证明上游历史。

## Current-worktree Re-audit

本次用户再次要求只执行 Phase 0 时，仓库已经位于
`feature/goai-education-agent`，HEAD 为 `73fc684`，并已包含 Phase 1–7 的本地提交。
因此本报告保留下方原始 Phase 0 基线，同时把本次命令结果单独列出，避免把预升级缺陷
错误表述为当前缺陷。

### Re-audit Status

PASS

- 当前工作树在复审前干净；本地分支比 `main` 领先 8 个提交；没有配置 remote 或
  可解析的远端默认分支。
- `python -m pip install -r requirements.txt`：退出码 0，9.6s，依赖均已满足。
- `pytest -q`：退出码 0，67 项测试通过，命令总耗时 84s。
- `pytest --collect-only -q`：15 个测试文件，共 67 项。
- `LLM_PROVIDER=mock python experiments/run_disclosure_eval.py`：退出码 0；80+180 条；
  precision/recall 1.000；提前披露率 0.000；injection resistance 1.000。
- `LLM_PROVIDER=mock python experiments/run_osce_eval.py`：退出码 0；10 条；MAE 19.100；
  pass/fail agreement 0.700；false fail 3；red flag accuracy 0.700。
- `LLM_PROVIDER=mock APP_ROLE=learner streamlit run streamlit_app.py`：进程 PID 34200；
  `/_stcore/health` HTTP 200、body `ok`；根页面 HTTP 200；检查后已停止。
- 当前共有 81 个 Python 文件、20 个 YAML 病例和 15 个 pytest 文件。
- learner 隔离、完整 Mock 离线闭环、危险回家阻断、Action Trace、复训与教师能力均随
  全量测试通过；本次未重跑不属于 Phase 0 指定命令的 GOAI Phase 6 评测。

### Re-audit Findings

- **历史泄露已修复：** 预升级 `main` 会向 learner 展示完整 profile；当前分支仅返回
  `LearnerVisibleCase`，普通 learner UI 没有 `st.json`，12 项隔离测试覆盖导出、reset、
  instructor gate 与 Patient Agent prompt 边界。
- **P0 已有实现证据：** 胸痛病例包含 YAML 配置的生命体征、ECG、troponin、安全规则；
  临床工具、鉴别诊断、处置、安全阻断、Trace、多维形成性反馈与 Focused Retry 均存在。
- **P1 尚未完全闭合：** 教师 Dashboard、Schema validator、两轮对比、15 条轨迹和
  prompt injection 测试存在，但公开 Streamlit Cloud URL 仍为空。
- **质量缺口：** 103 个公共函数/方法缺少 docstring；外部 provider 未统一配置显式
  timeout 与 fallback；依赖未锁定；本次运行使用全局 Python 环境。
- **提交卫生：** 没有被 Git 跟踪的数据库或缓存；工作区存在被忽略的本地数据库和缓存。
  密钥模式检索只命中文档中的示例占位符，没有发现真实 API Key。
- **表述边界：** 精确检索未发现用户列出的禁用夸大表述。OSCE MAE 19.1 和 3 个
  false fail 必须继续保留，只能表述为形成性反馈与内部软件评测。

### Files Modified by Re-audit

- `docs/goai_gap_analysis.md`
- `docs/goai_upgrade_plan.md`
- `reports/phase_0_report.md`

核心源码：无。benchmark 输出被指定命令重新生成，但内容未形成 Git diff。

## Goals

- 核查真实仓库、架构、测试、病例和运行状态；
- 建立 `feature/goai-education-agent` 升级分支；
- 运行用户指定的依赖安装、pytest 和两项 Mock 评测；
- 启动 Streamlit 原型并检查答案泄露、持久化和离线 Mock；
- 建立 GOAI 差距分析与增量升级计划；
- 不改动核心业务功能。

## Completed Work

- 枚举工作区：确认现有 Streamlit、service/provider/model/schema/repository、SQLite、YAML、评测与测试资产；
- 确认工作区初始没有 `.git`，README/技术报告中无可恢复远端 URL；
- 本地初始化 `main`，提交 102 个原始文件作为基线 `5e1c3c7`；
- 从基线创建并切换 `feature/goai-education-agent`；
- 安装 `requirements.txt`；
- 运行全部 24 项 pytest；
- 运行 80 条 disclosure policy unit 与 180 条 behavioral challenge；
- 运行 10 条 OSCE transcript 评测；
- 实际启动 Streamlit，health 与根页面均返回 HTTP 200，并在检查后停止该进程；
- 使用 Streamlit AppTest 点击 `chest_pain_001`，动态复现完整病例泄露；
- 验证 SQLite 局部持久化和新 UI 会话无法恢复当前训练；
- 在禁用 socket connect 的探针中验证 MockProvider 初始化、health、text 和 JSON 生成均无需网络；
- 统计 20 个病例、6 个测试文件、24 个测试用例和 54 个 Python 文件；
- 搜索并确认当前不存在核心临床工具和 Action Trace；
- 形成后续 Phase 1–7 的增量升级路线。

## Files Added

- `docs/goai_gap_analysis.md`
- `docs/goai_upgrade_plan.md`
- `reports/phase_0_report.md`

## Files Modified

核心源码：无。

以下现有评测输出被用户指定的 benchmark 命令重新生成；内容哈希与基线提交一致，仅工作区文件时间状态发生变化，后续 `git add` 刷新索引后不形成内容 diff：

- `experiments/results/disclosure_challenge_eval.csv`
- `experiments/results/disclosure_challenge_eval.json`
- `experiments/results/disclosure_eval_summary.md`
- `experiments/results/disclosure_policy_unit_eval.csv`
- `experiments/results/disclosure_policy_unit_eval.json`
- `experiments/results/osce_eval.csv`
- `experiments/results/osce_eval.json`
- `experiments/results/osce_eval_per_transcript.md`
- `experiments/results/osce_eval_summary.md`

本地运行生成了被 `.gitignore` 排除的 `simupatient.db`，用于持久化探针；未加入版本控制。

## Commands Executed

关键命令与等价 PowerShell 形式：

```text
git status --short --branch
git branch --show-current
git remote -v
git init -b main
git add -A
git commit -m "chore: capture pre-upgrade source snapshot"
git switch -c feature/goai-education-agent
pip install -r requirements.txt
pytest
$env:LLM_PROVIDER='mock'; python experiments/run_disclosure_eval.py
$env:LLM_PROVIDER='mock'; python experiments/run_osce_eval.py
python -m streamlit run streamlit_app.py --server.headless=true --server.port=8507
pytest --collect-only -q
```

还执行了只读源码搜索、case loader 统计、SQLite 查询、禁网 MockProvider 探针和 Streamlit AppTest 动态 UI 探针。

## Test Results

### Dependency installation

- `pip install -r requirements.txt`：退出码 0；命令耗时 99.1s。
- 成功安装/更新 Google Generative AI 依赖、pydantic 2.13.4、requests 2.34.2、protobuf 5.29.6 等。
- pip 报告全局环境存在若干项目外包冲突，包括 google-genai/httpx、gradio/fastapi、selenium/typing-extensions、shap/numpy 等。它们未阻止本项目测试，但说明应改用隔离虚拟环境。

### pytest

- 命令：`pytest`
- 退出码：0
- 首次基线结果：`24 passed in 11.76s`；工具记录总命令耗时 32.6s
- 文档生成后的最终复核：`24 passed in 9.21s`；工具记录总命令耗时 22.1s
- `git diff --check`：退出码 0

### Disclosure evaluation

- 命令：`LLM_PROVIDER=mock python experiments/run_disclosure_eval.py`
- 退出码：0
- policy unit scenarios：80
- precision / recall：1.000 / 1.000
- premature disclosure rate：0.000
- behavioral challenge scenarios：180
- precision / recall：1.000 / 1.000
- exact item match：1.000
- over-disclosure rate：0.000
- prompt injection resistance：1.000

### OSCE evaluation

- 命令：`LLM_PROVIDER=mock python experiments/run_osce_eval.py`
- 退出码：0
- transcripts：10
- total score MAE：19.100
- pass/fail agreement：0.700
- false pass / false fail：0 / 3
- red flag detection accuracy：0.700
- missed item detection accuracy（来自 summary）：0.432

### Streamlit startup

- provider：mock
- 进程 PID：32244
- `/_stcore/health`：HTTP 200，body `ok`
- `/`：HTTP 200，返回 Streamlit 页面
- 检查后已停止 PID 32244

## Demo Evidence

### Full-profile leakage reproduced

Streamlit AppTest 执行：

1. 打开应用；
2. 切换到 `Case template`；
3. 选择默认首项 `Acute chest pain ... (chest_pain_001)`；
4. 点击 `Start Case Consultation`。

实际结果：

- 无 Streamlit exception；
- 页面显示 `Case initialized. Patient ID: 1`；
- 页面出现 1 个 JSON 元素；
- JSON 中包含 `recent cocaine use`、披露条件、临床意义、ACS/PE/aortic dissection、完整 expected questions 和 scoring rubric；
- learner `st.session_state.patient_profile` 同样包含这些 instructor-only keys。

结论：学生端答案泄露已由动态 UI 证据确认，不只是静态代码推断。

### Persistence probe

- 一次实际 Mock chat 后数据库计数：patient 1、consultation 1、session state 1；
- persisted state：patient_id 1、trust 6、anxiety 4、cooperativeness 7、hidden revealed 1；
- 新 AppTest 会话：`patient_id=None`、`chat_history=[]`。

结论：数据库能持久化部分业务记录，但 UI 没有 active training 恢复机制。

### MockProvider offline probe

在将 `socket.socket.connect` 替换为立即抛错的条件下：

- provider class：MockProvider；
- health check：true；
- text generation：成功；
- JSON generation：成功。

结论：MockProvider 核心调用确实不需要 API 或网络。

### Mock integration inconsistency

对 chest pain patient 输入无关问题 `Hello, how are you feeling?`：

- 返回内容仍为固定的“两周头痛”回答，与胸痛病例不一致；
- `hidden_info_revealed` 被写为 true。

结论：当前满分 disclosure benchmark 不能代表端到端 Mock patient 行为；Phase 1 必须补集成回归。

## Known Issues

- 学生端直接泄露完整病例、隐藏信息、标准答案和评分 rubric；
- learner/full case state 未分离；
- MockProvider 不具备病例一致性，披露状态 gate 过宽；
- 无生命体征、体检、ECG、lab、imaging 工具；
- 无鉴别诊断、处置、安全网结构化提交；
- 无确定性 Safety Supervisor 和结束阻断；
- 无 Action Trace、资源/时间、完成条件；
- 评分维度不足且 OSCE 校准误差明显；
- 无 learner history、个性化推荐、三级提示、复训和两轮比较；
- 无教师视图、YAML 校验 UI 和报告导出；
- 新 UI 会话不能恢复 active training；
- requirements 无锁定且本次使用全局 Python 环境；
- `app/services/simu_engine.py` 中部分中文 prompt/注释在当前终端显示乱码，需区分“终端编码显示问题”与“源文件真实编码损坏”后再处理。

## Risks

- 原 `.git`、默认分支和远端缺失，无法验证上游历史或与真正 main 的差异；
- 当前本地 `main` 是 Phase 0 创建的源码快照基线，不应被表述为恢复的上游 main；
- disclosure 满分来自 authored deterministic evaluator，可能造成过度安全主张；
- OSCE 评测仅 10 份 authored transcripts，MAE/漏项指标不满足高风险评分用途；
- SQLite 单机适合初赛 Demo，但 Streamlit Cloud 睡眠会丢本地数据库；
- 直接在共享全局 Python 安装依赖可能影响同机其他项目；
- 如果后续把工具结果交给 LLM生成，将破坏事实可验证性；必须坚持 YAML + Python 规则边界。

## Next Phase Inputs

建议 Phase 1 只处理安全边界和披露集成，不提前实现整个工具闭环：

- 建立 full/learner/instructor case projection；
- 移除 student-facing full JSON；
- 防止 learner session payload 携带 instructor-only fields；
- 增加 Streamlit AppTest 与 service 防泄露测试；
- 修复 chest pain Mock 问答一致性和无关问题误解锁；
- 保持现有 24 项测试与两项 benchmark 通过；
- 生成 `reports/phase_1_report.md` 后停止。

等待用户发送：`继续 Phase 1`。
