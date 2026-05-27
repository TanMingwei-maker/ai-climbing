# AI Climbing

基于 `MediaPipe Pose` 的攀岩姿态分析 MVP。

当前版本支持：

- 读取本地视频
- 检测人体关键点
- 导出骨架标注视频
- 计算基础姿态指标
- 输出简单的攀岩动作建议
- 提取四肢静止片段
- 聚类候选接触点并导出动作序列
- 在标注视频中叠加候选接触点与当前附着状态

## 适合的第一版场景

- 室内抱石
- 单人出镜
- 固定机位
- 侧视或斜侧视角度

## 工程结构

```text
ai-climbing/
├─ data/
│  ├─ annotations/
│  └─ videos/
├─ outputs/
├─ examples/
│  └─ route_context.sample.json
├─ src/ai_climbing/
│  ├─ cli.py
│  ├─ metrics.py
│  ├─ move_sequence.py
│  ├─ pose_pipeline.py
│  ├─ route_context.py
│  └─ rules.py
└─ tests/
```

## 安装

建议使用 `uv`：

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

说明：

- 项目要求 `Python >= 3.11`
- 请优先使用项目 `.venv` 内的 Python，避免误用系统自带的旧版本 Python
- 当前代码已验证兼容 `mediapipe==0.10.14`

## 运行

将测试视频放到 `data/videos/`，然后执行：

```bash
python -m ai_climbing.cli data/videos/demo.mp4
```

如果你没有先 `source .venv/bin/activate`，也可以直接执行：

```bash
.venv/bin/python -m ai_climbing.cli data/videos/demo.mp4
```

如果你已经有墙面/路线点位标定文件，也可以附带传入：

```bash
.venv/bin/python -m ai_climbing.cli \
  data/videos/demo.mp4 \
  --route-context examples/route_context.sample.json
```

执行后会在 `outputs/` 下生成：

- `*.annotated.mp4`：叠加骨架和基础指标的视频
- `*.annotated.mp4` 现在还会额外显示候选点编号、四肢当前附着状态和最近的换点事件
- `*.analysis.json`：分析摘要、动作建议、候选岩点和动作序列
- 如果传入 `--route-context`，输出里还会包含 `route_context`，并为部分候选点补上 `route_hold_id`

## 当前分析指标

- 平均肘关节角度
- 平均膝关节角度
- 髋部相对双脚中点的水平偏移
- 双手高度差

## 当前动作序列输出

- `holds`：从四肢静止片段聚类得到的候选接触点
- `contacts`：某个肢体在某个候选点上的稳定接触片段
- `move_sequence`：按时间排序的换手/换脚附着事件
- `route_context`：可选的墙面/路线标定信息
- `route_move_sequence`：优先使用真实路线点 ID 的动作序列；如果某个点未映射，则回退到候选点 ID
- `phase_segments`：基于 `route_move_sequence + contacts` 切出的动作阶段，当前提供 `start / transition / finish`

## 路线标定文件格式

示例文件见 [route_context.sample.json](file:///Users/tan/Desktop/ai-climbing/examples/route_context.sample.json)。

```json
{
  "wall": {
    "name": "Demo Wall",
    "angle_deg": 10
  },
  "route": {
    "name": "Blue Demo"
  },
  "holds": [
    { "id": "S1", "x": 0.41, "y": 0.75, "role": "start" },
    { "id": "H1", "x": 0.48, "y": 0.61 },
    { "id": "T1", "x": 0.48, "y": 0.10, "role": "top" }
  ]
}
```

说明：

- `x` 和 `y` 使用相对于视频画面的归一化坐标，范围通常是 `0.0 ~ 1.0`
- `id` 是你希望最终在视频和 JSON 中看到的真实路线点名称
- `role` 是可选字段，可用于标记 `start`、`top` 等语义
- 当标定命中时，`holds`、`contacts`、`route_move_sequence` 都会附带 `route_hold_id`
- 阶段切分会优先利用 `role=start/top/finish`；如果没有这些标注，则退回到基于事件分位数的启发式切分

说明：

- 这一版仍然是 `MVP`，候选点来自人体关键点反推，并不等同于真实岩点识别
- 更适合固定机位、单人、遮挡较少的视频
- 候选点会经过近邻合并和短暂抖动去噪，但仍可能出现碎点或误合并
- 结果适合做回放和后续规则分析，不适合直接当作高置信度教练建议

## 当前建议规则

- 上肢发力偏多
- 下肢参与度偏低
- 髋部离支撑区域偏远
- 上肢高度差较大

## 下一步建议

- 加入关键帧切分
- 增加重心变化与转髋检测
- 加入路线阶段识别
- 为不同水平的攀岩者设置不同阈值
