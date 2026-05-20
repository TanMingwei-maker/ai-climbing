from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable


LIMBS = ("left_hand", "right_hand", "left_foot", "right_foot")


@dataclass(slots=True)
class LimbSample:
    frame_index: int
    limb: str
    x: float
    y: float
    visibility: float


@dataclass(slots=True)
class LimbState:
    frame_index: int
    limb: str
    x: float
    y: float
    visibility: float
    speed: float
    state: str


@dataclass(slots=True)
class Hold:
    hold_id: str
    x: float
    y: float
    source: str
    usage_count: int
    limbs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ContactSegment:
    limb: str
    hold_id: str
    start_frame: int
    end_frame: int
    center_x: float
    center_y: float


@dataclass(slots=True)
class MoveEvent:
    frame_index: int
    limb: str
    hold_id: str
    event_type: str


@dataclass(slots=True)
class _StaticRun:
    limb: str
    start_frame: int
    end_frame: int
    center_x: float
    center_y: float


def build_limb_states(
    samples: Iterable[LimbSample],
    movement_threshold: float = 0.015,
    visibility_threshold: float = 0.5,
) -> list[LimbState]:
    grouped_samples: dict[str, list[LimbSample]] = {limb: [] for limb in LIMBS}
    for sample in samples:
        grouped_samples.setdefault(sample.limb, []).append(sample)

    states: list[LimbState] = []
    for limb in LIMBS:
        previous_visible: LimbSample | None = None
        for sample in grouped_samples.get(limb, []):
            speed = 0.0
            state = "moving"
            if sample.visibility >= visibility_threshold and previous_visible is not None:
                speed = math.hypot(sample.x - previous_visible.x, sample.y - previous_visible.y)
                state = "static" if speed <= movement_threshold else "moving"
            if sample.visibility >= visibility_threshold:
                previous_visible = sample

            states.append(
                LimbState(
                    frame_index=sample.frame_index,
                    limb=sample.limb,
                    x=sample.x,
                    y=sample.y,
                    visibility=sample.visibility,
                    speed=speed,
                    state=state,
                )
            )

    states.sort(key=lambda item: (item.frame_index, item.limb))
    return states


def detect_move_sequence(
    limb_states: Iterable[LimbState],
    hold_radius: float = 0.04,
    min_static_frames: int = 4,
    merge_radius: float = 0.06,
    reconnect_gap: int = 3,
) -> tuple[list[Hold], list[ContactSegment], list[MoveEvent]]:
    grouped_states: dict[str, list[LimbState]] = {limb: [] for limb in LIMBS}
    for state in limb_states:
        grouped_states.setdefault(state.limb, []).append(state)

    runs: list[_StaticRun] = []
    for limb in LIMBS:
        runs.extend(_collect_static_runs(grouped_states.get(limb, []), min_static_frames=min_static_frames))

    holds, assignments = _cluster_runs(runs, hold_radius=hold_radius)
    contacts = [
        ContactSegment(
            limb=run.limb,
            hold_id=hold_id,
            start_frame=run.start_frame,
            end_frame=run.end_frame,
            center_x=run.center_x,
            center_y=run.center_y,
        )
        for run, hold_id in assignments
    ]
    contacts.sort(key=lambda item: (item.start_frame, item.limb))
    holds, contacts = _merge_holds(holds, contacts, merge_radius=merge_radius)
    contacts = _merge_contact_segments(contacts, reconnect_gap=reconnect_gap)

    move_events: list[MoveEvent] = []
    previous_hold_by_limb: dict[str, str] = {}
    for contact in contacts:
        previous_hold = previous_hold_by_limb.get(contact.limb)
        if previous_hold != contact.hold_id:
            move_events.append(
                MoveEvent(
                    frame_index=contact.start_frame,
                    limb=contact.limb,
                    hold_id=contact.hold_id,
                    event_type="attach",
                )
            )
            previous_hold_by_limb[contact.limb] = contact.hold_id

    return holds, contacts, move_events


def _collect_static_runs(states: list[LimbState], min_static_frames: int) -> list[_StaticRun]:
    runs: list[_StaticRun] = []
    current_run: list[LimbState] = []

    for state in states:
        if state.state == "static":
            current_run.append(state)
            continue
        _flush_run(current_run, runs, min_static_frames=min_static_frames)
        current_run = []

    _flush_run(current_run, runs, min_static_frames=min_static_frames)
    return runs


def _flush_run(current_run: list[LimbState], runs: list[_StaticRun], min_static_frames: int) -> None:
    if len(current_run) < min_static_frames:
        return
    runs.append(
        _StaticRun(
            limb=current_run[0].limb,
            start_frame=current_run[0].frame_index,
            end_frame=current_run[-1].frame_index,
            center_x=sum(state.x for state in current_run) / len(current_run),
            center_y=sum(state.y for state in current_run) / len(current_run),
        )
    )


def _cluster_runs(
    runs: list[_StaticRun],
    hold_radius: float,
) -> tuple[list[Hold], list[tuple[_StaticRun, str]]]:
    clusters: list[dict[str, object]] = []
    assignments: list[tuple[_StaticRun, str]] = []

    for run in runs:
        best_cluster: dict[str, object] | None = None
        best_distance = float("inf")
        for cluster in clusters:
            distance = math.hypot(run.center_x - float(cluster["x"]), run.center_y - float(cluster["y"]))
            if distance <= hold_radius and distance < best_distance:
                best_distance = distance
                best_cluster = cluster

        if best_cluster is None:
            best_cluster = {
                "hold_id": f"hold_{len(clusters) + 1}",
                "x": run.center_x,
                "y": run.center_y,
                "count": 0,
                "limbs": set(),
            }
            clusters.append(best_cluster)
        else:
            count = int(best_cluster["count"])
            best_cluster["x"] = (float(best_cluster["x"]) * count + run.center_x) / (count + 1)
            best_cluster["y"] = (float(best_cluster["y"]) * count + run.center_y) / (count + 1)

        best_cluster["count"] = int(best_cluster["count"]) + 1
        limbs = best_cluster["limbs"]
        assert isinstance(limbs, set)
        limbs.add(run.limb)
        assignments.append((run, str(best_cluster["hold_id"])))

    holds = [
        Hold(
            hold_id=str(cluster["hold_id"]),
            x=float(cluster["x"]),
            y=float(cluster["y"]),
            source="clustered",
            usage_count=int(cluster["count"]),
            limbs=sorted(cluster["limbs"]),
        )
        for cluster in clusters
    ]
    return holds, assignments


def _merge_holds(
    holds: list[Hold],
    contacts: list[ContactSegment],
    merge_radius: float,
) -> tuple[list[Hold], list[ContactSegment]]:
    if not holds:
        return [], []

    merged_clusters: list[dict[str, object]] = []
    hold_mapping: dict[str, str] = {}

    for hold in holds:
        best_cluster: dict[str, object] | None = None
        best_distance = float("inf")
        for cluster in merged_clusters:
            distance = math.hypot(hold.x - float(cluster["x"]), hold.y - float(cluster["y"]))
            if distance <= merge_radius and distance < best_distance:
                best_cluster = cluster
                best_distance = distance

        if best_cluster is None:
            best_cluster = {
                "index": len(merged_clusters) + 1,
                "x": hold.x,
                "y": hold.y,
                "weight": hold.usage_count,
                "limbs": set(hold.limbs),
            }
            merged_clusters.append(best_cluster)
        else:
            weight = int(best_cluster["weight"])
            total_weight = weight + hold.usage_count
            best_cluster["x"] = (float(best_cluster["x"]) * weight + hold.x * hold.usage_count) / total_weight
            best_cluster["y"] = (float(best_cluster["y"]) * weight + hold.y * hold.usage_count) / total_weight
            best_cluster["weight"] = total_weight
            limbs = best_cluster["limbs"]
            assert isinstance(limbs, set)
            limbs.update(hold.limbs)

        hold_mapping[hold.hold_id] = f"hold_{int(best_cluster['index'])}"

    rewritten_contacts = [
        ContactSegment(
            limb=contact.limb,
            hold_id=hold_mapping[contact.hold_id],
            start_frame=contact.start_frame,
            end_frame=contact.end_frame,
            center_x=contact.center_x,
            center_y=contact.center_y,
        )
        for contact in contacts
    ]

    usage_count_by_hold: dict[str, int] = {}
    limbs_by_hold: dict[str, set[str]] = {}
    for contact in rewritten_contacts:
        usage_count_by_hold[contact.hold_id] = usage_count_by_hold.get(contact.hold_id, 0) + 1
        limbs_by_hold.setdefault(contact.hold_id, set()).add(contact.limb)

    merged_holds = [
        Hold(
            hold_id=f"hold_{int(cluster['index'])}",
            x=float(cluster["x"]),
            y=float(cluster["y"]),
            source="clustered",
            usage_count=usage_count_by_hold.get(f"hold_{int(cluster['index'])}", 0),
            limbs=sorted(limbs_by_hold.get(f"hold_{int(cluster['index'])}", set())),
        )
        for cluster in merged_clusters
        if usage_count_by_hold.get(f"hold_{int(cluster['index'])}", 0) > 0
    ]
    return merged_holds, rewritten_contacts


def _merge_contact_segments(
    contacts: list[ContactSegment],
    reconnect_gap: int,
) -> list[ContactSegment]:
    if not contacts:
        return []

    contacts = sorted(contacts, key=lambda item: (item.limb, item.start_frame, item.end_frame))
    merged_contacts: list[ContactSegment] = []

    for contact in contacts:
        if not merged_contacts:
            merged_contacts.append(contact)
            continue

        previous = merged_contacts[-1]
        same_target = previous.limb == contact.limb and previous.hold_id == contact.hold_id
        short_gap = contact.start_frame - previous.end_frame <= reconnect_gap + 1
        if same_target and short_gap:
            previous_length = previous.end_frame - previous.start_frame + 1
            current_length = contact.end_frame - contact.start_frame + 1
            total_length = previous_length + current_length
            merged_contacts[-1] = ContactSegment(
                limb=previous.limb,
                hold_id=previous.hold_id,
                start_frame=previous.start_frame,
                end_frame=max(previous.end_frame, contact.end_frame),
                center_x=(previous.center_x * previous_length + contact.center_x * current_length) / total_length,
                center_y=(previous.center_y * previous_length + contact.center_y * current_length) / total_length,
            )
            continue

        merged_contacts.append(contact)

    return sorted(merged_contacts, key=lambda item: (item.start_frame, item.limb))
