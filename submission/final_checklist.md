# SimuPatient 初赛最终检查

## 总体结论

**READY WITH RISKS**

本地原型、无 API 闭环、评测、PPTX、PDF 和文字材料均已完成并验证。尚未填写公开
Streamlit Demo URL，也未在最终提交平台执行人工上传检查，因此不能标记为无条件 READY。

## 作品定位

- [x] 属于 AI+教育：定位为临床推理与 OSCE 形成性训练 Agent。
- [x] 个性化学习明确：按最低 1-3 个维度生成 Focused Retry。
- [x] 学情诊断明确：九维画像包含分数、证据、遗漏、风险和练习。
- [x] 教师辅助明确：Dashboard、Trace、报告导出和 YAML Validator 已实现。
- [x] 不是泛问答：闭环围绕结构化临床案例训练。
- [x] 有完整用户流程：目标、问诊、工具、决策、安全、评估、复训与比较。

## 原型

- [x] 本地可运行：`LLM_PROVIDER=mock streamlit run streamlit_app.py`。
- [x] 可完成核心闭环：GOAI 作者定义场景 15/15 达到预期结果。
- [x] 无 API 可运行：关闭 socket 访问时完整闭环 1/1。
- [x] 不泄露隐藏答案：负向探针提前披露 0/7；隔离测试通过。
- [x] 安全阻断真实存在：危险出院 3/3 被阻断。
- [x] 个性化复训真实存在：Focused Retry 与两轮比较已运行并截图。
- [ ] 公开在线 Demo URL：尚未部署/填写，是当前主要提交风险。

## 技术

- [x] Agent 架构清楚：五个职责组件在 PPT 第 5 页展示。
- [x] 工具接口清楚：八个结构化接口在 PPT 第 7 页与文档中展示。
- [x] YAML 数据来源和责任边界清楚。
- [x] 状态机、Action Trace 和恢复机制清楚。
- [x] 本地、Mock、Gemini 可选与 Streamlit Cloud 部署方式清楚。
- [x] 15 条评测轨迹、指标分母和运行命令可复现。

## 合规

- [x] 当前主 Demo 不使用真实患者数据。
- [x] secret scan：扫描 231 个文本/提交包内容，0 个密钥特征命中。
- [x] 无临床有效性、医院部署或真实用户规模夸大。
- [x] 明确不替代教师、临床专家或正式 OSCE 考官。
- [x] Provider、第三方依赖和自动评分限制已声明。
- [x] MIT `LICENSE` 存在。
- [x] learner/instructor 数据边界和公开 Demo 角色边界已说明。

## 材料

- [x] 中文简介正文 480 字符，不超过 500。
- [x] PPTX 10 页；Office 成功打开并导出 PDF；`slides_test.py` 无溢出。
- [x] PDF 10 页、未加密；pypdf/pdfplumber 可打开，Poppler 可逐页渲染。
- [x] 8 张截图来自真实本地原型并已视觉检查。
- [x] PPT/PDF 中的指标与 `evaluation/goai_metrics.json` 一致。
- [x] Demo 脚本中的 UI 名称与当前界面一致。
- [x] 已完成内容与未来路线图在 PPT 第 10 页明确分开。
- [x] PPT 每页包含 `[Sources]` 讲者注释，共 10 页注释。

## 真实验证摘要

- pytest：67/67 通过（Phase 7 最终回归）。
- disclosure benchmark：challenge precision/recall 1.000/1.000，提前披露率 0.000。
- OSCE benchmark：MAE 19.1，pass/fail agreement 0.7，false fail 3，missed-item 0.432。
- GOAI evaluation：15/15 作者定义场景达到预期；Action Trace 152/152。
- no-API Demo：1/1。
- secret scan：0 findings。

## 人工提交前必须完成

1. 部署公开 learner 模式 Streamlit Demo，并把 URL 写入 `prototype_guide.md` 和提交表单。
2. 在最终展示电脑上打开 PPTX/PDF，确认微软雅黑字体、截图和图表显示一致。
3. 按三分钟脚本录制视频，检查画面不出现本地路径、密钥或 instructor 隐藏内容。
4. 填写团队名称、负责人、联系方式等本仓库没有提供的比赛平台字段。
5. 上传全部文件后重新下载，核对页数、文件大小和 SHA-256。
6. 由医学教师/临床专家人工复核病例内容和所有对外医学表述。
