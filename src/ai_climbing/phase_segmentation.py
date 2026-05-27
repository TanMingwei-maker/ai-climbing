from __future__ import annotations

from dataclasses import dataclass, field

from ai_climbing.move_sequence import ContactSegment, MoveEvent


FINISH_ROLES = {"top", "finish"}


@dataclass(slots=True)
class PhaseSegment:
    phase_id: str
    phase_type: str
    start_frame: int
    end_frame: int
    start_event_index: int
    end_event_index: int
    event_count: int
    holds: list[str] = field(default_factory=list)
    reason: str = ""


def segment_climb_phases(
    route_move_sequence: list[MoveEvent],
    contacts: list[ContactSegment],
    total_frames: int,
) -> list[PhaseSegment]:
    if not route_move_sequence:
        return []

    last_frame = max([total_frames - 1, *(contact.end_frame for contact in contacts)], default=max(total_frames - 1, 0))
    start_indices = [index for index, event in enumerate(route_move_sequence) if event.route_role == "start"]
    finish_indices = [index for index, event in enumerate(route_move_sequence) if event.route_role in FINISH_ROLES]

    start_end_index, start_reason = _resolve_start_boundary(route_move_sequence, start_indices)
    finish_start_index, finish_reason = _resolve_finish_boundary(route_move_sequence, finish_indices, start_end_index)

    phases: list[PhaseSegment] = []
    first_frame = route_move_sequence[0].frame_index

    start_end_frame = _phase_end_frame(route_move_sequence, contacts, 0, start_end_index)
    phases.append(
        _build_phase(
            phase_id="phase_start",
            phase_type="start",
            events=route_move_sequence,
            start_index=0,
            end_index=start_end_index,
            start_frame=first_frame,
            end_frame=start_end_frame,
            reason=start_reason,
        )
    )

    if finish_start_index > start_end_index + 1:
        transition_start_index = start_end_index + 1
        transition_end_index = finish_start_index - 1
        phases.append(
            _build_phase(
                phase_id="phase_transition",
                phase_type="transition",
                events=route_move_sequence,
                start_index=transition_start_index,
                end_index=transition_end_index,
                start_frame=route_move_sequence[transition_start_index].frame_index,
                end_frame=_phase_end_frame(route_move_sequence, contacts, transition_start_index, transition_end_index),
                reason="基于起步段与结束段之间的剩余动作事件。",
            )
        )

    phases.append(
        _build_phase(
            phase_id="phase_finish",
            phase_type="finish",
            events=route_move_sequence,
            start_index=finish_start_index,
            end_index=len(route_move_sequence) - 1,
            start_frame=route_move_sequence[finish_start_index].frame_index,
            end_frame=last_frame,
            reason=finish_reason,
        )
    )

    return _merge_adjacent_same_type(phases)


def _resolve_start_boundary(events: list[MoveEvent], start_indices: list[int]) -> tuple[int, str]:
    if start_indices:
        return max(start_indices), "根据标注为 start 的路线点确定起步阶段。"

    heuristic_index = min(len(events) - 1, max(0, len(events) // 4 - 1))
    return heuristic_index, "未提供 start 标注，使用前 25% 动作事件估计起步阶段。"


def _resolve_finish_boundary(
    events: list[MoveEvent],
    finish_indices: list[int],
    start_end_index: int,
) -> tuple[int, str]:
    if finish_indices:
        finish_start_index = min(finish_indices)
        finish_start_index = max(finish_start_index, min(start_end_index + 1, len(events) - 1))
        return finish_start_index, "根据标注为 top/finish 的路线点确定结束阶段。"

    heuristic_index = max(start_end_index + 1, len(events) - max(1, len(events) // 4))
    heuristic_index = min(heuristic_index, len(events) - 1)
    return heuristic_index, "未提供 top/finish 标注，使用后 25% 动作事件估计结束阶段。"


def _build_phase(
    phase_id: str,
    phase_type: str,
    events: list[MoveEvent],
    start_index: int,
    end_index: int,
    start_frame: int,
    end_frame: int,
    reason: str,
) -> PhaseSegment:
    phase_events = events[start_index : end_index + 1]
    holds = list(dict.fromkeys(event.sequence_hold_id or event.hold_id for event in phase_events))
    return PhaseSegment(
        phase_id=phase_id,
        phase_type=phase_type,
        start_frame=start_frame,
        end_frame=end_frame,
        start_event_index=start_index,
        end_event_index=end_index,
        event_count=len(phase_events),
        holds=holds,
        reason=reason,
    )


def _phase_end_frame(
    events: list[MoveEvent],
    contacts: list[ContactSegment],
    start_index: int,
    end_index: int,
) -> int:
    sequence_hold_ids = {
        events[index].sequence_hold_id or events[index].hold_id
        for index in range(start_index, end_index + 1)
    }
    matching_contacts = [
        contact.end_frame
        for contact in contacts
        if (contact.sequence_hold_id or contact.hold_id) in sequence_hold_ids
    ]
    if matching_contacts:
        return max(matching_contacts)
    return events[end_index].frame_index


def _merge_adjacent_same_type(phases: list[PhaseSegment]) -> list[PhaseSegment]:
    if not phases:
        return []

    merged: list[PhaseSegment] = [phases[0]]
    for phase in phases[1:]:
        previous = merged[-1]
        if previous.phase_type != phase.phase_type:
            merged.append(phase)
            continue

        merged[-1] = PhaseSegment(
            phase_id=previous.phase_id,
            phase_type=previous.phase_type,
            start_frame=previous.start_frame,
            end_frame=max(previous.end_frame, phase.end_frame),
            start_event_index=previous.start_event_index,
            end_event_index=phase.end_event_index,
            event_count=previous.event_count + phase.event_count,
            holds=list(dict.fromkeys(previous.holds + phase.holds)),
            reason=previous.reason,
        )

    return merged
