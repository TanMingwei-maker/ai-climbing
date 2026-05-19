# AI Climbing

基于 `MediaPipe Pose` 的攀岩姿态分析 MVP。

当前版本支持：

- 读取本地视频
- 检测人体关键点
- 导出骨架标注视频
- 计算基础姿态指标
- 输出简单的攀岩动作建议

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
- `*.analysis.json`：分析摘要和动作建议

## 当前分析指标

- 平均肘关节角度
- 平均膝关节角度
- 髋部相对双脚中点的水平偏移
- 双手高度差

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
