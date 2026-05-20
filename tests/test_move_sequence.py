from ai_climbing.move_sequence import LimbSample, build_limb_states, detect_move_sequence


def test_build_limb_states_marks_static_samples() -> None:
    samples = [
        LimbSample(frame_index=0, limb="left_hand", x=0.10, y=0.20, visibility=1.0),
        LimbSample(frame_index=1, limb="left_hand", x=0.101, y=0.201, visibility=1.0),
        LimbSample(frame_index=2, limb="left_hand", x=0.102, y=0.202, visibility=1.0),
        LimbSample(frame_index=3, limb="left_hand", x=0.20, y=0.30, visibility=1.0),
    ]

    states = [state for state in build_limb_states(samples, movement_threshold=0.01) if state.limb == "left_hand"]

    assert states[0].state == "moving"
    assert states[1].state == "static"
    assert states[2].state == "static"
    assert states[3].state == "moving"


def test_detect_move_sequence_clusters_contacts_and_events() -> None:
    samples = []
    for frame_index in range(8):
        x = 0.10 if frame_index < 4 else 0.40
        samples.append(LimbSample(frame_index=frame_index, limb="left_hand", x=x, y=0.20, visibility=1.0))

    states = build_limb_states(samples, movement_threshold=0.01)
    holds, contacts, move_sequence = detect_move_sequence(states, hold_radius=0.05, min_static_frames=2)

    assert [hold.hold_id for hold in holds] == ["hold_1", "hold_2"]
    assert [(contact.hold_id, contact.start_frame, contact.end_frame) for contact in contacts] == [
        ("hold_1", 1, 3),
        ("hold_2", 5, 7),
    ]
    assert [(event.hold_id, event.frame_index) for event in move_sequence] == [
        ("hold_1", 1),
        ("hold_2", 5),
    ]


def test_detect_move_sequence_merges_close_holds_and_reconnects_contacts() -> None:
    samples = [
        LimbSample(frame_index=0, limb="left_hand", x=0.100, y=0.200, visibility=1.0),
        LimbSample(frame_index=1, limb="left_hand", x=0.101, y=0.201, visibility=1.0),
        LimbSample(frame_index=2, limb="left_hand", x=0.102, y=0.202, visibility=1.0),
        LimbSample(frame_index=3, limb="left_hand", x=0.180, y=0.260, visibility=1.0),
        LimbSample(frame_index=4, limb="left_hand", x=0.104, y=0.204, visibility=1.0),
        LimbSample(frame_index=5, limb="left_hand", x=0.105, y=0.205, visibility=1.0),
        LimbSample(frame_index=6, limb="left_hand", x=0.106, y=0.206, visibility=1.0),
        LimbSample(frame_index=7, limb="left_hand", x=0.112, y=0.208, visibility=1.0),
        LimbSample(frame_index=8, limb="left_hand", x=0.113, y=0.209, visibility=1.0),
    ]

    states = build_limb_states(samples, movement_threshold=0.01)
    holds, contacts, move_sequence = detect_move_sequence(
        states,
        hold_radius=0.02,
        merge_radius=0.03,
        min_static_frames=2,
        reconnect_gap=2,
    )

    assert len(holds) == 1
    assert holds[0].hold_id == "hold_1"
    assert len(contacts) == 1
    assert contacts[0].start_frame == 1
    assert contacts[0].end_frame == 8
    assert len(move_sequence) == 1
    assert move_sequence[0].hold_id == "hold_1"
