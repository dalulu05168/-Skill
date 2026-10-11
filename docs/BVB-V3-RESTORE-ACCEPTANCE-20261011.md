# BVB v3.3 原版恢复验收单（2026-10-11）

## 来源锁定
已在用户文件库中定位到 `BVB_News_Desk_v3_3_Chinese_Fixed.zip`；原始包包含：
- `BVB_News_Desk_Windows/index.html`
- `BVB_News_Desk_Windows/styles.css`
- `BVB_News_Desk_Windows/app.js`
- `BVB_News_Desk_Windows/materials-data.js`
- `BVB_News_Desk_Windows/BVB_Server.ps1`
- Windows 启动与检测脚本、使用说明

**严禁仅凭截图重新创建占位 UI，也不能将静态预览当成真实功能。**

## 已完成的隔离环境验证
- 原版前端 JavaScript 两个源文件经 Node `--check` 无语法错误。
- 原版 16 节点、编辑控件、TXT 文件导出、桌面 16:9 布局，在浏览器自动化环境测试通过。
- 独立 Python REST 兼容适配器的源地址白名单、RSS UTF-8 中文/罗马尼亚语解析、HTTP 500 失败信息展示测试通过。
- 原版 Windows `BVB_Server.ps1` 以及其余原始程序文件未做覆盖性修改。
- **未确认**用户 Windows/现有上游网络实际采集；离线环境测试不能宣称真实行情/新闻已接通。

## 恢复到模块一的强制验收标准
1. 模块一页面必须来自真正的原版 v3.3 程序，包含完整 `app.js`、`materials-data.js`，不得通过 `tools/build_finance_ui_preview.py` 的只读构建步骤删除脚本、禁用表单或按钮。
2. 保留原来新闻采集、16 节点、资讯搜索过滤、原文核验、稿件编辑、审核门槛和 TXT/JSON 导出能力。
3. 新闻采集需通过同源业务 API 提供 `/api/status`、`/api/refresh`、`/api/article`、`/api/translate`；上游不可用必须显示来源失败，不伪造数据。
4. 原稿件存储在浏览器 localStorage；站点域名改变不能自动继承旧 `127.0.0.1:18986` 的存储。部署前应先保全旧数据。
5. 在正式动态后端、账号登录、持久化策略、上游 API 实测均完成验收前，**禁止将 invest.sasakic.cc 现有服务宣称为已恢复业务版**。
6. 独立项目四交易网站继续独立；模块四仍是本地图片编辑器，不恢复旧外部跳转。
7. 不改其他三个模块的已保存业务数据，不删除线上 Render 服务。

## 当前真实状态
当前分支拥有四合一只读预览站，尚未导入并发布原版 v3.3 全部资源和兼容动态服务；因此线上模块一**仍未完成恢复**。原版恢复源码包已经在本次会话生成并通过独立测试，下一步需将其源码导入仓库并发布到受保护的动态 Web Service 后才能声称完成。

