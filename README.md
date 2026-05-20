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
├─ src/ai_climbing/
│  ├─ cli.py
│  ├─ metrics.py
│  ├─ move_sequence.py
│  ├─ pose_pipeline.py
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

执行后会在 `outputs/` 下生成：

- `*.annotated.mp4`：叠加骨架和基础指标的视频
- `*.annotated.mp4` 现在还会额外显示候选点编号、四肢当前附着状态和最近的换点事件
- `*.analysis.json`：分析摘要、动作建议、候选岩点和动作序列

## 当前分析指标

- 平均肘关节角度
- 平均膝关节角度
- 髋部相对双脚中点的水平偏移
- 双手高度差

## 当前动作序列输出

- `holds`：从四肢静止片段聚类得到的候选接触点
- `contacts`：某个肢体在某个候选点上的稳定接触片段
- `move_sequence`：按时间排序的换手/换脚附着事件

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
