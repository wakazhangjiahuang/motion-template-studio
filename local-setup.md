# 本地使用与复测

在解压后的仓库根目录执行。Python3.10+；核心依赖jsonschema4.26–4.x。启用MCP时安装MCP SDK1.29–1.x；安装Node22+、FFmpeg/ffprobe。浏览器渲染还需Playwright和真实可启动的Chromium。

```bash
python -m pip install -r requirements.txt
python skills/motion-template-studio/scripts/motion_studio.py doctor
python skills/motion-template-studio/scripts/test_motion_studio.py
python skills/motion-template-studio/scripts/motion_studio.py search '连续形变 接力' --engine adu-native --kb .
python skills/motion-template-studio/scripts/motion_studio.py audit path/to/author.motion --out workspaces/audit.json
```

命令中的相对输出路径需尚不存在；每次使用新任务目录。工作空间是任务素材/工程/修复副本区；知识资料目录用于来源读取。不要将用户视频、受保护包或凭据提交到仓库。

## 自己运行诊断工程

```bash
python skills/motion-template-studio/scripts/motion_studio.py init workspaces/diagnostic --name diagnostic-local
npm install --prefix workspaces/diagnostic playwright
npx --prefix workspaces/diagnostic playwright install chromium
node workspaces/diagnostic/tools/render.mjs --project workspaces/diagnostic --inputs workspaces/diagnostic/presets/demo.json --out workspaces/preview.mp4 --silent
python skills/motion-template-studio/scripts/motion_studio.py verify-render workspaces/preview.mp4 --manifest workspaces/diagnostic/motion.json --out workspaces/media.json
```

系统已有浏览器时可设置CHROME_PATH为浏览器可执行文件路径。Linux/macOS为环境变量，Windows可在PowerShell设置 `$env:CHROME_PATH='C:\...\chrome.exe'`。Playwright及浏览器安装按官方文档和本机权限完成；二进制存在不能证明能启动。

本示例是固定3秒无声Canvas诊断。制作目标模板时必须重建实际组件/时长/素材和声音，不只改标题。含HTML音视频或Web Audio的工程需要对应媒体适配器；内置runner明确拒绝。外部audio-plan支持显式音轨混合，但仍需试听，不隐式裁切口播。

## 官方打包

```bash
python skills/motion-template-studio/scripts/motion_studio.py pack workspaces/diagnostic --out workspaces/diagnostic.motion
python skills/motion-template-studio/scripts/motion_studio.py audit workspaces/diagnostic.motion --out workspaces/package-audit.json
```

默认公共GET下载当前MotionGit作者工具，核验BUILD、外部版本元数据与脚本SHA。没有发送模板内容或用户凭据。联网不可用时，明确提供事先下载且与锁定摘要一致的官方ZIP作为MOTION_STUDIO_OFFICIAL_BUNDLE并加--offline；未提供则明确失败。缓存工具不随本发行包复制。

## 本地MCP

编辑mcp.example.json，把仓库和工作目录换为本机绝对路径，在支持本地stdio MCP的客户端添加。命令为 `python /ABS/REPO/mcp/server.py`。工作目录需存在；超出该目录的文件读取/校正均拒绝。

8个工具：search_recipes、get_recipe、get_source_excerpt、check_compatibility、get_validation_case、audit_motion_package、plan_motion_repairs、apply_motion_repair。最后一项只写新文件；计划由源SHA绑定。get_source_excerpt只允许已登记source_id；知识库包括所有adu快照文件的登记项。

托管插件不自动连接你本地磁盘。这个ZIP提供已测试的本地服务代码和配置；若要云端独立MCP，后续需实施身份认证、上传接口、作业隔离和部署，不将此示例标为已上线。

## 重新构建插件包

运行 `python tools/build_plugin.py /ABS/NEW-plugin.zip`，会从本仓库Skill源文件和plugin/plugin.json生成单一私有插件ZIP；已有输出会拒绝覆盖。此命令只构建本地包，发布/更新需使用有权限的插件创建流程。
