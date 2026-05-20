from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FeedbackItem:
    code: str
    title: str
    detail: str


def evaluate_climbing_form(summary: dict[str, float]) -> list[FeedbackItem]:
    feedback: list[FeedbackItem] = []

    elbow_angle = summary.get("avg_elbow_angle", 0.0)
    knee_angle = summary.get("avg_knee_angle", 0.0)
    hip_distance = summary.get("avg_hip_to_ankle_dx", 0.0)
    hand_height_gap = summary.get("avg_hand_height_gap", 0.0)

    if elbow_angle < 105:
        feedback.append(
            FeedbackItem(
                code="overpulling",
                title="上肢发力偏多",
                detail="手臂平均弯曲较明显，建议先尝试用脚推和转髋，再用手完成最后的稳定。",
            )
        )

    if knee_angle > 145:
        feedback.append(
            FeedbackItem(
                code="low_leg_drive",
                title="下肢参与度偏低",
                detail="膝关节整体较伸直，说明蹬脚和踩点利用不足，可以尝试更主动地下压脚点。",
            )
        )

    if hip_distance > 0.12:
        feedback.append(
            FeedbackItem(
                code="hips_away",
                title="髋部离支撑区域偏远",
                detail="髋部与双脚中点的水平偏移较大，建议在触点前先把重心送到支撑脚上。",
            )
        )

    if hand_height_gap > 0.18:
        feedback.append(
            FeedbackItem(
                code="asymmetric_reach",
                title="上肢高度差较大",
                detail="双手高度长期不对称，可能处于单侧硬拉状态，建议结合转髋减少身体被动悬挂。",
            )
        )

    if not feedback:
        feedback.append(
            FeedbackItem(
                code="balanced",
                title="基础动作较稳定",
                detail="当前视频里姿态整体较平衡，可以进一步加入路线阶段分析和单步动作诊断。",
            )
        )

    return feedback
