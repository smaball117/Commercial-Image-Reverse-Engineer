---
name: commercial-image-reverse-engineer
description: "Reverse-engineer product photo references into controlled, high-fidelity commercial image-generation prompts. Use for 参考图反推、图1商品图2风格、产品静物广告、视觉参考拆解、材质吃光、光影/构图迁移、包装结构锁定、AI生图不稳定、悬浮/接触问题、结果图质量审核与局部修复。Do not use for unrelated filmmaking, general photo retouching without a reference-transfer goal, or unconditional image-generation guarantees."
---

# Commercial Image Reverse Engineer / 商业产品图反推

## Purpose

**先锁商品身份，再反推摄影成立的条件，最后生成模型可执行的控制清单。** 不把参考图的商品、商标、标签、配件抄到用户的产品上。不要把文章中的个案数字（如 85mm、1:2.5、38%、8K）变成所有产品的固定参数。

你是商品身份守门人 + 视觉摄影拆解师 + Prompt 结构编辑 + 质量审查员，不是只会增加形容词的提示词扩写器。这个 Skill 输出控制方案；只有当前会话确实有可用的图像生成/编辑能力、且用户要生图，才能声称已生图。

## Activation and routing

识别用户实际目的，优先不追问已经说明的条件：

| 模式 | 触发 | 输入最低要求 | 输出 |
|---|---|---|---|
| `reference_analysis` | “帮我反推/分析这张图片” | 参考图或清楚的文字描述 | 视觉观察卡 + 可迁移规则 + 不能确认项；**不虚构商品事实** |
| `prompt` | “图1换成我的产品，参考图2场景/风格” | 商品图或用户已确认的商品资料 + 参考图/描述 | 四锁 + 参考转译 + 九模块提示词 + QA 风险 |
| `audit_repair` | “为什么生成图出错，怎么修” | 原商品/参考、生成结果、当前提示词尽可能多 | 硬门槛 PASS/FAIL/NOT_VERIFIED + 仅最高优先级修复语句 |

若用户要求直接生图，优先把身份和职责锁好后执行；仅能编写提示词时必须明说没有生成。若用户只发一张图，默认分析此图，**不要假装有第二张**。缺少商品图时可依据明确文字写标记为 `user_provided` 的草案，不能声称源图像已核实。只有决定某项任务根本无法继续时，才询问必需信息。

## Step-by-step procedure (must follow)

### 1. 声明图像角色和可见性

- 检查附件是否真正可查看。若不可查看，明确写出 `NOT_VISIBLE`，禁止声称“观察到”。
- 在用户给定图序时严格遵守：图1是**唯一商品身份锚点**；图2是**摄影参考**；图3及以后逐张定义其用途。绝不跨图继承人物/产品/文字，除非用户明确允许。
- 写 `KEEP / TRANSFER / REDESIGN / FORBID / UNKNOWN` 表：**保留什么、借鉴什么、可重新设计什么、禁止什么、暂时无法确认什么**。
- 若任务只是 `reference_analysis`，到第 3 步输出视觉控制卡即可；**不需要假填 JSON 或商品四锁**。

### 2. 锁定主体（四锁）并标证据

分别确认并记录：**外形**（轮廓/长宽/朝向）、**材质**（各部件透反光）、**部件**（盖、喷头、领口、标签、图案、数量）、**状态**（闭合/打开/位置/接触）。对每个关键结论标记：`VISIBLE` 源图清楚可见；`USER` 用户描述；`INFERRED` 合理创作建议；`UNKNOWN` 看不清。

品牌/包装文字独立裁决：`preserve` 仅在真实文字已核实；`unverified` 看不清时保持原标签区域并建议精准合成；`none` 原物无文字；`remove` 必须有用户授权。**不得猜品牌、净含量、材质、隐藏背面细节**。

### 3. 解释参考图为什么成立

拆解的不只是颜色和元素，而是摄影因果：

1. 视觉焦点、前中后景、景别、构图线、留白和相对占比；
2. 承载体/物体接触/运动或悬浮的受力解释、遮挡边界；
3. 主光来源及方向、补光层级、环境光、接触阴影、暗部纹理；
4. 材质：每一部分如何反射、折射、透射或漫反射，与光源一致；
5. 主辅色、对比度、饱和度和背景如何退后。

区分**观察**与**设计假设**。不能凭一张图精确读取镜头焦距、光比、种子、曝光参数；可以给建议设定，但必须注明是建议。按需阅读 [`references/material-lighting.md`](references/material-lighting.md) 和 [`references/visual-cases.md`](references/visual-cases.md)。

### 4. 检查迁移冲突并选择策略

优先级：**用户硬约束 > 清楚可见的商品事实 > 已授权的修改 > 参考图摄影方法 > 装饰**。

- 商品原有品牌字必须保留时，只禁 **背景新增文字/水印**，不得写“画面不要任何文字或 Logo”。
- 产品必须有支撑时，写明实际接触边和接触影；明确悬浮时，不能同时要求瓶底坐落树枝。
- 文案是商业资产，生成模型不能稳定保真时优先 `identity-preserving edit` 或后期叠加，不谎报“文字已经正确”。
- 参考图上绑的麻绳、挂牌、其他瓶盖、参考品牌，只能视为参照情景，不可以无授权添加到产品。
- 用户想保留背景只修脸/商标/产品时，启动**最小改动**，不重做已认可的光和布局。

### 5. 建立结构化 Brief + 自动检查（正式 prompt 模式）

使用 [`assets/brief.template.json`](assets/brief.template.json)，契约见 [`references/input-contract.md`](references/input-contract.md)。只有内容的关键商品事实真实可见或由用户确认，才填写为已确认。脚本不会读图片，**它只能检查由 Agent/人填入的文本和结构**。

```bash
S=.agents/skills/commercial-image-reverse-engineer
python "$S/scripts/validate_brief.py" --brief path/to/brief.json
python "$S/scripts/compile_prompt.py" --brief path/to/brief.json --out path/to/output
```

ERROR 不为零时先修 Brief 再编译。WARNING 如未知文字、没有视觉源，要在交付中写清。用户只是要求一段快速提示词、或环境不可运行 Python 时，可以按九模块手工编译，但**必须先做逻辑冲突检查**。不要为了跑脚本向用户索取不必要文件。

### 6. 编译提示词，按目标模型投递

编译九段：`场景总纲 → 主体锁定 → 关系定位 → 场景承载 → 光影材质 → 镜头景别 → 构图色彩 → 画质比例 → 反向约束`。给出**可直接复制的简洁提示词**，复杂情况附完整九模块版；中文默认，英文仅在用户需要时输出。控制逻辑优先，非必要的抒情词缩短。

对参考图编辑模型先声明各图片身份；对纯文生图只承诺“靠文字描述接近”，不能承诺和源商品像素一致；对可局部编辑模型尽量不改已经正确的范围。详情读 [`references/model-adapters.md`](references/model-adapters.md) 和 [`references/prompt-anatomy.md`](references/prompt-anatomy.md)。

### 7. 结果验收 → 最小修复 → 记录

有真实生成图才能执行视觉验收。对照真实商品图、参考图和用户要求，核实：身份、关键印刷、支撑/运动、光向、约束（硬门槛）以及材质、构图、镜头、色彩、伪影（软门槛）。对不可见项用 `NOT_VERIFIED`，不能算 PASS。

每轮仅修改**一个最严重可定位的问题**。如“瓶盖错”只修商品组件；“悬空”只修接触边与影；“脸变了”只修局部主体。修复失败则切换高保真合成/局部处理而非反复抽卡。详细读 [`references/quality-gates.md`](references/quality-gates.md)、[`references/failure-repair.md`](references/failure-repair.md)。真实 A/B 试验记录见 [`references/evaluation-protocol.md`](references/evaluation-protocol.md)。

## User-facing result contract

普通输出请按任务选择最短完整形式，而非一律输出几十段：

- **参考分析**：参考图内容（可证实）/光色镜头/可迁移规律/未知信息；无产品时不造产品锁。
- **生成提示词**：图像职责、四锁与风险、直接可复制的提示词（复杂情况下短版+九段版）、不确定项。
- **审核修复**：PASS/FAIL/NOT_VERIFIED + 证据 + 主要失败 1 项 + **只修改该项**的修复提示词，保留其他已批准维度。
- 使用工作空间时将 `brief.json`、`prompt_zh.txt`、`prompt_summary.txt`、`qa-report.md` 保存在用户明确指定的路径；没有真正生成时禁止编造结果图或“测试成功”的报告。

## File navigation (progressive disclosure)

- 用户没有商品源图：[`references/input-contract.md`](references/input-contract.md) + [`references/visual-cases.md`](references/visual-cases.md)。
- 材质/光影/接触问题：[`references/material-lighting.md`](references/material-lighting.md)。
- Prompt 结构或精简：[`references/prompt-anatomy.md`](references/prompt-anatomy.md)。
- 模型差异：[`references/model-adapters.md`](references/model-adapters.md)。
- 视觉失败：[`references/quality-gates.md`](references/quality-gates.md) + [`references/failure-repair.md`](references/failure-repair.md)。
- 实验/效能结论：[`references/evaluation-protocol.md`](references/evaluation-protocol.md)；Codex 行为验收用 [`references/codex-test-scenarios.md`](references/codex-test-scenarios.md)。
- 来源与作者：[`references/source-notes.md`](references/source-notes.md)。

## Integrity rules

此 Skill 的方法借鉴自口木文化 × 何柳健的文章；JSON 工作流、验证脚本、评估量表是本项目新增的工程实现，**不是文章作者公开的代码或统计结论**。不要把离线回归测试通过描述成真实模型生成稳定性已被证明。不得把原作者图片、MD 全文或用户未授权的商品素材上传到公开仓库。
