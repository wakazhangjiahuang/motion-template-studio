# 验证矩阵与校正边界

| 层 | 方法/证据 | 不能证明什么 |
|---|---|---|
| 包结构 | strict JSON、精确Schema、路径/碰撞、引用、preset/variant、素材摘要/许可字段、integrity成员哈希 | 不执行源码，不认证许可所有权 |
| 工程运行 | 真实引擎启动、依赖版本、随机跳帧/资源ready、无console错误 | 不证明视觉像参考 |
| 编码 | ffprobe规格/帧数、FFmpeg完整解码 | 不证明没有黑屏/错字/坏动作或好听 |
| 保真 | 原片与重建同时间对照；逐场景/关键动作、完整连续看和听 | 图片相似分数不能代替语义与运动判断 |
| 复用 | 真实替换内容和边界preset渲染，检查实际换字/色/媒体、容量反馈 | demo能跑不等于各种内容都能跑 |
| 交付 | 干净目录解包、不依赖作者机器的绝对路径、按说明再导出 | 同一作者自测不是独立用户验收 |

每项记录状态PASS/FAIL/NOT_RUN/BLOCKED、输入SHA、输出SHA、工具版本、命令、证据文件和审看范围。无人真正试听时listening=NOT_RUN；只有metadata检查不能标视觉/运动通过。没有真实目标参考就不签发“视频转模板保真通过”。正式发布前由不同使用者在声明的Codex/WorkBuddy等实际客户端照说明试用；不能将编写者自测称为外部独立证据。

静态审核故意不执行模板代码，也不提取受保护内容。`audit`返回STATIC_PASS仅表示本工具已实现的作者合同检查通过，其他字段仍NOT_RUN。未知manifest可选信息保留。第三方profile静态可读但未必有本地runner；要求其原入口实测。

非破坏性自动校正仅限：单层包裹目录展平、作者包完整性清单重建。repair-plan绑定源SHA，repair重新计算可做操作并比对计划，拒绝旧源/空计划/覆盖目标。修复结果若仍有其他错误返回FAIL；必须查看剩余问题。个人分发封套不校正。重建哈希会接受当前字节，但不证明它们是可信原版。

视觉或代码错误：复制为版本化工作副本→定位观察与代码映射→最小修改→重跑相关场景与容量→官方重打包→全包审查→干净目录复测。不要自动重写原包、删未知文件或用原始参考视频铺满背景掩盖复刻不足。

命令速查：
```bash
python "$S/scripts/motion_studio.py" audit source.motion --out audit.json
python "$S/scripts/motion_studio.py" repair-plan source.motion --out plan.json
python "$S/scripts/motion_studio.py" repair source.motion --plan plan.json --out corrected.motion
python "$S/scripts/motion_studio.py" pack project --out authored.motion
```
不能将官方inspect和官网检查作为两个完全独立的运行证据：它们可能共享规则。结合不同实现的JSON Schema、本地静态检查、真正渲染、FFmpeg解码及外部用户试用。
