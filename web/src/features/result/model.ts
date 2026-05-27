import { getApiErrorMessage, isApiError, toApiUrl } from '../../api/client';
import { getAnalysisResult } from '../../api/results';

export type SummaryPayload = {
  avg_elbow_angle?: number;
  avg_knee_angle?: number;
  avg_hip_to_ankle_dx?: number;
  avg_hand_height_gap?: number;
};

export type RouteContextHold = {
  hold_id: string;
  x: number;
  y: number;
  role?: string | null;
};

export type RouteContextPayload = {
  wall_name?: string | null;
  wall_angle_deg?: number | null;
  route_name?: string | null;
  holds?: RouteContextHold[];
};

export type HoldPayload = {
  hold_id: string;
  x: number;
  y: number;
  source: string;
  usage_count: number;
  limbs: string[];
  route_hold_id?: string | null;
  route_role?: string | null;
  route_x?: number | null;
  route_y?: number | null;
  match_distance?: number | null;
};

export type MoveEventPayload = {
  frame_index: number;
  limb: string;
  hold_id: string;
  event_type: string;
  route_hold_id?: string | null;
  route_role?: string | null;
  sequence_hold_id?: string | null;
};

export type JsonPayload = {
  summary?: SummaryPayload;
  feedback?: Array<{ title: string; detail?: string }>;
  route_context?: RouteContextPayload | null;
  holds?: HoldPayload[];
  route_move_sequence?: MoveEventPayload[];
} & Record<string, unknown>;

export type FusionRow = {
  detectedHoldId: string;
  routeHoldId: string;
  detectedPoint: string;
  routePoint: string;
  limbs: string;
  distance: string;
  distanceValue: number | null;
  riskLabel: string;
  riskClassName: string;
};

export type FocusTarget = {
  detectedHoldId?: string | null;
  routeHoldId?: string | null;
};

export type UnmatchedRow = {
  detectedHoldId: string;
  detectedPoint: string;
  limbs: string;
  usageCount: number;
};

export type ScatterDetectedPoint = {
  holdId: string;
  x: number;
  y: number;
  routeHoldId?: string | null;
  routeX?: number | null;
  routeY?: number | null;
  matchDistance?: number | null;
};

export const DISTANCE_ALERT_THRESHOLD = 0.05;
export const DISTANCE_WARN_THRESHOLD = 0.03;
export const WALL_MAP_WIDTH = 320;
export const WALL_MAP_HEIGHT = 520;
export const WALL_MAP_PADDING = 26;

export function formatPoint(x?: number | null, y?: number | null) {
  if (x == null || y == null) {
    return '-';
  }
  return `${x.toFixed(3)}, ${y.toFixed(3)}`;
}

export function formatDistance(value?: number | null) {
  if (value == null) {
    return '-';
  }
  return value.toFixed(3);
}

export function formatMetric(value?: number) {
  if (value == null || Number.isNaN(value)) {
    return '-';
  }
  return value.toFixed(3);
}

export function limbLabel(limb: string) {
  const labels: Record<string, string> = {
    left_hand: '左手',
    right_hand: '右手',
    left_foot: '左脚',
    right_foot: '右脚',
  };
  return labels[limb] ?? limb;
}

export function classifyRisk(distance: number | null) {
  if (distance == null) {
    return { label: '未知', className: 'risk-unknown' };
  }
  if (distance > DISTANCE_ALERT_THRESHOLD) {
    return { label: '高风险', className: 'risk-high' };
  }
  if (distance > DISTANCE_WARN_THRESHOLD) {
    return { label: '偏大', className: 'risk-warn' };
  }
  return { label: '正常', className: 'risk-ok' };
}

export function buildFusionRows(holds: HoldPayload[] = []): FusionRow[] {
  return holds
    .filter((hold) => hold.route_hold_id)
    .map((hold) => {
      const risk = classifyRisk(hold.match_distance ?? null);
      return {
        detectedHoldId: hold.hold_id,
        routeHoldId: hold.route_hold_id ?? '-',
        detectedPoint: formatPoint(hold.x, hold.y),
        routePoint: formatPoint(hold.route_x, hold.route_y),
        limbs: hold.limbs.map(limbLabel).join(' / ') || '-',
        distance: formatDistance(hold.match_distance),
        distanceValue: hold.match_distance ?? null,
        riskLabel: risk.label,
        riskClassName: risk.className,
      };
    })
    .sort((left, right) => left.routeHoldId.localeCompare(right.routeHoldId));
}

export function buildUnmatchedRows(holds: HoldPayload[] = []): UnmatchedRow[] {
  return holds
    .filter((hold) => !hold.route_hold_id)
    .map((hold) => ({
      detectedHoldId: hold.hold_id,
      detectedPoint: formatPoint(hold.x, hold.y),
      limbs: hold.limbs.map(limbLabel).join(' / ') || '-',
      usageCount: hold.usage_count,
    }))
    .sort((left, right) => right.usageCount - left.usageCount);
}

export function buildFusionStats(rows: FusionRow[]) {
  const distances = rows
    .map((row) => row.distanceValue)
    .filter((value): value is number => value != null);
  const avgDistance = distances.length
    ? distances.reduce((sum, value) => sum + value, 0) / distances.length
    : null;
  const maxDistance = distances.length ? Math.max(...distances) : null;
  const warnCount = rows.filter((row) => row.distanceValue != null && row.distanceValue > DISTANCE_WARN_THRESHOLD).length;
  const highRiskCount = rows.filter((row) => row.distanceValue != null && row.distanceValue > DISTANCE_ALERT_THRESHOLD).length;
  return {
    avgDistance,
    maxDistance,
    warnCount,
    highRiskCount,
  };
}

export function toWallMapPoint(x: number, y: number) {
  const innerWidth = WALL_MAP_WIDTH - WALL_MAP_PADDING * 2;
  const innerHeight = WALL_MAP_HEIGHT - WALL_MAP_PADDING * 2;
  return {
    x: WALL_MAP_PADDING + x * innerWidth,
    y: WALL_MAP_PADDING + y * innerHeight,
  };
}

export function scatterLineColor(distance: number | null) {
  if (distance == null) {
    return '#94a3b8';
  }
  if (distance > DISTANCE_ALERT_THRESHOLD) {
    return '#0ea5e9';
  }
  if (distance > DISTANCE_WARN_THRESHOLD) {
    return '#facc15';
  }
  return '#4ade80';
}

export function scatterDetectedColor(distance: number | null, matched: boolean) {
  if (!matched) {
    return '#fb7185';
  }
  if (distance == null) {
    return '#82d2ff';
  }
  if (distance > DISTANCE_ALERT_THRESHOLD) {
    return '#38bdf8';
  }
  if (distance > DISTANCE_WARN_THRESHOLD) {
    return '#fde68a';
  }
  return '#82d2ff';
}

export function buildRecentEvents(events: MoveEventPayload[] = []) {
  return events.slice(-5).reverse().map((event) => ({
    frame: event.frame_index,
    limb: limbLabel(event.limb),
    hold: event.sequence_hold_id ?? event.route_hold_id ?? event.hold_id,
    eventType: event.event_type,
  }));
}

export function isFocusActive(target: FocusTarget | null) {
  return Boolean(target?.detectedHoldId || target?.routeHoldId);
}

export function isFusionRowFocused(row: FusionRow, target: FocusTarget | null) {
  if (!target) {
    return false;
  }
  return row.detectedHoldId === target.detectedHoldId || row.routeHoldId === target.routeHoldId;
}

export function isDetectedPointFocused(point: ScatterDetectedPoint, target: FocusTarget | null) {
  if (!target) {
    return false;
  }
  return point.holdId === target.detectedHoldId || point.routeHoldId === target.routeHoldId;
}

export function isManualPointFocused(hold: RouteContextHold, target: FocusTarget | null) {
  if (!target) {
    return false;
  }
  return hold.hold_id === target.routeHoldId;
}

export function focusLabel(target: FocusTarget | null) {
  if (!target) {
    return '点击点位或表格行，查看人工点与识别点的对应关系。';
  }
  if (target.routeHoldId && target.detectedHoldId) {
    return `当前高亮: ${target.routeHoldId} <-> ${target.detectedHoldId}`;
  }
  if (target.routeHoldId) {
    return `当前高亮人工点: ${target.routeHoldId}`;
  }
  if (target.detectedHoldId) {
    return `当前高亮识别点: ${target.detectedHoldId}`;
  }
  return '点击点位或表格行，查看人工点与识别点的对应关系。';
}

export async function getOptionalResult(videoId: string) {
  try {
    return await getAnalysisResult(videoId);
  } catch (error) {
    if (isApiError(error) && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function fetchResultJson(resultJsonUrl: string) {
  const response = await fetch(toApiUrl(resultJsonUrl));
  if (!response.ok) {
    throw new Error(`结果 JSON 读取失败: ${response.status}`);
  }
  return response.json() as Promise<JsonPayload>;
}

export function getResultStatusMessage(args: {
  isPending: boolean;
  videoError: unknown;
  resultError: unknown;
  jsonError: unknown;
  hasResult: boolean;
}) {
  if (args.isPending) {
    return '正在加载分析结果...';
  }
  if (args.videoError) {
    return getApiErrorMessage(args.videoError, '视频信息加载失败');
  }
  if (args.resultError) {
    return getApiErrorMessage(args.resultError, '结果加载失败');
  }
  if (args.jsonError) {
    return getApiErrorMessage(args.jsonError, '结果 JSON 读取失败');
  }
  return args.hasResult ? '分析完成' : '当前还没有分析结果，请先完成标注并启动分析。';
}
