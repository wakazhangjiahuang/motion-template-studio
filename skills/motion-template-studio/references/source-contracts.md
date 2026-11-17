# 一手资料与精确合同（核读日期2026-11-17）

事实来源：MotionGit spec/spec.md、内容JSON Schema、公开作者工具BUILD与其外部版本元数据；adu-motion-video固定提交4ae737a04107083288c02eab5c0861834fcc0364。仓库source-manifest记录选取文件和哈希；不要把滚动main当作永久版本。

## MotionGit分层

- 作者内容：format=motiongit-template，specVersion精确0.1.0-draft.1，ZIP根motion.json。Schema核心required只有format/specVersion/template/runtime/output；完整可复用交付还须参数、素材、指南、依赖闭包、许可和真实预览。
- 运行：runtime.profile与适配器决定执行能力。格式不锁定模型或动画引擎；在线API可选，不是生成motion的必要条件。
- 个人分发：外层1.0.0-rc.1 / personal-download-v1；与作者内容版本不同。签名/Key/保护core不属于本工具校正范围。
- Schema根允许未知可选元数据；保留它们，遇到未知执行或权限语义需提示并停止受影响操作。Schema结构合法≠引用齐全≠可运行≠高质量。
- variants当前上限24；每项preset须真实存在且满足参数Schema。完整性使用sha256，内容变更需重新生成；重算不能使不可信代码可信。

## adu实际技术路线

这是已有风格/模板库及内容适配、运行导出的一套代码工作流，有大量可复用工程组件；不是任意MP4自动恢复原源码的完整系统。当前README优先导向MotionGit下载新版，旧版Skill/工程仍可维护。不能把旧库每种资源和新版受保护下载包视为相同源码。

关键模块（在资料仓库sources/adu-motion-video/保留上游路径）：

| 文件 | 技术作用 | 对本系统的用法 |
|---|---|---|
| scripts/pipeline.py | 内容到制作管线的编排入口 | 阅读其子命令/输入输出后复用；不直接宣称MP4→motion |
| scripts/extract_authored_pack.py | 从已有作者工程提取可用包内容 | 借鉴完整依赖闭包，不把素材目录节选当完整模板 |
| scripts/authored_units.mjs | 作者单元/片段的承接和组织 | 对齐单元接口、长度、转场和源码引用 |
| scripts/adapt_project.py | 依据新内容适配工程 | 后期接口参考；前期参数通用化与边界测试依据 |
| scripts/build_macro_project.py + macro_runtime.js | 宏镜头编排与运行 | 保留连续动作和转场，不仅组静态字幕卡 |
| scripts/render_project.mjs + export_project.py | 浏览器/渲染与导出 | 以真实入口、依赖和声音链实测，不靠文件存在判断运行 |
| references/template-intake.md | 模板接入约束 | 案例→结构识别→验证→回归 |
| references/adaptive-composition.md | 内容适配与构图 | 保留表达、适配长短内容，超容显式处理 |
| references/automatic-selection.md | 选择可用片段/模板 | 先能力与内容关系匹配，再美术相似度 |
| references/portrait.md | 竖屏布局 | 重新布局而非裁切横屏；检查安全区和遮挡 |
| references/quality-upgrade.md | 质量规则 | 作为测试线索，不能替代本次实测 |

本系统的“视频→观察合同→代码重建→可复用参数→验证→作者打包”补齐上游工程创建环节。生成质量仍取决于可见证据、实际代码实现和运行修正，不是由格式Schema推导出来。

## 外部资料边界

OpenEdit、OpenStoryline是后期独立适配候选；Shotcraft/ Motion Prompt提供镜头或动作配方，需核对引擎；Creator Style Kit为HyperFrames风格合同。Overlay Studio使用自定义受限源码许可，不直接纳入商用可分发组件。Atlas/IdeaRocket只保留链接和原创观察笔记，不复制视频、GIF、截图库。私有仓库不扩大上游许可。

官方工具入口https://github.com/adunext/motiongit-skill要求从完成工程开始。生产默认公共官网取当前bundle并按公开元数据验证；离线仅接受锁定的公开下载副本。官方工具源码本技能不再分发，也不把这项下载能力写成已安装的云端服务。
