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
- 图片模板在当前页面浏览器内存中处理；导出的 PNG 由浏览器下载，不上传到服务器。
- 股票元数据识别需要网络；如果数据源不可用，可手动填写公司、市场和模拟价格。返回的价格仅是参考报价，必须人工确认，模拟买卖不会提交真实订单。
- 原有 `START-FINANCE-SKILL.cmd` 仍保留，供开发者以浏览器方式启动源码版。

## 当前环境限制

Manus 当前执行环境是 Linux Sandbox，没有可用 Windows runner/桌面，也没有已授权的 GitHub 写入连接。因此这里可以准备并测试源码、打包脚本与 CI，但**不能在本沙箱直接产出或验证 Windows `.exe`**。Windows Actions 工作流必须在这些文件提交到用户仓库后，才能用 Windows runner 生成安装器；不可把源码包称为已生成的安装程序。
