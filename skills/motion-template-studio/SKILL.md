---
name: motion-template-studio
description: "将用户上传的目标视频拆解、重建和参数化，创建完整可复用的作者 .motion 模板及使用说明、预览、真实验证记录。也用于检查已有作者 .motion 的规范、引用、参数、完整性与运行问题，并非破坏性校正。触发词包括视频转模板、参考视频生成motion、motion检查修复。后期用已有模板制作口播或混剪成片不是本技能的主任务；不得自动改成只交付MP4。"
---

# Motion 模板创建与校正工作室

## 目标与入口

用户只需提供目标视频；工程由助手在工作空间中重建。最终交付新的作者 `.motion`，附使用说明、参考对照预览、验证记录；工程是制作中间产物。不得要求用户先完成工程、不得把诊断骨架打包后冒充目标视频模板。

先列出实际可读取的附件和执行能力。无目标视频时，只请求补充视频或可读路径，可先检查已有模板；不得从截图、文件名或历史讨论虚构全片观察。只有既有模板制作新成片的请求，说明应交由对应模板制作流程；本技能仅提供包审查，不强行重建模板。

设置 `S` 为本 SKILL.md 所在目录，`W` 为本次独立工作目录。不要写入技能安装目录。脚本需 Python3.10+、`jsonschema>=4.26,<5`；媒体需 FFmpeg/ffprobe；打包需 Node22+；渲染需真实可用浏览器及对应引擎。运行 `python "$S/scripts/motion_studio.py" doctor`；缺失项明确记录，已有成果继续保存。

## 1. 识别与证据

阅读 [视频拆解](references/video-analysis.md)。用 `probe` 记录哈希、画幅、帧率、时长、音轨，再连续审看和定向抽帧，关键变化前后追加相邻帧。转写/强制对齐只有实际工具可用时执行，记录工具、版本与时间基准；没有对齐不要用字数均分代替真实时间戳。

输出 `observations.json`，满足 `assets/schemas/observations.schema.json`。把可见事实、实现推断、不可确定项分开；每场景连到证据、源码实现与验收点。用 `validate-observations` 检查结构和全片区间。抽帧不能标记为已完整看过；未知项不得直接编码成“原视频就是如此”。

## 2. 检索与选择代码结构

阅读 [规范与源码依据](references/source-contracts.md) 与 [代码重建](references/authoring.md)。

优先 `search "观察到的结构或动效" --engine 实际引擎`；有 `MOTION_STUDIO_KB` 时增加 `--kb "$MOTION_STUDIO_KB"`。先核实命中项目版本、运行入口、组件接口、许可、验证状态，再读源码。没有私有仓库或MCP连接时使用随技能提供的种子资料，不虚构远程命中或伪装已接入。

相同引擎和契约优先复用结构并针对性改源码。允许保留目录、组件接口、时间轴合同；不要求保留会妨碍参考效果的内部实现。不同引擎显式建立适配，不能只复制文件或改扩展名。保持完整镜头、过渡、尾部动画、背景与声音闭包；局部重建只能标为局部。

## 3. 重建、参数化与渲染

有可用作者工程则复制到新工作目录，先跑基线。没有工程且参考可由纯 HTML/Canvas 确定性逐帧呈现，可运行 `init "$W/project" --name 合法模板ID`，再依据观察替换动画实现。内置项目仅是三秒诊断骨架，不是通用复刻模型。

原生视频、HTML音视频/Web Audio、3D、Remotion或adu原生运行链必须保留/实现适用适配器；内置渲染器不支持时停止受影响的渲染并交代缺项，不可删去媒体后声称完成。按时间驱动 `renderFrame(frame, inputs)`，支持独立跳帧和字体/资源ready。锁定随机性、输出规格与实际依赖。

提炼颜色、字体、布局、文字、素材槽、动作节奏与容量；每个公开参数必须在代码中实际消费，并在使用说明列出边界。长文/多条目要分页、换镜头或给清晰容量反馈；禁止缩小到不可读、裁切、删词。可换内容不等于可以改变用户观点或事实。

渲染器见 starter/tools/render.mjs。纯Canvas固定时长项目可运行：
```bash
node "$W/project/tools/render.mjs" --project "$W/project" --inputs "$W/inputs.json" --out "$W/preview.mp4" --silent
python "$S/scripts/motion_studio.py" verify-render "$W/preview.mp4" --manifest "$W/project/motion.json" --out "$W/media-check.json"
```
`--silent` 只用于本来无声或明确静音的测试；有声音时提供实际音频编排 `--audio-plan FILE`，不能无声交付冒充含声音的参考。命令、报告和证据必须来自实际执行。

## 4. 校验、修复与交付

阅读 [验证与校正](references/validation.md)。静态通过不等于可运行、像参考、可复用。至少检查：包与参数→连续画面/声音→参考对照→新内容替换→干净目录解包后再运行。

每条验证保留 `PASS / FAIL / NOT_RUN / BLOCKED`、输入/输出哈希、工具版本和证据路径。功能性缺口不得被总分掩盖。问题能修则修改工作副本、重跑受影响检查；记录修改前后。对照预览与试听没有执行就不得写通过。

作者工程完成后运行 `pack project --out NEW.motion`，默认从固定官网取当前作者工具、校验公开摘要；联网不可用时可用显式官方缓存 `MOTION_STUDIO_OFFICIAL_BUNDLE=/path/official.zip ... --offline`，仅支持锁定版本。工具未随技能再分发，不能把“缓存缺失”说成已打包。也可用已验证的官方工程入口。再用 `audit NEW.motion --out report.json` 并在干净目录实际试用。

已有作者包先 `audit`；仅根目录多一层或完整性缺陷可 `repair-plan FILE --out PLAN`，再 `repair FILE --plan PLAN --out NEW.motion`。计划绑定源文件哈希，只另存、不覆盖。完整性重算不证明来源可信，也不自动修正视觉；源码/参数/素材错误须在工作副本修复并重打包。

遇到 `personal-download-v1`：只识别外层公开标记，使用公开入口，不读Key、release.bin或受保护core，不重包、不上传、不自动联网验签。作者内容版本与个人封套版本不可互换。

交付包括：`.motion`、人读使用说明、至少一套真实预览、验证JSON与待办。说明支持宿主/依赖、参数、素材角色、容量、时长策略、运行导出命令、许可与已知限制。缺关键运行条件可交付明确标注“待验候选”的已有成果，不能标记正式完成。用户未授权公开时不发布素材、模板或仓库。

## 按需参考

- [视频拆解](references/video-analysis.md)：时间基准、观察证据、镜头/动态字幕分析。
- [代码重建](references/authoring.md)：结构复用、引擎路由、参数和媒体边界。
- [规范与源码依据](references/source-contracts.md)：格式分层、adu实际架构及版本。
- [一手入口索引](references/source-index.md)：规范、Schema、官方样例与固定源码提交。
- [验证与校正](references/validation.md)：验收矩阵、非破坏性修复、声明限制。
- [知识库与本地MCP](references/knowledge-mcp.md)：检索、证据回溯、检查/修复接口与接入。
