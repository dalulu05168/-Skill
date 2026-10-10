# 验证记录

> 旧版ZIP验收记录（历史）。2026-10-09 v2.2.0仅完成GitHub源码与配置回读检查：16节点都提前30分钟、备料仍早30分钟、两套核心Skill保留、65份角色文件保留。**未重新打包dist ZIP，未进行跨GPT安装/端到端测试、自动推送或实时行情测试**。

验证了ZIP在新的临时目录解压后SKILL.md入口可读；65份人物编号完整、不重复且保留simulation_only；索引姓名性别及文件名与完整档案一致；全部Markdown相对链接有效；JSON模板可解析；上午试稿有18条对白、5位成员，人物姓名匹配；原始人物档案与生成前字节一致。

上午试稿为假设数据的人工结构验证；没有执行实时行情采集，也未在另一个GPT平台调用模型测试。另一GPT能否自动读取ZIP和仓库依赖其工具能力。课程首次日期和实际开课时间尚未设定。

旧 `dist/` 包不再作为下载源；最新导演资料包通过 `Romanian Skill Quality Gate` 工作流的 `romania-skill-bundles` 构建产物获取，或运行 `python tools/assemble_bundle.py --out-dir build/skill-bundles` 重建。仓库README提供迁移读取步骤。
