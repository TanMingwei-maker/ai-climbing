import json

from ai_climbing.move_sequence import ContactSegment, Hold, MoveEvent
from ai_climbing.route_context import apply_route_mapping, load_route_context, match_holds_to_route


def test_load_route_context(tmp_path) -> None:
    route_file = tmp_path / "route.json"
    route_file.write_text(
        json.dumps(
            {
                "wall": {"name": "Training Wall", "angle_deg": 15},
                "route": {"name": "Blue V2"},
                "holds": [
                    {"id": "A1", "x": 0.25, "y": 0.80, "role": "start"},
                    {"id": "A2", "x": 0.45, "y": 0.60},
                ],
            }
        ),
        encoding="utf-8",
    )

    route_context = load_route_context(route_file)

    assert route_context.wall_name == "Training Wall"
    assert route_context.wall_angle_deg == 15.0
    assert route_context.route_name == "Blue V2"
    assert [hold.hold_id for hold in route_context.holds] == ["A1", "A2"]


def test_match_holds_to_route_assigns_unique_nearest_route_hold() -> None:
    holds = [
        Hold(hold_id="hold_1", x=0.26, y=0.79, source="clustered", usage_count=2),
        Hold(hold_id="hold_2", x=0.44, y=0.61, source="clustered", usage_count=3),
        Hold(hold_id="hold_3", x=0.27, y=0.78, source="clustered", usage_count=1),
    ]

    route_context = load_route_context_from_dict(
        {
            "wall": {"name": "Training Wall"},
            "route": {"name": "Blue V2"},
            "holds": [
                {"id": "A1", "x": 0.25, "y": 0.80, "role": "start"},
                {"id": "A2", "x": 0.45, "y": 0.60, "role": "finish"},
            ],
        }
    )

    mapped = match_holds_to_route(holds, route_context, max_distance=0.05)

    assert mapped[0].route_hold_id == "A1"
    assert mapped[0].route_role == "start"
    assert mapped[1].route_hold_id == "A2"
    assert mapped[1].route_role == "finish"
    assert mapped[2].route_hold_id is None


def test_apply_route_mapping_annotates_contacts_and_sequence_ids() -> None:
    holds = [
        Hold(hold_id="hold_1", x=0.26, y=0.79, source="clustered", usage_count=2, route_hold_id="A1", route_role="start"),
        Hold(hold_id="hold_2", x=0.44, y=0.61, source="clustered", usage_count=3),
    ]
    contacts = [
        ContactSegment(
            limb="left_hand",
            hold_id="hold_1",
            start_frame=10,
            end_frame=15,
            center_x=0.26,
            center_y=0.79,
        ),
        ContactSegment(
            limb="right_hand",
            hold_id="hold_2",
            start_frame=20,
            end_frame=24,
            center_x=0.44,
            center_y=0.61,
        ),
    ]
    move_sequence = [
        MoveEvent(frame_index=10, limb="left_hand", hold_id="hold_1", event_type="attach"),
        MoveEvent(frame_index=20, limb="right_hand", hold_id="hold_2", event_type="attach"),
    ]

    mapped_contacts, route_move_sequence = apply_route_mapping(holds, contacts, move_sequence)

    assert mapped_contacts[0].route_hold_id == "A1"
    assert mapped_contacts[0].sequence_hold_id == "A1"
    assert mapped_contacts[1].route_hold_id is None
    assert mapped_contacts[1].sequence_hold_id == "hold_2"
    assert route_move_sequence[0].route_hold_id == "A1"
    assert route_move_sequence[0].sequence_hold_id == "A1"
    assert route_move_sequence[1].sequence_hold_id == "hold_2"


def load_route_context_from_dict(payload: dict) -> object:
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp_dir:
        route_file = Path(tmp_dir) / "route.json"
        route_file.write_text(json.dumps(payload), encoding="utf-8")
        return load_route_context(route_file)
