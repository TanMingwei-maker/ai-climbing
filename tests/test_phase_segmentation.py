from ai_climbing.move_sequence import ContactSegment, MoveEvent
from ai_climbing.phase_segmentation import segment_climb_phases


def test_segment_climb_phases_with_route_roles() -> None:
    route_move_sequence = [
        MoveEvent(frame_index=10, limb="left_foot", hold_id="hold_1", event_type="attach", route_hold_id="S1", route_role="start", sequence_hold_id="S1"),
        MoveEvent(frame_index=20, limb="right_foot", hold_id="hold_2", event_type="attach", route_hold_id="S2", route_role="start", sequence_hold_id="S2"),
        MoveEvent(frame_index=40, limb="left_hand", hold_id="hold_3", event_type="attach", route_hold_id="H1", route_role=None, sequence_hold_id="H1"),
        MoveEvent(frame_index=60, limb="right_hand", hold_id="hold_4", event_type="attach", route_hold_id="H2", route_role=None, sequence_hold_id="H2"),
        MoveEvent(frame_index=80, limb="left_hand", hold_id="hold_5", event_type="attach", route_hold_id="T1", route_role="top", sequence_hold_id="T1"),
    ]
    contacts = [
        ContactSegment(limb="left_foot", hold_id="hold_1", start_frame=10, end_frame=30, center_x=0.4, center_y=0.8, sequence_hold_id="S1"),
        ContactSegment(limb="right_foot", hold_id="hold_2", start_frame=20, end_frame=36, center_x=0.5, center_y=0.8, sequence_hold_id="S2"),
        ContactSegment(limb="left_hand", hold_id="hold_3", start_frame=40, end_frame=52, center_x=0.45, center_y=0.6, sequence_hold_id="H1"),
        ContactSegment(limb="right_hand", hold_id="hold_4", start_frame=60, end_frame=74, center_x=0.55, center_y=0.58, sequence_hold_id="H2"),
        ContactSegment(limb="left_hand", hold_id="hold_5", start_frame=80, end_frame=98, center_x=0.48, center_y=0.1, sequence_hold_id="T1"),
    ]

    phases = segment_climb_phases(route_move_sequence, contacts, total_frames=100)

    assert [phase.phase_type for phase in phases] == ["start", "transition", "finish"]
    assert phases[0].end_event_index == 1
    assert phases[1].start_event_index == 2
    assert phases[2].start_event_index == 4
    assert phases[2].holds == ["T1"]


def test_segment_climb_phases_without_route_roles_uses_heuristic() -> None:
    route_move_sequence = [
        MoveEvent(frame_index=10, limb="left_foot", hold_id="hold_1", event_type="attach", sequence_hold_id="hold_1"),
        MoveEvent(frame_index=20, limb="right_foot", hold_id="hold_2", event_type="attach", sequence_hold_id="hold_2"),
        MoveEvent(frame_index=30, limb="left_hand", hold_id="hold_3", event_type="attach", sequence_hold_id="hold_3"),
        MoveEvent(frame_index=40, limb="right_hand", hold_id="hold_4", event_type="attach", sequence_hold_id="hold_4"),
    ]

    phases = segment_climb_phases(route_move_sequence, contacts=[], total_frames=50)

    assert [phase.phase_type for phase in phases] == ["start", "transition", "finish"]
    assert phases[0].reason.startswith("未提供 start 标注")
    assert phases[2].reason.startswith("未提供 top/finish 标注")
