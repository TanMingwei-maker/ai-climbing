from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from ai_climbing.move_sequence import ContactSegment, Hold, MoveEvent


@dataclass(slots=True)
class RouteHold:
    hold_id: str
    x: float
    y: float
    role: str | None = None


@dataclass(slots=True)
class RouteContext:
    wall_name: str | None = None
    wall_angle_deg: float | None = None
    route_name: str | None = None
    holds: list[RouteHold] = field(default_factory=list)


def load_route_context(path: Path) -> RouteContext:
    payload = json.loads(path.read_text(encoding="utf-8"))
    wall = payload.get("wall", {})
    route = payload.get("route", {})
    angle_deg = wall.get("angle_deg")
    holds = [
        RouteHold(
            hold_id=str(item["id"]),
            x=float(item["x"]),
            y=float(item["y"]),
            role=item.get("role"),
        )
        for item in payload.get("holds", [])
    ]
    return RouteContext(
        wall_name=wall.get("name"),
        wall_angle_deg=float(angle_deg) if angle_deg is not None else None,
        route_name=route.get("name"),
        holds=holds,
    )


def match_holds_to_route(
    holds: list[Hold],
    route_context: RouteContext,
    max_distance: float = 0.08,
) -> list[Hold]:
    if not holds or not route_context.holds:
        return holds

    candidates: list[tuple[float, int, int]] = []
    for hold_index, hold in enumerate(holds):
        for route_index, route_hold in enumerate(route_context.holds):
            distance = math.hypot(hold.x - route_hold.x, hold.y - route_hold.y)
            if distance <= max_distance:
                candidates.append((distance, hold_index, route_index))

    candidates.sort(key=lambda item: item[0])
    assigned_holds: set[int] = set()
    assigned_route_holds: set[int] = set()
    matched_pairs: dict[int, int] = {}
    matched_distances: dict[int, float] = {}

    for _, hold_index, route_index in candidates:
        if hold_index in assigned_holds or route_index in assigned_route_holds:
            continue
        assigned_holds.add(hold_index)
        assigned_route_holds.add(route_index)
        matched_pairs[hold_index] = route_index
        matched_distances[hold_index] = _

    mapped_holds: list[Hold] = []
    for hold_index, hold in enumerate(holds):
        route_index = matched_pairs.get(hold_index)
        if route_index is None:
            mapped_holds.append(hold)
            continue

        route_hold = route_context.holds[route_index]
        mapped_holds.append(
            Hold(
                hold_id=hold.hold_id,
                x=hold.x,
                y=hold.y,
                source=hold.source,
                usage_count=hold.usage_count,
                limbs=hold.limbs,
                route_hold_id=route_hold.hold_id,
                route_role=route_hold.role,
                route_x=route_hold.x,
                route_y=route_hold.y,
                match_distance=matched_distances.get(hold_index),
            )
        )

    return mapped_holds


def apply_route_mapping(
    holds: list[Hold],
    contacts: list[ContactSegment],
    move_sequence: list[MoveEvent],
) -> tuple[list[ContactSegment], list[MoveEvent]]:
    hold_lookup = {hold.hold_id: hold for hold in holds}

    mapped_contacts = [
        ContactSegment(
            limb=contact.limb,
            hold_id=contact.hold_id,
            start_frame=contact.start_frame,
            end_frame=contact.end_frame,
            center_x=contact.center_x,
            center_y=contact.center_y,
            route_hold_id=_route_hold_id(hold_lookup, contact.hold_id),
            route_role=_route_role(hold_lookup, contact.hold_id),
            sequence_hold_id=_sequence_hold_id(hold_lookup, contact.hold_id),
        )
        for contact in contacts
    ]

    mapped_events = [
        MoveEvent(
            frame_index=event.frame_index,
            limb=event.limb,
            hold_id=event.hold_id,
            event_type=event.event_type,
            route_hold_id=_route_hold_id(hold_lookup, event.hold_id),
            route_role=_route_role(hold_lookup, event.hold_id),
            sequence_hold_id=_sequence_hold_id(hold_lookup, event.hold_id),
        )
        for event in move_sequence
    ]
    return mapped_contacts, mapped_events


def _route_hold_id(hold_lookup: dict[str, Hold], hold_id: str) -> str | None:
    hold = hold_lookup.get(hold_id)
    return hold.route_hold_id if hold else None


def _route_role(hold_lookup: dict[str, Hold], hold_id: str) -> str | None:
    hold = hold_lookup.get(hold_id)
    return hold.route_role if hold else None


def _sequence_hold_id(hold_lookup: dict[str, Hold], hold_id: str) -> str:
    hold = hold_lookup.get(hold_id)
    if hold and hold.route_hold_id:
        return hold.route_hold_id
    return hold_id
