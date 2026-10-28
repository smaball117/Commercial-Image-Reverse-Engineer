# 输入契约和职责映射

## 输入最小单元

优先从聊天中读取用户的图片、图序和需求。标准用法：一张**商品事实图** + 一张**风格参考图** + 输出类型/比例（如未指定可提示候选方案，但不得编造为用户明确要求）。可接受纯文字参考，但必须标注“无可直接观察的风格图”。不要为无关细节连续追问，先用可见事实完成草案。

## 核心数据结构

`assets/brief.template.json` 提供可复制字段；`scripts/validate_brief.py` 实施最低一致性检查。

- `task.mode`: `prompt|audit_repair`；`reference_analysis` 在对话中完成，不需要强行填入 Brief；`task.aspect_ratio` 如 `3:4` 或 `1:1`。
- `assets.subject_image`: 商品源图地址、代号或文件名，非模型自造路径；`assets.reference_images`: 场景参考图列表；`assets.generated_image`: 只有真实生成结果时填写。
- `reference_policy.transfer`: 明确继承哪些可解释的视觉属性，允许：`lighting|palette|composition|camera|depth|background|prop_logic|mood`。
- `reference_policy.exclude`: 不继承哪些参考源元素，如 `brand_identity|product_shape|irrelevant_props|reference_text`。
- `subject`: `identity/category/shape/materials/components/state/must_preserve/provenance/label`。`provenance` 必须为 `identity/shape/materials/components/state` 分别标记 `visible_in_source|user_confirmed|inferred`；四锁必须能够清晰描述。
- `scene`: `concept/background/support_type/support/props/placement/contact/occlusion/physics`。`support_type=physical|suspended|none`。
- `lighting`: `key/fill/rim/contrast/shadows`，数值型光比仅用于设定目标，非图像测量。
- `camera`: `focal_length_equiv/viewpoint/framing/subject_scale/focus/depth_of_field`；焦段空缺应写“建议”，不可声明镜头 EXIF。
- `color`: `dominant/accent/hierarchy/avoid`。
- `negative_constraints`: 仅描述与本次风险相关的禁项。
- `observations`: 记录 `verified_from_image`/`user_provided`/`inferred_or_suggested`/`unknown`，避免把推断写成事实。

## 三类产品文字策略

1. `label.policy=preserve` 且 `exact_text` 由用户确认/可辨识：**保留包装原文字**，只禁止背景额外文字，标识不得被道具遮挡。
2. `label.policy=unverified`：不可凭模糊图像猜文案；提示词要求保留原标签区域/版式，最终建议 Photoshop 原图贴合或局部高保真处理；不写虚构品牌。
3. `label.policy=none` 或 `remove`：在允许的范围内无印刷标识。`remove` 若涉及现有真实品牌，须用户明确指示。

## 五栏判定

| 权限 | 用途 | 示例 |
|---|---|---|
| KEEP | 用户商品不变 | 原瓶盖、印花、品牌字、部件数 |
| TRANSFER | 向参考借摄影法 | 侧逆光、色调、构图、景深 |
| REDESIGN | 在约束内重新规划 | 不同承载面、背景微景观 |
| FORBID | 防模型添加 | 麻绳、木牌、额外包装、伪文字 |
| UNKNOWN | 尚无证据 | 液体实际颜色、标签后几行小字 |

## 来源优先级

用户明确硬约束 > 商品图上清楚可见事实 > 用户批准的创作变更 > 参考图的视觉组织 > 通用摄影知识推断。用户要求与可见素材冲突时指出矛盾并选择不破坏产品的最小解释，不静默改商品。
