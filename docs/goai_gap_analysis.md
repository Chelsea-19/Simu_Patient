# SimuPatient GOAI Gap Analysis

审计日期：2026-08-05
目标赛道：GOAI 2026 Boundless Agents · AI+教育
审计范围：当前工作区源码快照、Streamlit 原型、MockProvider、YAML 病例、SQLite 持久层、pytest 与两项内部评测

## Current Worktree Re-audit (2026-08-05)

本节记录用户本次指令触发的**当前工作区复审**。下方原有分析保留的是 `main`
提交 `5e1c3c7` 的预升级基线，不应被误读为当前
`feature/goai-education-agent` 分支的功能状态。当前分支已领先本地 `main` 8 个提交，
且没有配置 Git 远端，因此只能证明本地分支隔离，不能证明上游默认分支或远端同步状态。

### Current Runtime Evidence

| 项目 | 当前分支复审结果 |
|---|---|
| Python 文件 | 81 |
| YAML 病例 | 20 |
| pytest 文件 / 用例 | 15 / 67；`pytest -q` 退出码 0 |
| disclosure benchmark | 80 条 policy unit + 180 条 challenge；precision/recall 1.000；提前披露率 0.000 |
| OSCE benchmark | 10 条；MAE 19.100；pass/fail agreement 0.700；false fail 3 |
| Streamlit | Mock + learner 模式启动成功；health 与根页面均 HTTP 200；检查后已停止进程 |
| learner 隔离 | 12 项隔离测试通过；learner UI 无完整 JSON；instructor 数据需 `APP_ROLE=instructor` |
| Mock 无网络闭环 | `test_mock_provider_completes_full_encounter_without_network` 随全量测试通过 |
| GOAI 既有证据 | 15 条评测轨迹、8 张原型截图和可追溯指标文件存在；本次 Phase 0 未重跑 Phase 6 评测 |

### Priority Re-audit

| 优先级 | 当前状态 | 证据或边界 |
|---|---|---|
| P0 | COMPLETE | 隐藏状态隔离、胸痛闭环、vitals/ECG/troponin、鉴别与处置、安全阻断、Action Trace、多维诊断、Focused Retry、Mock 离线 Demo 与提交材料均有代码和测试/文件证据 |
| P1 | PARTIAL | 教师 Dashboard、Schema 验证器、两轮对比、15 条轨迹与 injection 测试已存在；公开 Streamlit Cloud URL 尚未部署/填写 |
| P2 | DEFERRED | 语音、数字人、医学影像输入、多用户权限、班级统计、医院连接、移动端与正式临床验证未实现，符合初赛后再做边界 |

### Current Quality and Compliance Gaps

- 所有公共函数参数与返回值均有类型标注；但 AST 扫描发现 103 个公共函数/方法没有
  docstring，不满足“新增公共函数写 docstring”的完整要求。
- Gemini、Ollama、OpenAI provider 均有异常转换或 health check，但未形成统一、显式的
  API timeout 配置与 Mock/template fallback；核心 Mock 路径不受此问题影响。
- `requirements.txt` 仍主要使用下界约束，且本次复审使用全局 Python 环境；可复现性弱于
  隔离虚拟环境加锁文件。
- 工作区存在被 `.gitignore` 排除的 `simupatient.db`、
  `evaluation/results/ui_evidence_phase6.db` 和缓存目录；它们均未被 Git 跟踪，但提交前仍应
  做一次打包范围复核。
- 精确检索未发现用户列出的夸大或禁用表述；密钥扫描只命中 README/部署文档中的
  `your-key` 示例占位符，未发现真实 API Key。
- PPT/PDF、简介和原型说明均存在，但公开在线 Demo URL 和最终录屏仍是人工提交前事项。

### Current Leakage Conclusion

预升级 `main` 基线确实存在完整病例泄露；当前升级分支已修复。当前 learner service 只返回
`LearnerVisibleCase`，learner session state 不保存 full profile，普通导出不包含隐藏事实，
`st.json(...)` 仅存在于角色门控的 instructor 页面。此结论来自全量 pytest 中的 12 项
隔离测试与当前源码路径复核，不代表临床有效性或高风险正式考试适用性。

## Executive Summary

当前项目具备适合增量升级的基础：Streamlit 单体入口、分层服务代码、SQLModel/SQLite、20 个可验证 YAML 病例、确定性 MockProvider、隐藏信息披露评测和 OSCE 内部评测均可运行。无需改写为 FastAPI、React、微服务或自由多 Agent 架构。

预升级原型当时尚不能作为 SimuPatient 比赛 Demo。首要阻断项是学生端直接展示完整病例对象；对 `chest_pain_001` 的动态 UI 探针确认页面泄露近期可卡因使用、red flags、expected questions、scoring rubric 和完整病史。当前流程也只有“建病例—聊天—评分”，缺少检查工具、鉴别诊断/处置提交、安全阻断、Action Trace、分层提示、复训对比和教师视图。

现有自动评分必须继续定位为形成性反馈和内部软件评测。基线 OSCE 评测的总分 MAE 为 19.100，通过/失败一致率为 0.700，红旗识别准确率为 0.700，尚不足以支持正式考核或临床验证主张。

## Repository and Runtime Baseline

| 项目 | 审计结果 |
|---|---|
| 应用入口 | `streamlit_app.py`，单 Streamlit 进程 |
| Python 文件 | 54 |
| YAML 病例 | 20，全部可通过当前 schema 加载 |
| pytest 文件 | 6 |
| pytest 用例 | 24，全部通过 |
| 数据层 | SQLModel + `sqlite:///simupatient.db` |
| 默认 LLM provider | `mock` |
| 可选 provider | Gemini、Ollama；另有 OpenAI provider 文件但 factory 当前公开选择需另行核查 |
| Streamlit 启动 | 成功；health endpoint HTTP 200，根页面 HTTP 200 |
| 原始 Git 元数据 | 工作区未提供 `.git`，无可恢复远端 URL或提交历史 |
| Phase 0 Git 基线 | 本地 `main` 根提交 `5e1c3c7`；已切换 `feature/goai-education-agent` |

## Evidence-backed Findings

### P0 — 学生端完整病例泄露

证据链：

- `streamlit_app.py` 在随机病例创建后调用 `st.json(data["profile"])`。
- `streamlit_app.py` 在 YAML 病例初始化后也调用 `st.json(data["profile"])`。
- `SimuEngine._profile_from_case_template()` 将 `hidden_info`、`hidden_information`、`red_flags`、`expected_key_questions` 和 `scoring_rubric` 放入同一个 `profile_data`。
- `generate_patient_from_case_template()` 将这个完整字典原样作为 `profile` 返回给 UI。
- Streamlit AppTest 启动 `chest_pain_001` 后实际渲染的 JSON 包含：
  - `hidden_info`: recent cocaine use；
  - `hidden_information`: 披露条件与临床意义；
  - `red_flags`: ACS、PE、aortic dissection；
  - `expected_key_questions`: 完整问题清单；
  - `scoring_rubric`: 40/20/20/10/10 权重；
  - 完整 HPI、既往史、用药史、家族史和社会史。

影响：核心训练答案在问诊开始前即可见，比赛的隐藏信息披露、临床推理、评分和复训证据均失效。

建议：Phase 1 建立明确的 `FullCaseState -> LearnerVisibleState + InstructorHiddenState` 投影边界；所有 learner UI 与 learner-facing service 只能接收投影后的 DTO，并加入 AppTest 防泄露回归测试。

### P0 — MockProvider 集成披露状态与基准逻辑不一致

确定性 disclosure benchmark 得分为满分，但实际聊天集成路径中的 `MockProvider.generate_json()` 只要状态更新 prompt 含 `should_reveal_hidden`/`disclosure`/`state`，就固定返回 `should_reveal_hidden=True`。用无关问题 `Hello, how are you feeling?` 运行实际 service 后，数据库中的 `hidden_info_revealed` 从 false 变为 true。

同时，MockProvider 的患者文本固定为头痛回答，即使正在运行 58 岁急性胸痛病例，响应仍是“两周头痛”。这说明：

- 当前 disclosure benchmark 主要验证独立、规则化的 evaluator，不等价于端到端 Patient Agent 披露安全；
- MockProvider 虽然完全离线且确定性，但目前不是病例感知的高保真 Demo provider；
- 比赛 Demo 需要为 `chest_pain_001` 提供病例感知的确定性回答和语义等价披露测试。

### P0 — 临床训练流程过度依赖聊天

代码搜索未发现以下工具或 Action Trace：

- `request_vital_signs`；
- `perform_physical_exam`；
- `order_ecg`；
- `order_lab_test`；
- `order_imaging`；
- `submit_differential_diagnosis`；
- `submit_management_plan`；
- `request_hint`；
- `finish_encounter`；
- `action_trace`。

`chest_pain_001.yaml` 当前 schema 也没有生命体征、体格检查、ECG、troponin、影像、正确动作、危险动作或完成条件字段。因此 ECG/troponin 等结果目前无法由结构化病例真相确定，也没有资源/时间或解锁规则。

### P0 — 缺少安全监督闭环

当前“Finish Consultation and Evaluate”按钮可以直接结束问诊。未发现对急性胸痛回家处置、未识别危重风险、未申请关键检查或缺少安全网建议的结束阻断。现有 `safety_flags` 只在事后评估中参与扣分，且由 provider 输出，不是确定性 Safety Supervisor。

### P1 — 学情诊断维度不完整

当前 UI 展示 5 个维度：history taking、communication、reasoning、empathy、closure。与比赛需求相比，缺少明确且独立的：

- 危险信号识别；
- 检查选择合理性；
- 鉴别诊断质量；
- 处置安全性；
- 总结与安全网建议。

当前评分依赖 provider 生成 qualitative JSON，再由 Python 融合；虽有 rubric 和内部指标，但尚未完全落实“结构化事实 + Python 规则决定基础分，LLM 只做语言/抽取”的边界。

### P1 — 会话数据持久化不等于训练可续接

动态检查结果：SQLite 成功保存了 1 个 patient、1 条 consultation 和 1 条 session state；但新 AppTest/浏览器会话的 `patient_id` 为 `None`、`chat_history` 为空。UI 没有从数据库加载既有训练的入口，也没有稳定的 learner/session/attempt 标识。

因此当前状态是：

- 数据记录具备局部持久化；
- 当前 UI 会话依赖 `st.session_state`；
- 页面重连或新浏览器会话无法恢复完整训练；
- 无法可靠组织第一轮/第二轮、历史弱项或学习进步。

### P1 — 缺少个性化学习与学习陪伴

未发现 learner profile、历史弱项聚合、case recommendation、difficulty adaptation、三层 hint、targeted retraining task 或两轮 comparison 数据模型/服务/UI。

### P1 — 缺少教师辅助视图

当前只有 Create Patient、Consultation、OSCE Assessment 三个 tab。未发现教师角色边界、完整 Action Trace、关键遗漏审阅、attempt comparison、报告导出或 YAML 模板验证 UI。

### P1 — 依赖可复现性风险

`requirements.txt` 全部使用下界约束，没有锁文件或上界。Phase 0 安装成功，但 pip 报告当前全局 Python 环境中存在多项与项目外包的版本冲突；安装还升级/降级了 pydantic、protobuf、requests 等共享环境依赖。后续应使用项目虚拟环境与受控锁定策略，避免比赛机器漂移。

## Baseline Test and Evaluation Results

### pytest

`pytest`：24 passed in 11.76s；工具记录的总命令耗时为 32.6s。

当前测试覆盖 YAML loader、case service、disclosure metrics、OSCE metrics、provider factory 和 MockProvider service smoke test。没有 Streamlit UI 防泄露测试、端到端病例一致性测试、工具路由测试、安全阻断测试、复训闭环测试或教师视图测试。

### Disclosure Evaluation

`LLM_PROVIDER=mock python experiments/run_disclosure_eval.py`：退出码 0。

- policy unit scenarios: 80；precision 1.000；recall 1.000；premature disclosure rate 0.000；
- challenge scenarios: 180；precision 1.000；recall 1.000；premature disclosure rate 0.000；
- exact item match 1.000；over-disclosure 0.000；prompt injection resistance 1.000。

解释边界：这是 authored deterministic rule evaluation，不是实际聊天集成、外部模型或临床环境验证。

### OSCE Evaluation

`LLM_PROVIDER=mock python experiments/run_osce_eval.py`：退出码 0，10 transcripts。

- total score MAE: 19.100；
- score correlation: 0.970；
- pass/fail agreement: 0.700；
- false pass: 0；false fail: 3；
- red flag detection accuracy: 0.700；
- missed item detection accuracy: 0.432。

解释边界：排序相关性较高，但校准误差、错误不通过和漏项识别不足明显；只能用于内部回归与形成性反馈。

## GOAI Education Track Mapping

| 教育价值 | 当前证据 | 差距 | 目标能力 |
|---|---|---|---|
| 个性化学习 | 无历史学习者模型 | 无推荐、调难、复训、对比 | Planner 基于弱项生成 attempt 1/2 训练计划 |
| 学情诊断 | 5 维形成性评分 | 缺检查、鉴别、安全网等维度 | 规则证据驱动的多维诊断与证据链接 |
| 学习陪伴 | 普通患者聊天 | 无分层提示 | 反思式→方向性→教学解释，记录提示成本 |
| 教师辅助 | 最终 JSON 报告 | 无角色隔离、Action Trace、导出、模板验证 | 轻量 Instructor View |
| 可演示闭环 | 建病例→聊天→评分 | 无工具、阻断、复训与进步比较 | 完整 attempt loop 与可回放证据 |

## Assets to Reuse

- `streamlit_app.py`：保留单应用入口，增量添加 learner/instructor 页面和流程控制。
- `app/services/`：保留 case loader、simulation、disclosure、assessment 的职责基础；新增确定性 training/safety/tool/attempt 服务。
- `app/providers/`：保留 factory 与 Mock/Gemini/Ollama 抽象；强化病例感知 Mock，不让 provider 决定事实和分数。
- `app/models/`、`app/schemas/`、`app/repositories/`：保留 SQLModel 分层；增量增加 learner、training attempt、action event、submission、retraining plan。
- SQLModel + SQLite：足以支撑初赛单机 Demo 和 trace 持久化，无需引入外部数据库。
- YAML case templates：保留 20 个现有病例；优先只扩展 `chest_pain_001` 的 v2 可选字段并保持其他病例向后兼容。
- disclosure/OSCE evaluations：保留为内部回归基线，并新增端到端集成轨道。
- pytest 与 MIT License：完整保留。

## Modules to Add Incrementally

- learner/instructor case projection schema；
- deterministic encounter state machine；
- clinical skill router 与工具结果 schema；
- Action Trace/event repository；
- Safety Supervisor 与 finish guard；
- differential/management structured submissions；
- expanded formative assessment evidence model；
- three-level hint policy；
- Learning Planner、retraining plan 和 attempt comparison；
- Instructor View、YAML validator 和 report export。

## Claim Boundaries

所有 UI、报告和比赛材料应明确：

- 系统用于临床技能与 OSCE 形成性训练；
- 自动评分是学习过程诊断和教师辅助参考；
- 不是医疗器械，不提供真实患者诊断或治疗；
- 不替代真实 OSCE 考官；
- 未经临床验证，不用于高风险正式考核；
- Mock/内部 benchmark 的满分只代表确定性 authored 测试通过。
