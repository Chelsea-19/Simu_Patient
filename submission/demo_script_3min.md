# SimuPatient 三分钟演示脚本

## 0:00-0:20｜问题与定位

**画面：** 封面后切到学习目标页。

**旁白：**

“真人标准化患者训练昂贵且机会有限，而普通 AI 问答往往只给答案，难以稳定记录学生怎样问、查了什么、为何做出决策。SimuPatient 是面向医学生和教师的自适应临床推理与 OSCE 训练 Agent：把一次虚拟问诊变成可追踪、可诊断、可复训的学习闭环。”

## 0:20-0:45｜选择目标与病例

**操作：** 在 **Choose Training** 选择 `Acute chest pain with cardiac risk factors`，展示 learner ID、训练目标和难度，开始病例。

**旁白：**

“本次目标是高危胸痛的重点问诊、证据获取和安全处置。比赛主 Demo 使用结构化 YAML 胸痛病例；学生端只看到人口学信息、主诉和开场白，标准答案、Rubric 与未解锁检查不会进入学习者状态。”

## 0:45-1:20｜问诊与隐藏信息

**操作：** 先问疼痛起病、程度等常规问题；展示未主动出现药物史。再直接输入：`Have you used cocaine, recreational drugs, or stimulants recently?`

**旁白：**

“Patient Agent 不能自己补写病例事实。近期可卡因使用是隐藏信息，只有直接或语义等价询问娱乐性药物或兴奋剂时，确定性 disclosure 规则才允许披露。Prompt injection 也不能越过这条边界。”

## 1:20-1:45｜调用临床工具

**操作：** 依次点击 **Request Vital Signs**、**Order ECG**，选择 `troponin` 并点击 **Order Lab**；展开最新临床工具结果。

**旁白：**

“这不是纯聊天机器人。生命体征、查体、ECG 和 troponin 都是结构化工具调用；结果由 YAML 病例决定，Python 状态机负责阶段、时间成本、证据解锁和 Action Trace，LLM 无权把检查改成正常。”

## 1:45-2:05｜危险处置被阻断

**操作：** 提交鉴别诊断；处置填写 `discharge home to observe symptoms`，点击完成，停留在红色 Safety Supervisor 提示。

**旁白：**

“对于高风险胸痛，如果关键检查不足又选择回家，Safety Supervisor 会阻止结束。反馈不会直接说出标准诊断，而是要求学习者重新检查危险原因、必要检查和处置地点。该安全事件同步写入 Trace。”

## 2:05-2:30｜修正并完成首次训练

**操作：** 补做 ECG，完善急诊监护、紧急升级和安全网建议，再次提交并完成评估。

**旁白：**

“学习者补齐证据并改为紧急监护路径后，系统允许进入形成性评估。确定性清单与 Trace 决定基础分和安全判断，语言模型只补充受限的表达质量反馈。”

## 2:30-2:50｜学情诊断与复训

**操作：** 切到 **Formative Feedback**，展示九维画像、最低维度、Personalized Remediation Plan，点击或指向 **Start Focused Retry**。

**旁白：**

“系统不只给总分，而是诊断病史采集、沟通、临床推理、红旗识别、检查选择、处置安全、共情、收尾和效率。Learning Planner 依据最低的一到三个维度生成 Focused Retry，并采用三级提示策略陪伴练习。”

## 2:50-3:00｜两轮对比与开放复用

**操作：** 展示真实对比截图：80 到 93；快速切到教师 Dashboard/YAML Validator。

**旁白：**

“当前 Demo 的个体表现从 80 到 93，这不是教学有效性证明。教师可追溯完整过程并验证 YAML；项目以 MIT License 开放病例 Schema、工具接口、安全规则、MockProvider 和评测轨迹。”

## 演示底线

- 不称自动评分为正式 OSCE 成绩。
- 不称项目完成临床验证、医院部署或真实诊疗能力。
- 不展示 instructor 模式给学习者，也不在公开 Demo 中设置 `APP_ROLE=instructor`。
- 如果现场网络不可用，始终使用 MockProvider 完成全流程。
