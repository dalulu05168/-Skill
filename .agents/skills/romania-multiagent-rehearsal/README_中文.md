# 多智能体集成使用说明（增量包）

## 已完成
- 与仓库既有罗马尼亚导演v2.0并列，不覆盖白天50/45条规则。
- 直接读取 `skills/romania-market-director/characters/profiles/` 的65份原始v4.1档案。
- 人物轮换、角色隔离SQLite记忆、可选Mem0 v3接入、可选TinyTroupe模拟、可选CrewAI财经审核。
- 仅离线三轮选角验证，不等于三轮模型生成结果。

## 三个阶段
1. **离线：** 安装Python；在仓库根目录执行 `python .agents/skills/romania-multiagent-rehearsal/scripts/engine.py three-rounds --topic 'riscurile diversificării' --output three_rounds.json`，然后运行 `python -m unittest discover -s .agents/skills/romania-multiagent-rehearsal/tests -v`。
2. **本地模型联调：** 独立Python3.10–3.12虚拟环境，安装TinyTroupe（GitHub官方入口）、Mem0、CrewAI，配置OpenAI API密钥到本机环境变量。在不暴露凭据的情况下执行 `preflight`，确认环境已就绪。
3. **三轮真实模拟（只用于内部）：** 分别运行下面三个命令，审查生成内容和API开销。即使成功，也不能把虚构成员的消息发布成真实用户证言。

```bash
python .agents/skills/romania-multiagent-rehearsal/scripts/engine.py live-rehearsal --topic 'diversificarea portofoliului' --session 0 --size 5 --steps 2 --ack-internal --output run0.json
python .agents/skills/romania-multiagent-rehearsal/scripts/engine.py live-rehearsal --topic 'diversificarea portofoliului' --session 1 --size 5 --steps 2 --ack-internal --output run1.json
python .agents/skills/romania-multiagent-rehearsal/scripts/engine.py live-rehearsal --topic 'diversificarea portofoliului' --session 2 --size 5 --steps 2 --ack-internal --output run2.json
```

## 注意
- 不会自动发送WhatsApp消息、不会创建定时推送。
- 存储模拟人物使用 `simulation_ro_persona_01..65`，不允许真实电话号码或客户ID。
- 真正行情和真实成员问题必须以外部可验证的来源为依据；无可用来源就不生成时效性的数值。
- 当前仓库仍保留既有导演v2.0与早期课程文本，如果旧文档与最终周一三五技术、周二四理念的晚间安排冲突，以本新增Skill规则为准，后续可统一升级主Skill文档。
- 接入外部模型所需的API密钥需由项目管理员在安全的本地/CI密钥系统配置，不要提交到仓库。
