# Debug Session: result-video-playback
- **Status**: [OPEN]
- **Issue**: 分析结果已生成，但结果页上的视频无法播放
- **Debug Server**: pending
- **Log File**: .dbg/trae-debug-log-result-video-playback.ndjson

## Reproduction Steps
1. 启动前后端服务
2. 完成一次分析，进入结果页
3. 观察视频播放器是否加载、请求的资源 URL、接口返回与浏览器行为

## Hypotheses & Verification
| ID | Hypothesis | Likelihood | Effort | Evidence |
|----|------------|------------|--------|----------|
| A | 结果页拿到的 `result_video_url` 不正确，前端拼接后的地址不可访问 | High | Low | Pending |
| B | 后端静态目录已挂载，但 `outputs` 目录没有被正确暴露，返回了 404/403 | High | Low | Pending |
| C | 视频文件存在，但浏览器拿到的响应头或 MIME 类型不合适，导致播放器不认 | Med | Med | Pending |
| D | 前端结果页状态逻辑有问题，`video` 标签没有真正拿到 `src` 或被错误状态覆盖 | Med | Low | Pending |
| E | 生成出来的 MP4 文件编码浏览器不兼容，文件存在但无法解码播放 | Med | Med | Pending |

## Log Evidence
- `A` rejected：结果页视频地址会拼成 `http://127.0.0.1:8000/static/outputs/vid_f71c2c65/vid_f71c2c65.annotated.mp4`
- `B` rejected：`curl -I` 返回 `200 OK`，且 `content-type: video/mp4`、`accept-ranges: bytes`
- `C` rejected：范围请求 `Range: bytes=0-1023` 返回 `206 Partial Content`
- `E` confirmed：
  - 旧结果视频 `ffprobe` 显示 `codec_name=mpeg4`、`codec_tag_string=mp4v`
  - 该编码在浏览器中兼容性较差，容易导致页面上 `<video>` 无法播放
- 修复后：
  - `pose_pipeline.py` 输出编码由 `mp4v` 改为 `avc1`
  - 新生成结果视频 `ffprobe` 显示 `codec_name=h264`、`codec_tag_string=avc1`

## Verification Conclusion
- 根因已确认：前端页面不能播放的主要原因是结果视频采用了 `mpeg4/mp4v` 编码，而不是浏览器更稳定支持的 `h264/avc1`
- 最小修复已完成：输出视频改为 `avc1`
- 后续需要用户在重启后端后重新生成一次结果视频，并在页面验证播放
