# Commercial Image Reverse Engineer

**可被 Codex 自动发现的商业摄影反推 Agent Skill**。将「图1是我的产品，参考图2的风格」转化为可追溯的**主体身份锁定 → 参考视觉拆解 → 控制规格 → 提示词 → 验收 → 单变量修复**闭环。

> 不复刻其他品牌的产品；从参考图借的是构图、光线、景深、材质呈现和空间组织。**默认中文提示词**，不虚构未看清的文字，不假装 8K、绝对保真或模型成功率已经验证。

## 1. 项目结构（Codex 原生识别）

```text
Commercial-Image-Reverse-Engineer/
├── AGENTS.md
├── README.md
├── .gitignore
├── .github/workflows/skill-check.yml
└── .agents/skills/
    └── commercial-image-reverse-engineer/
        ├── SKILL.md                 # 唯一执行入口（YAML frontmatter）
        ├── agents/openai.yaml       # Codex 技能卡名称与默认调用语句
        ├── references/              # 按任务加载，而非全文灌入上下文
        ├── assets/                  # brief / QA / iteration 模板
        ├── scripts/                 # 无第三方依赖，验证/编译
        ├── examples/                # 虚构产品，展示不同任务模式
        └── tests/                   # 结构、冲突、输出回归
```

`SKILL.md` 在 `.agents/skills/...` 是因为 **Codex 从项目根目录启动时会搜索 `.agents/skills`**。全局使用请将整个 `commercial-image-reverse-engineer` 子目录复制到 `~/.agents/skills/`，而不是把仓库根目录复制进去。

## 2. 在 Codex 中使用

1. 在 Codex 打开/克隆**这个仓库**，通过 `/skills` 或 `$` 检查是否显示 `commercial-image-reverse-engineer`。
2. 在同一个对话中提供商品原图（图1）与摄影参考图（图2），明确画幅、产品必须保留的细节。
3. 发送：

```text
$commercial-image-reverse-engineer
图1是我的商品身份锚点，图2是视觉参考，不得继承图2的品牌/包装/配件。
先列图像职责与「可见事实 / 用户提供 / 推断 / 未知」，
再交付九模块中文控制提示词、短版、冲突检查。
如果已有生图结果，优先诊断并只修复最严重的一个问题。
```

若 Codex 没看到图像附件，就只根据明确文字建立草案并标记未知，不得声称「已分析图片」。

## 3. 离线验证（复制执行）

从仓库根目录执行：

```bash
S=.agents/skills/commercial-image-reverse-engineer
python -m unittest discover -s "$S/tests" -v
python "$S/scripts/validate_brief.py" --brief "$S/examples/forest-serum.brief.json"
python "$S/scripts/compile_prompt.py" --brief "$S/examples/forest-serum.brief.json" --out output-demo
```

只验证规则与编译，不会自行生成图像。`output-demo` 是本地临时文件，已由 `.gitignore` 排除。

## 4. 三种可见工作模式

- **参考分析**：只需参考图，输出镜头、布光、构图、光学关系的控制卡，不伪造商品四锁。
- **构图迁移 / 生成提示词**：图1商品 + 图2参考，完整主体四锁、迁移裁决、正式九模块提示词。
- **结果审核 / 定向修复**：输入原图、生成图和已批准提示词，核对硬约束，优先修正一个失败维度。

## 5. 用户自己的验收和持续升级

真实视觉测试建议比较三组任务：实体承托（林间瓶）、悬浮流体（玻璃与水）、含准确包装文字（高风险）；每组同模型同参数比较朴素 prompt 与本 Skill，保留所有结果。参考 [`references/evaluation-protocol.md`](.agents/skills/commercial-image-reverse-engineer/references/evaluation-protocol.md)。

## 6. 来源及边界

框架受到口木文化 × 何柳健于 2026-10-19 发表的[《AIGC-为什么你的反推图片质量差？》](https://www.zcool.com.cn/work/ZNzQyODA1NDg=.html)启发。图片页码索引在 `references/visual-cases.md`；本文没有搬运原文图片、完整正文，也不声称本文作者提供了这些校验脚本和评分模型。项目所有示例产品为原创虚构案例。当前仓库是 **Public**，请不要提交商业客户原图。

## 7. 交给 Codex 的测试剧本

在[Codex 行为验收剧本](.agents/skills/commercial-image-reverse-engineer/references/codex-test-scenarios.md)里有 T1–T8。将真实输入图放在 Codex 会话中，逐项检查逻辑、接触、文字和最小修复。离线回归测试通过并不意味着真实图像生成质量已验证。
