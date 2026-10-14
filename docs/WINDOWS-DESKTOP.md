# Windows 桌面版

## 目标平台

Windows 10/11 x64。应用以独立桌面窗口运行，不要求最终用户安装 Python；安装器会在 WebView2 Runtime 缺失时调用微软签名的 WebView2 安装引导程序。

桌面版只保留新闻审核、65人模拟交易和图片编辑，不显示“财经 Skill”入口，也屏蔽其桌面路由/API。浏览器源码版仍保留原来的 Skill 页面与资料，未删除仓库内容。

## 生成并领取安装器

仓库包含 GitHub Actions 工作流 `.github/workflows/windows-desktop-installer.yml`。将本次项目改动提交到 GitHub 后：

1. 打开仓库 **Actions → Windows Desktop Installer**。
2. 选择 **Run workflow**，或等待代码变更后的自动构建。
3. 构建成功后，在对应运行记录底部下载 `RomaniaFinanceSkillHub-Windows-x64-Installer` 工件。
4. 解压后运行 `RomaniaFinanceSkillHub-Setup.exe`。

也可在已装 Python 3.11 x64 的 Windows 构建机运行 PowerShell：

```powershell
./scripts/windows/build-installer.ps1
```

此命令安装/使用 PyInstaller 与 pywebview、校验微软 WebView2 安装引导程序的数字签名，使用 Inno Setup 6 生成 `dist/installer/RomaniaFinanceSkillHub-Setup.exe`。它只生成安装包，不发布 GitHub Release。

## 安装后的行为

- 开始菜单快捷方式启动 NUVEXA 财经工作台；安装时可选创建桌面快捷方式。
- 页面与 API 在本机随机端口、仅绑定 `127.0.0.1`，由桌面 WebView 显示；应用退出时关闭本地服务。
- 新闻/交易/人物等应用数据保存在 `%LOCALAPPDATA%\NUVEXA\RomaniaFinanceSkillHub`，应用升级和卸载时都不删除该目录。
- 两份内置模板（战绩表、推票/买卖卡）及自定义模板均在本机浏览器内存中绘制；导出的 PNG 由浏览器下载，不上传到服务器。买入/卖出成交时间自动居中填入；卖出理由由用户填写。
- 卖出卡图表使用随安装包内置的 TradingView Lightweight Charts 与 Yahoo Finance 历史日线数据，自动绘制白底无网格线图、截图并嵌入模板；读取行情需要网络。若数据源暂不可用，页面会提示重试，不会提交订单或伪造走势。
- 股票元数据识别也需要网络；如果数据源不可用，可手动填写公司、市场和模拟价格。返回报价仅供模拟单参考，必须人工确认，模拟买卖不会提交真实订单。
- 原有 `START-FINANCE-SKILL.cmd` 仍保留，供开发者以浏览器方式启动源码版。

## 当前环境限制

Manus 当前执行环境是 Linux Sandbox，不能在这里直接产出或验证 Windows `.exe`。本轮新增的模板、数据映射与前端静态资源尚待用户批准同步至公开仓库；获批推送后，Windows Actions 工作流会在 Windows runner 上重新生成安装器。未完成该 Windows 构建前，不把源码改动称为已更新的 `.exe`。
