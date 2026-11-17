# 外部参考的具体用法与边界

## OpenEdit

https://github.com/veedstudio/open-edit

固定提交：e4dc93892268eaf04b64386935ba6e53098a5c79；许可：Apache-2.0。

用法：后期字幕、素材剪辑、HTML动效与渲染流程候选。

代码定位：cli/src/render/timing.ts；cli/src/render/footage.ts；.github/README.md。

边界：CLI与浏览器渲染路线；转写可选本地或服务端，付费能力不是前期必需项。状态：定向源码/文档核读；未进行集成或运行验证。

## Video Shotcraft

https://github.com/Vincentwei1021/video-shotcraft

固定提交：42f922fe076f6428814d10f6184caf22a8b2adc2；许可：Apache-2.0。

用法：前期镜头识别、动作阶段、参考实现与验收反例。

代码定位：references/shots/data/before-after-slider-scrub.md；对应demos。

边界：基于Remotion，不能直接视为adu或HTML/Canvas组件；本轮未安装运行。状态：定向源码/文档核读；未进行集成或运行验证。

## FireRed-OpenStoryline

https://github.com/FireRedTeam/FireRed-OpenStoryline

固定提交：c9e945215586f45c12a61c1951ee9a8e9c43a027；许可：Apache-2.0。

用法：后期B素材理解、剪辑编排和风格工作流候选。

代码定位：src/open_storyline/nodes；.storyline/skills；README.md。

边界：MCP/剪辑Agent并非.motion作者打包器；新脚本生成与粗剪默认不纳入保留原内容流程。状态：定向源码/文档核读；未进行集成或运行验证。

## Overlay Studio

https://github.com/jeszhou/overlay-studio

固定提交：e35e1aff9dae3b3addc21f68f3bcd51f95bdc1a8；许可：自定义源码公开许可。

用法：语义选卡、SRT时间线、固定卡片参数和透明动效层。

代码定位：LICENSE；motion-playground/src/effects/registry.ts。

边界：不属于OSI开源；限制软件及修改版商业再分发和同类对外服务。私有仓库并不扩大原许可。状态：定向源码/文档核读；未进行集成或运行验证。

## Motion Prompt

https://github.com/showheyohtaki/motion-prompt

固定提交：683ecca0548a1754ada141d10dc3a009d4c59bef；许可：MIT。

用法：把画面观察映射为动作名称、运镜词汇、规格与样例。

代码定位：packs/motion；packs/camera；skills/motion-prompt/references/porting.md。

边界：命名和样例不等于自动识别正确，也不等于任意引擎即插即用。状态：定向源码/文档核读；未进行集成或运行验证。

## Creator Style Kit

https://github.com/threeaus/creator-style-kit

固定提交：6aeb1ba22913dbc75b3dea0f9e131cfa78422504；许可：MIT（仓库自有部分）。

用法：字体、配色、构图、组件、动作与声音规则拆分。

代码定位：REFERENCE.md；styles/<id>/style.yaml；runtime/kit.js。

边界：基于HyperFrames；字体、第三方运行库和音效分开核查，不能直接套到另一运行器。状态：定向源码/文档核读；未进行集成或运行验证。

## 视觉词汇参考

https://atlas.letz.ai/ ：仅链接和原创观察笔记，不复制动效视频或图库。

https://idearocketanimation.com/13721-12-principles-of-animation-gifs/ ：动画原则教学参考，非原始出版资料；不复制GIF或整篇文章，不以本文替代实际运动验证。
