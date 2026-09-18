# 个性化推题与生题规则

## 1. 目的与适用范围

本规则定义结构化题库中的诊断推题、个性化生题、质量审核和投放门禁。它适用于
`scripts/recommend_structured_bank.py`、`scripts/generate_personalized_candidate_pool.py`、
`scripts/live_personalized_generation.py` 以及相应验证脚本。

当前实现版本：

- 掌握度：`student-mastery-v3`，模型 `bkt-beta-blend-v1`。
- 离线候选评分：`recommendation-score-v2`。
- 实时生题：`cherry-studio-api-gateway-live-v1`。

## 2. 不可跨越的边界

1. 原始错题、作答记录与人工标签是诊断证据；生题只能作为候选训练材料，不能替换原始证据。
2. 已发布的有效题、疑似题和错题必须先完成去重、标签、难度、答案和解析校验，才可参与推荐。
3. 生成题不得仅通过改数字、改选项顺序或改措辞复用原题结构。
4. 每道生成题必须独立审题。审题服务不可用、审题失败或答案不一致时，题目必须拒绝，不能投放。
5. 生成成功只表示进入待人工审核；只有教师审核为 `approved` 的题目可作为正式交付题。

## 3. 数据与质量门禁

### 3.1 题源优先级

1. 人工核验的原题全文、答案和解析。
2. 结构化题库中的标签、题型、难度和质量状态。
3. 学生作答记录与教师反馈。
4. 可追溯的公开真题或授权题源。

缺失题干全文、答案、解析、知识标签或质量状态的记录，不能进入 `safe_pool`。只有
`safe_pool` 中的题目可被推荐或作为生题参考。

### 3.2 最小题目契约

每道候选题至少包含：`question_id`、`stem_markdown`、`answer`、`solution_markdown`、
`question_type`、`primary_knowledge`、难度、来源和质量状态。选择题还必须拥有且仅拥有
`A` 至 `D` 四个选项，答案必须是有效选项标签。

## 4. 掌握度估计

### 4.1 Beta 平滑

对学生 s、知识点 k，以正确数 c、错误数 w 表示先验平滑后的掌握度：

```text
P_beta(s, k) = (alpha + c) / (alpha + beta + c + w)
```

其中 `alpha`、`beta` 是全局先验。该分数防止小样本的 0% 或 100% 被过度解读。

### 4.2 BKT 递推

记先验掌握概率为 L、作答正确性为 y、猜对率为 G、失误率为 S、学习转移率为 T：

```text
P(correct) = L * (1 - S) + (1 - L) * G
P(L | correct) = L * (1 - S) / P(correct)
P(L | wrong)   = L * S / (1 - P(correct))
L_next = P(L | y) + (1 - P(L | y)) * T
```

当前实现将 BKT 与 Beta 平滑分数混合，输出 `mastery_score`；同时输出
`mastery_uncertainty`。数据量少、近期表现矛盾或证据不足时，不确定度更高。

### 4.3 使用约束

- 目标掌握度不是试卷难度标签，必须按学生的当前 `mastery_score` 和 `mastery_uncertainty` 计算。
- 演示或模拟作答数据只能验证流程，不可用来校准真实教学参数或评价学生能力。
- 真实上线前应按学科、年级、题型分层回测 BKT 参数与难度映射。

## 5. 推荐排序与集合选择

### 5.1 预测成功率

每个候选题 i 使用暂定 1PL 模型估计目标学生的成功率：

```text
P(success | s, i) = sigmoid(ability_s - difficulty_i)
```

优先选择接近目标成功率的题，而不是机械地选择固定难度。低掌握度侧重可完成的巩固题，
高掌握度逐步增加迁移与挑战。

### 5.2 候选总分

候选分数由以下信号共同决定：

```text
utility = knowledge_need
        + weakness_signal
        + target_probability_fit
        + information_gain
        + answer_solution_quality
        + source_quality
        - repeated_exposure
        - feedback_penalty
```

- `knowledge_need`：知识点的掌握缺口与学习优先级。
- `target_probability_fit`：预测成功率与目标成功率的接近程度。
- `information_gain`：约在 50% 成功率附近更能减少不确定性。
- `repeated_exposure`：已推荐或已练习的同题惩罚。
- `feedback_penalty`：教师确认过的质量问题惩罚。

### 5.3 MMR 多样性选择

排序后的题目逐题进入集合时，必须减去它与已选题的最大相似度：

```text
selection_score = utility - lambda * max_similarity(selected, candidate)
```

相似度综合知识路径、题型、难度、题干结构和来源。最终集合应覆盖薄弱知识、不过度重复
同一题型或同一题源，并保留必要的巩固到迁移梯度。

## 6. 离线候选生题

### 6.1 教学链

每个生成位必须来自一个教学链：诊断证据 -> 目标知识 -> 目标难度 -> 题型 -> 练习意图。
新题的 `task_spec` 必须记录诊断锚题、知识点、题型、难度等级、练习意图和结构约束。

### 6.2 单全文锚点

一个生成任务只能使用一题完整题干作为结构锚点。其他原题仅可作为题号、标签、难度和
证据摘要，不可拼接多个完整题干形成新题。

### 6.3 难度等级

| 等级 | 含义 | 生成约束 |
| --- | --- | --- |
| 1 | 识记 | 单一公式、定义或直接计算 |
| 2 | 理解 | 条件辨析或基础变式 |
| 3 | 巩固 | 两步推理，要求过程完整 |
| 4 | 迁移 | 改变情境或表示方式，需要方法选择 |
| 5 | 挑战 | 多条件整合或证明性推理 |

难度应由步骤数、抽象程度、条件耦合、表示转换和方法选择判断；不得只通过增大数值或延长题干提高等级。

### 6.4 教师反馈记忆

反馈只对相同教学指纹生效：知识点、题型、方法族、练习意图、推理结构。对 `solution_error`、
`duplicate_structure`、不适配或难度方向错误的历史反馈施加有上限的负分；不应因某道题被否定而
误伤整个知识点。

## 7. 实时生题与校验

### 7.1 双阶段流程

1. 生成器依据 `task_spec` 和单全文锚点产出草稿。
2. 独立审题器只依据新题题面重新求解，输出状态、答案、完整解析和说明。
3. 系统核验题型结构、选项、答案一致性、难度、知识点、解析过程、重复结构和历史相似度。
4. 通过后写入生成历史，状态保持 `teacher_review.pending`。
5. 教师审核通过后，才允许进入正式交付集合。

生成器和审题器不能互相传递“正确答案”作为验证依据。答案分歧时必须进行第二次独立裁决；
高风险证明题要求更严格的一致性判断。

### 7.2 确定性安全模板

对可精确构造和验证的知识分支，优先使用确定性安全模板、CAS 或精确分数计算。模板题仍需
满足结构去重和教学目标约束；模板可补强可解性，不能绕过内容质量门禁。

### 7.3 服务异常处理

当 Cherry Studio 网关在独立审题阶段返回连接、超时、HTTP 或格式错误时：

1. 已生成草稿写入 `live_personalized_generation_rejections.jsonl`，记录“独立审题服务不可用”。
2. 释放批次中的草稿占位，避免阻塞后续任务。
3. 向调用方返回网关错误；不写入生成历史，不产生待审核题，不允许投放。
4. 后续请求会将该结构视为失败记录，禁止原样或仅改数字后复用。

## 8. 可执行验收

在变更推荐、生题或数据契约后，至少执行：

```powershell
python -m pytest -q smart-question-recommender-v3/tests
python smart-question-recommender-v3/scripts/validate_recommendations.py output/示例题库_structured
python smart-question-recommender-v3/scripts/validate_generated_questions.py output/示例题库_structured --input output/示例题库_structured/generation/student_generated_question_candidates.json
```

有可用网关时，还应完成一次真实的“生成 -> 独立审题 -> 本地契约校验”验收。验收记录必须包含
题目 ID、题型、目标知识、答案、审题状态、难度匹配、生成策略和 `teacher_review` 状态。
网关异常本身也是验收结果：确认草稿被拒绝、记录可审计且不会进入可交付题目集合。

## 9. 运行与监控指标

至少按天和按知识点统计：推荐覆盖率、目标成功率偏差、练习后掌握度变化、重复率、教师拒绝率、
审题失败率、网关不可用率和审核滞留量。指标异常时，先排查数据契约和质量门禁，再调整模型参数；
不能用放宽校验或自动批准来掩盖失败率。
