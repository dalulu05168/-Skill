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

## 更新：一条命令连续执行三轮真实模型内部模拟
前提：三套可选框架和 OpenAI 模型访问已由管理员安全地配置在本地虚拟环境，先运行 `engine.py preflight`。请勿在公开仓库、日志、聊天中粘贴密钥。此步骤可能产生API费用。

在仓库根目录（Windows PowerShell 或终端）执行：

```powershell
python .agents/skills/romania-multiagent-rehearsal/scripts/live_batch.py --topic "diversificarea și gestionarea riscului" --output-dir ./private_rehearsals/first_real_run --ack-internal
```

输出仅用于内部模拟，不是实际真实WhatsApp成员发言。执行后生成：
- `rehearsal_round_1.json`
- `rehearsal_round_2.json`
- `rehearsal_round_3.json`
- `run_summary.json`

**必须人工审核**：发言自然度、人物性格、罗马尼亚语准确性、重复率、虚构收益/持仓、来源时间和隐私。任何轮次失败，会停止后续生成并写入 `INCOMPLETE_DO_NOT_USE`；已有输出不会覆盖。禁止将生成的虚构“成员”话语作为真实用户观点在投资群发布。建议将 `private_rehearsals/` 目录加入本地 `.gitignore` 或保存在工作区之外；请勿推送生成记录到公开仓库。

## 验收层级
- **L1 离线**：结构与安全逻辑无密钥自动测试，包括额外的三轮批处理假模型测试。
- **L2 模型联调**：要看见 `run_summary.json` 中 `actual_runs_completed=3` 才算真实调用了模型。
- **L3 内容审校**：真实模型运行成功仍不等于内容合格或具备发布许可；必须人工核验。
