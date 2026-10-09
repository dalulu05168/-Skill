# BVB准确性增强技能包 v1.0

本包是**4个专属SKILL + 6份开源技术参考**，服务现有导演v2.3.0、股票资讯核验V2.1；不是第三方依赖安装或运行时服务。请按以下次序调用：

1. 事实、行情、公告→[bvb-fact-check](../bvb-fact-check/SKILL.md)
2. 新闻新旧、去重、重大分级→[news-priority](../news-priority/SKILL.md)
3. 助理、教授、65名虚构模拟成员→[character-consistency](../character-consistency/SKILL.md)
4. 稿件完成前→[script-qa](../script-qa/SKILL.md)

6份原始技术文件见 [第三方来源记录](../../third_party/orchestra-research/README.md)，它们是参考资料，不得覆盖当前课表、人物设定、核实要求、发布授权。保留原项目MIT许可证。

**未完成**：没有安装Instructor、Sentence Transformers、Phoenix；没有部署跨来源语义去重服务、自动行情订阅、自动群发。BVB行情500错误仍需独立修复。运行`python tools/test_accuracy_pack.py`检查文件结构。