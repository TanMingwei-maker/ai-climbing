from __future__ import annotations

import argparse
from pathlib import Path

from ai_climbing.pose_pipeline import ClimbingPoseAnalyzer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="使用 MediaPipe 分析攀岩视频姿态。")
    parser.add_argument("input", type=Path, help="输入视频路径")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="输出目录，默认是 outputs",
    )
    parser.add_argument(
        "--route-context",
        type=Path,
        help="可选的路线标定 JSON，用于将候选点映射到真实路线点",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    analyzer = ClimbingPoseAnalyzer()
    output_video = args.output_dir / f"{args.input.stem}.annotated.mp4"
    output_json = args.output_dir / f"{args.input.stem}.analysis.json"
    result = analyzer.analyze_video(
        args.input,
        output_video,
        output_json,
        route_context_path=args.route_context,
    )

    print("分析完成")
    print(f"总帧数: {result.total_frames}")
    print(f"成功分析帧数: {result.analyzed_frames}")
    print(f"标注视频: {output_video}")
    print(f"分析结果: {output_json}")
    matched_count = sum(1 for hold in result.holds if hold.route_hold_id)
    if args.route_context:
        print(f"已映射路线点: {matched_count}/{len(result.holds)}")
    print("建议:")
    for item in result.feedback:
        print(f"- {item.title}: {item.detail}")


if __name__ == "__main__":
    main()
