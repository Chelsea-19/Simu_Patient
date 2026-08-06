# SimuPatient 原型说明

## 在线 Demo

- 地址：`[待提交前填写 Streamlit Community Cloud URL]`
- 当前状态：尚未发布公开在线实例；本地 MockProvider 原型已通过健康检查。
- 入口角色：公开 Demo 必须使用 `APP_ROLE=learner`。

## 本地运行

Linux/macOS：

```bash
pip install -r requirements.txt
LLM_PROVIDER=mock streamlit run streamlit_app.py
```

Windows PowerShell：

```powershell
pip install -r requirements.txt
$env:LLM_PROVIDER = "mock"
$env:APP_ROLE = "learner"
streamlit run streamlit_app.py
```

浏览器打开终端显示的地址，通常是 `http://localhost:8501`。

## Demo 角色

- 学习者：默认角色，无账号；本地 `learner_id` 建议使用 `demo_learner`。
- 教师：仅受控演示时设置 `APP_ROLE=instructor`，可查看 Action Trace、评分证据和 YAML 验证器。
- 重要边界：`APP_ROLE` 是环境级演示开关，不是生产身份认证。

## 三分钟核心流程

1. 在 **Choose Training** 选择 `chest_pain_001`，填写训练目标并开始病例。
2. 在 **Clinical Encounter** 问诊；先用非相关问题证明隐藏信息不会主动披露，再直接询问娱乐性药物或兴奋剂使用。
3. 调用 **Request Vital Signs**、**Order ECG**，并选择 `troponin` 后调用 **Order Lab**。
4. 提交鉴别诊断以及“回家观察”的危险处置，点击完成，展示 Safety Supervisor 阻断。
5. 补充必要问诊、ECG 和紧急监护/转诊处置，再次完成并进入形成性评估。
6. 在 **Formative Feedback** 展示九维学情画像和 Personalized Remediation Plan。
7. 启动 **Focused Retry**，完成第二轮并展示两轮个体表现对比。
8. 受控切换教师角色，展示训练记录、Trace、安全事件与 YAML Case Template Validator。

## MockProvider

- 无需 API 密钥，不调用外部模型服务。
- 病人回复、工具结果、安全阻断和基础评分可以确定性复现。
- 可选 Gemini/Ollama Provider 不影响核心无 API 演示；使用时必须明确标示实际 Provider。

## 已知限制

- 自动评分仅用于形成性反馈，原 OSCE benchmark 的总分 MAE 为 19.1，并出现 3 个 false fail。
- 当前 15 条 GOAI 轨迹是内部确定性软件评测，不是独立临床验证或教学效果研究。
- 两轮分数变化仅表示当前 Demo 中的个体表现比较，不能证明教学有效性。
- Streamlit Community Cloud 的 SQLite 数据可能在休眠或重部署后重置。
- 当前没有生产认证、长期数据保留或机构隐私治理流程。

## 故障恢复

- 页面状态异常：使用侧栏 **Reset Current Session**，重新创建病例。
- 页面刷新后恢复：展开 **Resume structured encounter**，输入 Session ID 并点击 **Resume Encounter**。
- SQLite 锁定：停止使用同一数据库的重复 Streamlit 进程后重启。
- Gemini 配置错误：改用 `LLM_PROVIDER=mock`，确保无需密钥也能完成核心闭环。
- 工具提示未配置：确认使用胸痛主病例，或在教师 YAML Validator 中检查病例字段。
- 健康检查：访问 `/_stcore/health`；正常结果为 HTTP 200 和 `ok`。

## 安全声明

本原型只用于医学教育模拟和软件研究，不提供医疗建议，不辅助真实诊断或治疗，也不替代教师、临床专家或正式 OSCE 考官。
