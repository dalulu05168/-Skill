# 罗马尼亚财经统一工作台：invest.sasakic.cc 部署指南

**项目对应**：`dalulu05168/-Skill`。包含 BVB 新闻审核、16 节点、交易中心及正式 65 人物资料。**绝对不是** `brantone-veylor-romania` 网站。外部交易平台 `trade.sasakic.cc` 不受影响。

## 当前完成边界

`render.yaml` 是可导入 Render 的云端服务定义，尚不表示服务、DNS 或 HTTPS 已经成功开通。不能仅凭 GitHub 绿灯声称部署成功。

## 用 Render Blueprint 建立安全工作台

1. 在 Render 连接能访问私有 GitHub 仓库 `dalulu05168/-Skill` 的账号；在 **New > Blueprint** 选择该仓库的 **main** 分支，读取仓库根目录 `render.yaml`。
2. 首次创建时输入 `FINANCE_ACCESS_PASSWORD`，必须是至少 16 位的独立强密码；**不要**把密码、API Key、角色历史或用户数据提交到仓库或发在聊天里。账号默认 `admin`，可在 Render 环境变量中另行更改。
3. Blueprint 配置新加坡区的 Python Web Service、1 GB 持久磁盘挂载 `/var/data`、`/healthz` 存活检查，`autoDeployTrigger: checksPass`。启用服务与持久磁盘可能产生费用，创建前查看 Render 账单页面。
4. Blueprint 为服务预登记 `invest.sasakic.cc`。服务创建成功后，进入 **Settings > Custom Domains** 核对该名称。
5. 在 `sasakic.cc` 的权威 DNS 管理后台**只为 invest 主机**创建 CNAME，指向 Render 显示的该服务专属 `*.onrender.com` 主机名。Cloudflare 初次验证时选 **DNS only**，不要凭空填写 IP，不要更改 `trade`、`crm` 或根域名等其他记录，也不要设置错误的 AAAA。
6. 回 Render 点击该自定义域名的 **Verify**，待证书激活，验证 `https://invest.sasakic.cc/` 要求账号密码；`/trading`、`/trade-platform`、`/api/trading/people` 均不得未授权访问。验证 `/healthz` 返回真实可用状态。

## 安全与运行边界

- `--host 0.0.0.0` 才启用公网监听，且没有足够长的 `FINANCE_ACCESS_PASSWORD` 就拒绝启动。Windows 本地双击启动脚本仍监听 `127.0.0.1`，不需要密码，也不影响本地数据。
- 云端初始数据盘为空；**不会**自动搬运个人电脑中 `~/.romania-finance-skill-hub` 的历史文件。迁移需要先备份、核对并由管理员通过安全方式单独导入，禁止把私有数据提交到 GitHub。
- 原浏览器客户端保存或浏览的草稿在服务端新数据盘存储，不会无故标记为“已发布”；真正的 WhatsApp 推送、行情 API、自动群发及真实交易仍未接通。
- 本机 Ollama 没有自动迁到 Render。云端模型状态应显示未就绪，不应把云端未安装模型说成可用，也不要开启未授权公网 Ollama 接口。
- 主持人／65名角色都是**明确披露的虚构教育模拟角色**，不能冒充真实客户、制造假投资收益或向外群发送虚构真实业绩。
- 上线前确认单一管理员是否满足需求。HTTP Basic Auth 适合当前受限私人工作台，**不等于多用户权限体系**。正式多用户使用前应另行实现会话、细分角色权限、审计、登录限速等能力。
- 持久磁盘不能代替异地备份；应配置备份与恢复演练。

## 预检

GitHub Actions 的 `Romanian Skill Quality Gate` 会验证所有旧功能；新增 `tools/test_finance_skill_hosted.py` 会随 `test_finance_skill*.py` 执行，检查认证保护、跨域拦截、65人人物读取、新闻候审持久化及健康检查。

最终公网验收必须分别证明：DNS 指向目标服务、Render 域名已验证、HTTPS 证书有效、访问受保护、正确账号登录、三个页面可打开、真实 65 人数据可读取且状态写入可保留。任何一项未过都不标记“上线完成”。
