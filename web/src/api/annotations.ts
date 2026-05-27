import type { HoldDraft } from '../stores/annotationStore';
import { apiFetch } from './client';

export type RouteContextDto = {
  wall: {
    name?: string | null;
    angle_deg?: number | null;
  };
  route: {
    name?: string | null;
  };
  holds: HoldDraft[];
};

export function getRouteContext(videoId: string) {
  return apiFetch<RouteContextDto>(`/videos/${videoId}/route-context`);
}

export function saveRouteContext(videoId: string, payload: RouteContextDto) {
  return apiFetch<RouteContextDto>(`/videos/${videoId}/route-context`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}
