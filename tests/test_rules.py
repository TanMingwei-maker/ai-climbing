from ai_climbing.rules import evaluate_climbing_form


def test_rules_detect_overpulling() -> None:
    summary = {
        "avg_elbow_angle": 90.0,
        "avg_knee_angle": 150.0,
        "avg_hip_to_ankle_dx": 0.15,
        "avg_hand_height_gap": 0.2,
    }

    feedback = evaluate_climbing_form(summary)
    codes = {item.code for item in feedback}

    assert "overpulling" in codes
    assert "low_leg_drive" in codes
    assert "hips_away" in codes
    assert "asymmetric_reach" in codes


def test_rules_detect_balanced_form() -> None:
    summary = {
        "avg_elbow_angle": 125.0,
        "avg_knee_angle": 130.0,
        "avg_hip_to_ankle_dx": 0.05,
        "avg_hand_height_gap": 0.08,
    }

    feedback = evaluate_climbing_form(summary)

    assert len(feedback) == 1
    assert feedback[0].code == "balanced"
