# SimuPatient GOAI Incremental Upgrade Plan

计划日期：2026-08-05
工作分支：`feature/goai-education-agent`
策略：围绕 `case_templates/chest_pain_001.yaml` 建立真实、可回放的最小教育闭环；保持 Streamlit + SQLModel/SQLite 架构，不进行大规模重写。

## Current Implementation Checkpoint (2026-08-05)

本计划最初基于本地 `main` 预升级快照编写。当前
`feature/goai-education-agent` 已包含后续阶段实现，本次只做 Phase 0 复审，不重复开发或
进入下一阶段。

| 工作流 | 当前证据状态 |
|---|---|
| P0 比赛闭环 | 已实现并由 67 项 pytest、Mock 无网络测试、15 条现有评测轨迹支持 |
| P1 教师与评测 | Dashboard、模板验证、两轮对比、injection 测试已实现；在线部署仍待人工完成 |
| P2 扩展能力 | 按初赛边界继续延后，不进入本轮计划 |
| 代码质量补强 | 后续优先统一 provider timeout/fallback、补公共 docstring、收紧依赖锁定 |

本次复审后的建议执行顺序保持为：先完成公开部署和质量硬化，再考虑 P2；不要因已有提交
而把正式临床验证、真实患者使用或 OSCE 考官替代写成已完成。

## Target Demo Contract

最终 Demo 必须按同一训练 attempt 的确定性状态推进：

```text
训练目标与历史弱项
→ 推荐胸痛病例与难度
→ 多轮病史采集
→ 生命体征/体检/ECG/troponin 工具
→ 鉴别诊断提交
→ 处置与安全网提交
→ Safety Supervisor 允许或阻止结束
→ 多维形成性学情诊断
→ 针对性复训任务
→ 第二轮训练
→ 两轮证据与得分对比
```

完成定义：每一步均有持久化 Action Trace、结构化输入/输出、确定性规则结果、UI 演示路径和 pytest 证据。

## Architectural Constraints

1. YAML/结构化病例是事实唯一来源；生命体征、ECG、troponin 和答案不得由 LLM 临场生成。
2. Python 决定状态迁移、工具解锁、安全阻断、资源成本、基础评分与完成条件。
3. LLM 只用于语义理解、患者措辞、自由文本结构化和反馈表达；Mock 路径必须完全离线。
4. learner-facing DTO 永远不包含 instructor-only 字段。
5. 自动评分只称为形成性反馈/内部评测，不做正式 OSCE 或临床有效性主张。
6. 其他 19 个病例必须继续通过现有 loader；v2 字段采用向后兼容默认值。

## Proposed Incremental Component Map

| 组件 | 复用 | 增量新增 |
|---|---|---|
| Learning Planner | case loader、SQLite repositories | learner history、weakness profile、case recommendation、retraining plan |
| Patient Agent | SimuEngine、providers、disclosure service | learner-visible case context、case-aware Mock、禁止事实扩写 |
| Clinical Skill Router | Streamlit services | typed tool commands、deterministic results、cost/unlock rules |
| Safety Supervisor | red flags、assessment flags | critical action rules、unsafe plan detection、finish guard |
| Assessment & Coaching | rubric、OSCE evaluator | evidence-linked dimensions、hint cost、weakness diagnosis、attempt comparison |

## Phase Plan

### Phase 1 — Case Boundary and Leakage Elimination

目标：先使学生端安全，再扩展流程。

- 新增 `LearnerVisibleCase` 与 `InstructorCaseState`/full case 投影；
- learner service 不再返回 full profile；
- 移除两处 learner UI 的完整 `st.json(profile)`；
- consultation summary 只展示基础人口学、主诉、场景和已解锁事实；
- 为 `chest_pain_001` 建立 AppTest 防泄露断言；
- 确保 instructor-only 字段仍可在受控服务中读取；
- 修复 Mock 集成路径“无关问题即设置 hidden revealed”的问题。

验收重点：学生页面、session state 中的 learner payload 和 learner-facing service 响应均不含 hidden/red flag/rubric/expected question/ground truth。

### Phase 2 — Structured Chest-pain Case and Clinical Skill Router

目标：加入真实可运行的确定性检查工具与 Action Trace。

- 向 v2 YAML schema 添加可选的 vitals、physical exam、ECG、labs、imaging、cost/time、unlock rules；
- 扩展 `chest_pain_001.yaml`，加入固定生命体征、ECG 与 troponin 结果；
- 实现 encounter state machine 与 typed tool commands；
- 实现 `request_vital_signs`、`perform_physical_exam`、`order_ecg`、`order_lab_test`、`order_imaging`；
- 所有调用持久化为 append-only Action Trace；
- 其他 19 个病例使用向后兼容默认值。

验收重点：工具结果只来自 YAML，刷新后可回放，未调用的结果不出现在 learner state。

### Phase 3 — Structured Submissions and Safety Supervisor

目标：让病例能安全结束，而非任意点击完成。

- 实现 differential、management、safety-net structured submission；
- LLM 可做自由文本抽取，但确定性规则评估结构化结果；
- chest pain critical rules 至少覆盖 ACS 风险、ECG/troponin、紧急升级、危险回家建议；
- 实现 `finish_encounter` guard；
- 对不安全结束给反思式风险提示，不直接泄露标准答案；
- 把阻断、解除阻断和最终提交写入 trace。

验收重点：“让患者回家”或未完成安全关键动作时不能结束；补救后可继续完成。

### Phase 4 — Multidimensional Formative Assessment

目标：从单一总分升级为证据可解释的学情诊断。

- 评分覆盖 history、communication、reasoning、red flags、test selection、differential、management safety、empathy、closure/safety net；
- 每个维度链接到 Action Trace 证据与遗漏；
- Python 生成基础分与安全上限，LLM 仅组织反馈语言；
- 加入不确定性和形成性用途声明；
- 新增端到端 chest pain golden traces（good/borderline/unsafe）。

验收重点：同一 trace 的 Mock 评分可重复，危险处置不能被高沟通分掩盖。

### Phase 5 — Layered Hints, Planner, and Retraining Loop

目标：完成个性化学习闭环。

- 实现三级提示：反思式、方向性、明确教学解释；
- 记录提示级别、使用次数与评分影响；
- 从 attempt 1 弱项生成 targeted retraining plan；
- 创建 attempt 2，推荐重点维度/难度；
- 生成两轮维度、关键遗漏、提示依赖与安全表现对比。

验收重点：可从第一次训练一键进入有针对性的第二轮，并显示证据化进步。

### Phase 6 — Instructor View and Export

目标：提供轻量教师辅助，不扩展为复杂 LMS。

- 受控 Instructor View 展示 full Action Trace、维度证据、安全遗漏和 attempt comparison；
- 提供 YAML 模板校验与错误定位；
- 导出 Markdown/JSON（必要时 PDF 延后）训练报告；
- 明确 learner/instructor 页面边界与演示角色切换。

验收重点：教师能审阅，学生看不到隐藏态；导出内容可复核且不夸大效度。

### Phase 7 — Hardening, Demo Evidence, and Competition Materials

目标：形成稳定可交付初赛版本。

- 全量 pytest、两项原评测、新端到端评测与 Streamlit smoke test；
- 建立一条 happy path、一条 unsafe-block path、一条 retraining-improvement path；
- 校验 Mock 离线演示，不依赖 API；
- 收紧依赖与建立干净环境安装说明；
- 完成 README、架构图、演示脚本、教育价值映射、限制与证据表；
- 保留 MIT License 与临床/考核用途边界。

验收重点：从干净环境可复现；所有比赛口径均由实际功能和测试支持。

## Initial File Change Map

文件名可在实现阶段按现有命名风格微调，但职责保持稳定。

### Reuse and Modify

- `streamlit_app.py`：页面边界、工具 UI、提交、复训和教师视图入口；
- `app/streamlit_services.py`：learner-safe facade 与新 workflow 调用；
- `app/services/simu_engine.py`：收窄为 patient/dialogue orchestration，避免承载全部 workflow；
- `app/services/disclosure_service.py`：确定性 gate 优先，LLM 语义辅助受规则约束；
- `app/services/assessment_engine.py`：接入 trace-based evidence 和形成性声明；
- `app/schemas/case_template_file.py`：向后兼容 v2 字段；
- `case_templates/chest_pain_001.yaml`：核心 Demo 事实、工具结果和安全规则；
- `app/providers/mock_provider.py`：病例感知的确定性响应；
- `README.md`、`TECHNICAL_REPORT.md`：在功能落地后更新叙事与限制。

### Likely Additions

- `app/schemas/learner_case.py`；
- `app/schemas/training.py`；
- `app/models/training_attempt.py`；
- `app/models/action_event.py`；
- `app/repositories/training_repository.py`；
- `app/repositories/action_trace_repository.py`；
- `app/services/learning_planner.py`；
- `app/services/clinical_skill_router.py`；
- `app/services/safety_supervisor.py`；
- `app/services/training_workflow.py`；
- `app/services/coaching_service.py`；
- focused tests for case projection, tools, safety, assessment, retraining, UI and export.

## Test Strategy

每个 Phase 至少包含：

1. schema/unit tests：事实和规则；
2. repository tests：SQLite 持久化与恢复；
3. service integration tests：MockProvider 完全离线；
4. Streamlit AppTest：学生端不泄露、关键演示路径可点击；
5. deterministic golden trace tests：分数、阻断和复训比较可重复；
6. 原 24 项测试与两项 benchmark 回归。

优先新增的失败测试：

- learner payload 不含 `hidden_info`、`hidden_information`、`red_flags`、`expected_key_questions`、`scoring_rubric`；
- 无关问句不能解锁可卡因使用；直接/语义等价询问才能解锁；
- 工具结果与 YAML 完全一致；
- 未 order 的 ECG/troponin 不可见；
- unsafe discharge 被阻断；
- 新会话可恢复 active attempt 和 trace；
- attempt 2 comparison 使用同一维度定义。

## Delivery and Risk Controls

- 每个 Phase 单独生成 `reports/phase_N_report.md`，真实记录命令、退出码和指标；
- 默认每个 Phase 后停止，等待用户明确继续；
- 不删除或重写现有病例、providers、评测和数据库分层；
- 不把 authored benchmark 满分包装为临床安全证据；
- 不把自动评分包装为正式 OSCE 分数；
- 如需 schema migration，先备份/兼容现有 SQLite 数据，不直接破坏表结构；
- 对 Gemini/Ollama 只做可选验证，核心比赛闭环必须由 Mock 离线复现。

## Phase 1 Inputs

- 已复现的 UI 泄露 JSON 与代码路径；
- `chest_pain_001` 当前 full case schema；
- 24 项 pytest 基线；
- disclosure benchmark 基线；
- OSCE benchmark 基线；
- 本地 Git baseline commit `5e1c3c7` 与工作分支 `feature/goai-education-agent`。
