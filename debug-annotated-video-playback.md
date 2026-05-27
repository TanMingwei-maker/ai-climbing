# Debug Session: annotated-video-playback
- **Status**: [OPEN]
- **Issue**: 结果页中的特定标注视频 `vid_07d01fc3.annotated.mp4` 无法播放
- **Debug Server**: pending
- **Log File**: .dbg/trae-debug-log-annotated-video-playback.ndjson

## Reproduction Steps
1. 打开结果页并加载 `vid_07d01fc3`
2. 结果页渲染 `<video src="http://127.0.0.1:8000/static/outputs/vid_07d01fc3/vid_07d01fc3.annotated.mp4" />`
3. 观察浏览器是否能加载并播放

## Hypotheses & Verification
| ID | Hypothesis | Likelihood | Effort | Evidence |
|----|------------|------------|--------|----------|
| A | 页面使用的视频 URL 不存在或指向错误资源 | Med | Low | Pending |
| B | 静态文件可访问，但 HTTP 响应头或 Range 支持异常，浏览器无法流式播放 | Med | Low | Pending |
| C | 视频文件编码不是浏览器友好的 H.264/`avc1`，导致 `<video>` 无法解码 | High | Low | Pending |
| D | 文件已被重新生成，但页面仍命中过期缓存或旧版本资源 | Med | Low | Pending |
| E | 前端 `<video>` 节点拿到的 `src` 正确，但缺少错误可视化，导致只表现为“不能播放” | Low | Med | Pending |

## Log Evidence
- `A` rejected：`curl -I` 访问 `http://127.0.0.1:8000/static/outputs/vid_07d01fc3/vid_07d01fc3.annotated.mp4` 返回 `200 OK`
- `B` rejected：带 `Range: bytes=0-1023` 的请求返回 `206 Partial Content`，说明流式播放响应正常
- `C` confirmed：`ffprobe` 显示该文件编码为 `codec_name=mpeg4`、`codec_tag_string=mp4v`
- 该文件路径存在，大小约 `59,497,089` 字节，说明不是空文件或路径失效
- 当前结论：这个具体视频文件仍是旧的 `mp4v` 输出，而不是修复后的 `h264/avc1`

## Verification Conclusion
- 根因已确认：这个具体文件不能播放，是因为它本身仍然使用浏览器兼容性较差的 `mpeg4/mp4v` 编码
- URL、静态资源映射、响应头、Range 支持均正常
- 后续需要使用已修复的编码逻辑重新生成该视频文件，并确认后端已重启到最新代码
