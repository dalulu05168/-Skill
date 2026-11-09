# 免费开源辅助能力筛选（2026-10-11）

这里只登记阅读过的原仓库及许可证，**尚未安装、复制或接入它们的代码**。要从对应项目提取设计方法，而不是无条件安装多个框架。存在模型调用时仍可能产生费用。

| 项目 | 主仓库 | 已查看许可 | 可移植的思路 | 当前决定 |
| --- | --- | --- | --- | --- |
| Generative Agents | https://github.com/joonspk-research/generative_agents | Apache-2.0 | 记忆检索、反思、按事件推演人物行动；其原版需要OpenAI API，**不直接跑** | P1：先借用方法，自研轻量按角色/时间索引 |
| AI Town | https://github.com/a16z-infra/ai-town | MIT | 多人自然互动、自主选择开口、世界事件状态 | P1：借助行为/互动逻辑，不引入游戏/UI/Convex依赖 |
| Promptfoo | https://github.com/promptfoo/promptfoo | MIT | 固定测试题组，比较提示词输出、重复率、违反人设率 | P1：先写零API结构回归；日后再试有模型调用的eval |
| LangGraph | https://github.com/langchain-ai/langgraph | MIT | 保存状态、任务调度、插播后恢复、局部返工 | P2：演化为自动调用编剧时再选 |
| Mem0 | https://github.com/mem0ai/mem0 | Apache-2.0 | 带时间的长期记忆检索、分角色事件索引 | P2：先用本地JSON/SQLite；不照搬云端基准的性能宣传 |
| Pydantic AI | https://github.com/pydantic/pydantic-ai | MIT | 强类型结构化角色资料/任务交付、Agent接口 | P2：格式稳定后再评估；第一版用JSON Schema |

## 许可证与运行边界
已阅读仓库根 LICENSE；若实际引入代码，必须核对所使用子目录、外部资产、模型和服务各自许可证，保留适当归属、版权及许可文本。直接引用研究构思不等于引入代码，原作者的专有名称和素材也不能误用。

GitHub开放源码≠免费模型调用：Generative Agents原版明确需要OpenAI API key；AI Town提供Ollama等替代方案但完整运行有后台、模型和资源成本；Promptfoo自动生成/评分可能调用付费模型。用户当前手机端操作，因此第一阶段不要引入需要强算力或长期服务器的依赖。

## 原有两套用户技能的使用边界
- 旧人物导演 `skills/romania-market-director/` 的**一般设计方法**，以及研究 Skill `.agents/skills/romania-stock-intelligence/` 的事实核对方法，可以在新项目作为参考文献。
- 新项目的身份、记忆、剧情、配置**不能读写旧目录**；未来若决定导入某个素材，必须逐项说明来源并由用户确认，而不是批量复制旧人物。
