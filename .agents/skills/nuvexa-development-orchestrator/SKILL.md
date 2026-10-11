---
name: nuvexa-development-orchestrator
description: 编排已连接的编程插件，协调现有GitHub源码的开发、测试、独立验收与发布授权；不将计划当成已执行结果。
---
# Nuvexa 编程总协调 Skill

## 适用场景
当用户要求在真实 GitHub 项目里开发功能、修复错误、建设底层框架时使用；不干涉金融新闻、人物编剧及其他业务 Skill。

## 严格步骤
1. 读取真实 GitHub 仓库目录、默认分支、PR 和已有测试，避免新建无关系统或覆盖其他工作。
2. 为每项具体任务建立隔离工作分支。用 python -m dev_framework.orchestrator init 生成任务记录，所有阶段默认待办；不得虚写通过状态。
3. GitHub 负责代码及提交；Replit/Floot 仅在确认可直接读写同一源码时负责实现；Context7 提供可靠技术文档；Superpowers 提供调试与测试方法。
4. 如需 Supabase/Neon，先核对目标库、备份、迁移和权限。禁止自动处理真实客户财产或生产数据。
5. 实际运行项目的单元/接口/浏览器测试，记录失败和修复，之后交给独立的 .agents/skills/nuvexa-independent-acceptance/SKILL.md 复查。
6. 调用已有 delivery_gate/validator.py 检查真实证据和精确提交 SHA。无实际登录、无手机/桌面验证、无独立复核均必须 BLOCK；框架自测不是业务验收。
7. 合并主分支、生产部署、修改DNS、产生费用须分别获得用户明确授权，且需部署权限隔离。文字宣称和 JSON 状态不能代替批准。

## 事实状态输出
- “已写入独立分支” = GitHub 实际提交成功；
- “框架自测通过” = 只保证协调程序本身的测试通过；
- “业务验收通过” = 项目真实证据+独立复核+受保护CI合格；
- “已正式部署” = 真实部署记录且获得授权。

这些状态不可混用。不具备跨插件自动编排权限时直接说明，不得制造后台联动或运行成功的假象。

详细用法：dev_framework/README.md。
