# SimuPatient 演示镜头清单

| 时间 | 镜头 | 现场操作或素材 | 核心信息 | 备份证据 |
|---|---|---|---|---|
| 0:00-0:08 | 01 封面 | PPT 第 1 页 | 自适应临床推理与 OSCE 训练 Agent | PPTX/PDF |
| 0:08-0:20 | 02 痛点 | PPT 第 2 页 | 训练机会、过程诊断与复训缺口 | PPTX/PDF |
| 0:20-0:45 | 03 训练目标 | Choose Training，选择胸痛模板 | learner 入口与目标 | `01_learning_goal_selection.png` |
| 0:45-1:05 | 04 多轮问诊 | 输入常规胸痛问题 | 隐藏信息不主动泄露 | `02_patient_interview.png` |
| 1:05-1:20 | 05 正确解锁 | 直接询问 cocaine/recreational drugs/stimulants | 规则允许后才披露 | `04_correct_hidden_unlock.json` |
| 1:20-1:45 | 06 临床工具 | Vital Signs → ECG → troponin | YAML 决定结果，Trace 记录动作 | `03_clinical_tool_call.png` |
| 1:45-2:05 | 07 安全分支 | 危险回家计划 → Finish | Safety Supervisor 真实阻断 | `04_safety_block.png` |
| 2:05-2:30 | 08 修正闭环 | 补 ECG、紧急监护/转诊、安全网 | 安全后允许评估 | `08_block_then_correct.json` |
| 2:30-2:40 | 09 学情诊断 | Formative Feedback 九维表 | 证据可追溯，不只总分 | `05_learning_diagnosis.png` |
| 2:40-2:50 | 10 个性化复训 | Personalized Remediation Plan | 最低维度生成 Focused Retry | `06_personalized_retry.png` |
| 2:50-2:56 | 11 两轮对比 | Focused Retry Progress | 真实 Demo 80→93，非教学效果证明 | `07_two_round_comparison.png` |
| 2:56-3:00 | 12 教师与开放模板 | Teacher Dashboard / YAML Validator | Trace、模板验证与开放复用 | `08_teacher_dashboard.png` |

## 录屏准备

- 分辨率建议：1440×900 或 1920×1080；浏览器缩放 100%。
- 预先设置：`LLM_PROVIDER=mock`、`APP_ROLE=learner`。
- 预先复制英文问诊、鉴别诊断和处置文本，避免现场输入超时。
- 记录 Session ID，刷新后可用 **Resume structured encounter** 恢复。
- 教师镜头使用单独的受控 instructor 进程或预录素材，避免角色切换污染学习者 Demo。
- 所有 UI 名称以当前英文界面为准；旁白使用中文。

## 录屏后检查

- 未出现完整 patient profile、Rubric、ground truth diagnosis 或未解锁结果。
- 红色安全提示清晰可读，但没有直接泄露标准诊断。
- 画面中的指标与 `evaluation/goai_metrics.json` 一致。
- 80→93 明确标注为当前 Demo 个体比较。
- 不显示 API 密钥、个人路径、终端环境变量或 instructor 隐藏病例内容。
