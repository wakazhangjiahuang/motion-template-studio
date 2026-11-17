# 资料仓库与本地MCP

推荐仓库名motion-template-studio，Private。它是创建、检索、校正、验证的工程底座：规范与来源快照、镜头/动作配方、引擎兼容、作者包校验/修复、回归样例与实际证据。不是素材链接收藏夹，也不是MCP自动识别器。

使用随附assets/catalog.json可离线检索；独立仓库设MOTION_STUDIO_KB=仓库绝对路径。catalog是显式词项匹配，rank_score不是识别置信度；未跑的上游配方保持NOT_RUN/READ_ONLY_REFERENCE。新条目需稳定ID、来源/提交/许可、引擎、触发观察、实现路径、适配条件、验证案例和状态。先用视频观察提取特征再检索，最后靠真实帧和代码排除相似误命中。

安装MCP SDK：`python -m pip install 'mcp>=1.29,<2' 'jsonschema>=4.26,<5'`。配置客户端可使用仓库mcp.example.json的stdio server命令，替换两个绝对路径：MOTION_STUDIO_KB（知识库只读来源）、MOTION_STUDIO_WORKSPACE（允许读取媒体包和另存修复的工作目录）。运行 `python scripts/mcp_server.py`。没有设置工作目录时拒绝访问文件工具，不能任意读取机器文件。

工具：search_recipes、get_recipe、get_source_excerpt、check_compatibility、get_validation_case、audit_motion_package、plan_motion_repairs、apply_motion_repair。来源摘录只能通过catalog登记的source_id读取资料内路径，不能输入任意文件。check_compatibility只比较能力声明，不认证运行；审查/校正调用同一真实校验器。MCP不负责视觉推断、ASR或云渲染。

该服务器是本地stdio实现；没有伪造云端HTTPS地址，私有插件未自动挂载本机磁盘。ChatGPT托管端若不能运行本地进程，使用随技能文件工具或后续授权部署远程MCP；部署、身份认证、对象上传和隔离作业需要单独实施。不能把仓库ZIP或配置示例称为已部署服务。
