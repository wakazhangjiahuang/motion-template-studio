# 创建GitHub私有仓库

建议账户：wakazhangjiahuang；名称：**motion-template-studio**；可见性：**Private**。

仓库描述建议：`Private video-to-motion authoring toolkit: evidence-based reconstruction, reusable code recipes, package audit, non-destructive repair and regression validation via local MCP.`

1. GitHub点击New repository，填名称并选择Private。
2. ZIP先在本机解压。网页Upload files上传解压后motion-template-studio目录里的内容，不能只上传ZIP本身，也不要再套一层目录。文件数多时使用GitHub Desktop添加解压目录并发布为该私有仓库。
3. 检查根目录含README.md、skills/、knowledge/、sources/、mcp/、verification/。保持上游LICENSE和THIRD_PARTY资料。
4. 在Codex/WorkBuddy运行环境取得仓库本地副本，设置MOTION_STUDIO_KB为其绝对路径；接本地MCP时另设MOTION_STUDIO_WORKSPACE。
5. 增加新motion示例前先确认作者源码/授权/可分发素材；保留来源版本和实际测试。个人授权封套与Key不入库。

本交付提供上传包与命名，未创建远程仓库、未设置协作者权限、未部署MCP云服务。完成上传前技能使用随附的本地种子资料，不依赖一个尚未存在的私有远程地址。
