# Debug Session: analyze-500-error
- **Status**: [OPEN]
- **Issue**: `POST /api/videos/{video_id}/analyze` 返回 500 Internal Server Error
- **Debug Server**: pending
- **Log File**: .dbg/trae-debug-log-analyze-500-error.ndjson

## Reproduction Steps
1. 启动 `api` 服务
2. 调用 `POST /api/videos/vid_f71c2c65/analyze`
3. 观察后端 traceback 与调试日志

## Hypotheses & Verification
| ID | Hypothesis | Likelihood | Effort | Evidence |
|----|------------|------------|--------|----------|
| A | `api` 运行环境缺少分析依赖，导入或执行 `ClimbingPoseAnalyzer` 时抛异常 | High | Low | Pending |
| B | 数据库里虽然有 `video_id`，但对应视频文件路径不存在或不可读 | High | Low | Pending |
| C | 分析过程中输出目录/静态文件写入失败，导致接口在运行中抛异常 | Med | Low | Pending |
| D | `route_context.json` 或视频内容触发了 `pose_pipeline` 中的运行时错误 | Med | Med | Pending |
| E | `api` 与核心项目的 Python 版本/路径注入不一致，导致运行到分析阶段时模块行为异常 | Med | Med | Pending |

## Log Evidence
- `B`: 视频记录存在，且文件路径 `/Users/tan/Desktop/ai-climbing/data/uploads/vid_f71c2c65.mov` 可读
- `C`: 标注文件和输出路径都已正常准备
- `D`: `ClimbingPoseAnalyzer.analyze_video()` 内部在加载 `route_context.json` 时抛错：
  `TypeError: float() argument must be a string or a real number, not 'NoneType'`
- 定位到 `src/ai_climbing/route_context.py` 中：
  `wall_angle_deg=float(wall["angle_deg"]) if "angle_deg" in wall else None`
- 触发数据是：
  `data/annotations/vid_f71c2c65.route_context.json` 里的 `"angle_deg": null`

## Verification Conclusion
- 已确认：
  - `A` rejected，分析器已成功初始化并开始执行
  - `B` rejected，视频文件存在
  - `C` rejected，输出路径已创建
  - `D` confirmed，`route_context` 解析 `null angle_deg` 时崩溃
  - `E` rejected，当前异常与 Python 路径无关
- 修复：
  - 将 `load_route_context()` 改为仅在 `angle_deg is not None` 时执行 `float(...)`
- 修复后验证：
  - 在 `8001` 新实例上重新执行 `POST /api/videos/vid_f71c2c65/analyze`
  - 调试日志显示 `analyze_video finished successfully`
  - `GET /api/videos/vid_f71c2c65/result` 返回 `status=succeeded`
  - 产物已生成：
    - `data/outputs/vid_f71c2c65/vid_f71c2c65.analysis.json`
    - `data/outputs/vid_f71c2c65/vid_f71c2c65.annotated.mp4`
