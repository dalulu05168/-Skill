# 在 Codex 中使用 Romania Stock Intelligence

## A. 直接在 GitHub 仓库内使用（无需本地安装）

本仓库已将技能发布到 `.agents/skills/romania-stock-intelligence/SKILL.md`。在 Codex 中选择 GitHub 仓库 `dalulu05168/-Skill`，重新打开会话或刷新工作区。Codex 将从仓库根目录自动发现 `.agents/skills/` 下的技能。需要的话可输入 `$romania-stock-intelligence` 明确调用。

> 该技能仅在当前仓库 / 工作区自动发现，并不自动在你打开的其他仓库生效。

## B. 使本地 Codex 对其他仓库也生效

将本压缩包解压，执行 `scripts/install-windows.ps1` (Windows PowerShell) 或 `scripts/install-unix.sh` (Mac/Linux)。默认复制到用户级 `$HOME/.agents/skills/romania-stock-intelligence`。关闭并重新打开 Codex；也可在 Codex 使用 `skill-installer` 从 GitHub 路径安装到其管理的技能目录。

GitHub 安装源（仅发布完成后可用）：
`https://github.com/dalulu05168/-Skill/tree/main/.agents/skills/romania-stock-intelligence`

## C. 验收指令

`$romania-stock-intelligence 请生成今天的罗马尼亚市场晨报，逐项给出数值、单位、比较基准、观测时间及时区、具体来源、延迟状态和上次简报变化；未能核验的标记待核验。`

## 重要限制

Skill 无法自己开通实时行情 API、创建自动任务或跨工作区安装。三个罗马尼亚时间自动推送时段的规范已写入文件，但必须单独启用自动任务才会定时发送。消息仅在 ChatGPT 内，不通过邮件。
