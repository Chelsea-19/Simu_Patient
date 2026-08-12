# SimuPatient 初赛提交清单

## 提交包状态

**READY WITH RISKS**：材料完整，公开在线 Demo URL 待人工部署后填写。

## 必交与辅助文件

| 文件 | 用途 | 核验结果 |
|---|---|---|
| `project_intro_zh.md` | 500 字符以内中文作品简介 | 480 字符，PASS |
| `SimuPatient_GOAI_Preliminary.pptx` | 10 页初赛方案 | 10 slides、10 notes、无溢出，PASS |
| `SimuPatient_GOAI_Preliminary.pdf` | PPT 的固定版式导出 | 10 pages、未加密、逐页渲染，PASS |
| `prototype_guide.md` | 本地/在线入口、角色与故障恢复 | 在线 URL 为占位，RISK |
| `demo_script_3min.md` | 三分钟旁白和操作脚本 | 与当前 UI 对齐，PASS |
| `demo_shot_list.md` | 录屏镜头与备份证据 | 12 镜头，PASS |
| `final_checklist.md` | 最终定位、技术、合规与材料审计 | READY WITH RISKS |
| `submission_manifest.md` | 提交文件和证据索引 | PASS |

## 二进制文件指纹

| 文件 | 字节数 | SHA-256 |
|---|---:|---|
| `SimuPatient_GOAI_Preliminary.pptx` | 151836 | `bac6265a52737445599a0845bb107f797fe1a1049e9a3d8721d3c543a17b09b3` |
| `SimuPatient_GOAI_Preliminary.pdf` | 503642 | `2a7128b03957a352771499b25df2f02802cd9895a40a15dedd6c61ca09a94d99` |

## 核心证据索引

- 指标源：`evaluation/goai_metrics.json`
- 评测解释：`evaluation/goai_evaluation_report.md`
- 场景明细：`evaluation/results/goai_scenarios.json`
- Action Trace：`assets/demo_traces/01_correct_complete.json` 至
  `assets/demo_traces/15_session_recovery.json`
- 真实截图：`assets/screenshots/01_learning_goal_selection.png` 至
  `assets/screenshots/08_teacher_dashboard.png`
- 部署说明：`docs/deployment.md`
- 病例编写：`docs/case_authoring_guide.md`
- 工具接口：`docs/tool_interface.md`
- 状态隔离：`docs/state_separation.md`
- 许可：`LICENSE`（MIT）

## 指标口径

- “任务闭环 15/15”表示 15 个作者定义场景均达到各自预期系统结果；其中危险场景的
  正确结果是阻断，不表示每个 encounter 都进入评估。
- “工具调用错误率 4%”包含故意调用不存在检查以及预期安全阻断，不能解释为随机故障率。
- “80 -> 93”只来自当前 Demo 的个体两轮比较，不能作为教学有效性证明。
- 原 OSCE benchmark 的 MAE 19.1、3 个 false fail 和 missed-item 0.432 必须与优秀的
  确定性安全/流程指标同时展示。

## 未包含或待人工填写

- 公开 Streamlit Community Cloud URL。
- 三分钟最终录屏文件。
- 团队名称、成员、联系方式与比赛平台账号字段。
- 临床专家背书、真实学生研究或机构合作证明；项目当前没有这些证据，也不得虚构。
