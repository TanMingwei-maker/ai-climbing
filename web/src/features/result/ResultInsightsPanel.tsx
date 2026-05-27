import { Link } from 'react-router-dom';
import type {
  FocusTarget,
  FusionRow,
  JsonPayload,
  RouteContextHold,
  RouteContextPayload,
  ScatterDetectedPoint,
  SummaryPayload,
  UnmatchedRow,
} from './model';
import {
  DISTANCE_ALERT_THRESHOLD,
  WALL_MAP_HEIGHT,
  WALL_MAP_WIDTH,
  focusLabel,
  formatDistance,
  formatMetric,
  isDetectedPointFocused,
  isFocusActive,
  isFusionRowFocused,
  isManualPointFocused,
  scatterDetectedColor,
  scatterLineColor,
  toWallMapPoint,
} from './model';

type RecentEvent = {
  frame: number;
  limb: string;
  hold: string;
  eventType: string;
};

type ResultInsightsPanelProps = {
  videoId: string;
  summary?: SummaryPayload;
  routeContext?: RouteContextPayload | null;
  routeHolds: RouteContextHold[];
  fusionRows: FusionRow[];
  fusionStats: {
    avgDistance: number | null;
    maxDistance: number | null;
    warnCount: number;
    highRiskCount: number;
  };
  filteredFusionRows: FusionRow[];
  unmatchedRows: UnmatchedRow[];
  recentEvents: RecentEvent[];
  feedback: Array<{ title: string; detail?: string }>;
  jsonPayload: JsonPayload | null;
  scatterDetectedPoints: ScatterDetectedPoint[];
  showOnlyAlerts: boolean;
  focusedPoint: FocusTarget | null;
  onToggleAlerts: () => void;
  onFocusedPointChange: (target: FocusTarget | null) => void;
};

export function ResultInsightsPanel({
  videoId,
  summary,
  routeContext,
  routeHolds,
  fusionRows,
  fusionStats,
  filteredFusionRows,
  unmatchedRows,
  recentEvents,
  feedback,
  jsonPayload,
  scatterDetectedPoints,
  showOnlyAlerts,
  focusedPoint,
  onToggleAlerts,
  onFocusedPointChange,
}: ResultInsightsPanelProps) {
  const hasFocusedPoint = isFocusActive(focusedPoint);

  return (
    <aside className="panel">
      <p className="eyebrow">融合摘要</p>
      <div className="result-stack">
        <section className="result-card">
          <h2>路线信息</h2>
          <div className="result-grid">
            <div>
              <span className="result-label">路线</span>
              <strong>{routeContext?.route_name ?? '-'}</strong>
            </div>
            <div>
              <span className="result-label">墙面</span>
              <strong>{routeContext?.wall_name ?? '-'}</strong>
            </div>
            <div>
              <span className="result-label">角度</span>
              <strong>{routeContext?.wall_angle_deg == null ? '-' : `${routeContext.wall_angle_deg} 度`}</strong>
            </div>
            <div>
              <span className="result-label">人工点数</span>
              <strong>{routeContext?.holds?.length ?? 0}</strong>
            </div>
            <div>
              <span className="result-label">已融合点数</span>
              <strong>{fusionRows.length}</strong>
            </div>
          </div>
        </section>

        <section className="result-card">
          <h2>点位示意图</h2>
          {routeHolds.length || scatterDetectedPoints.length ? (
            <div className="wall-map-shell">
              <div className="compact-row result-tools">
                <span className="muted">{focusLabel(focusedPoint)}</span>
                <div className="button-row">
                  {focusedPoint?.routeHoldId ? (
                    <Link className="ghost-button" to={`/annotate/${videoId}?focusHoldId=${encodeURIComponent(focusedPoint.routeHoldId)}`}>
                      去标注定位
                    </Link>
                  ) : null}
                <button
                  className="ghost-button"
                  type="button"
                  onClick={() => onFocusedPointChange(null)}
                  disabled={!hasFocusedPoint}
                >
                  清除高亮
                </button>
                </div>
              </div>
              <svg
                className="wall-map"
                viewBox={`0 0 ${WALL_MAP_WIDTH} ${WALL_MAP_HEIGHT}`}
                role="img"
                aria-label="人工点和识别点散点示意图"
              >
                <rect
                  x="8"
                  y="8"
                  width={WALL_MAP_WIDTH - 16}
                  height={WALL_MAP_HEIGHT - 16}
                  rx="18"
                  fill="rgba(2, 6, 23, 0.9)"
                  stroke="rgba(148, 163, 184, 0.25)"
                />

                {scatterDetectedPoints
                  .filter((point) => point.routeX != null && point.routeY != null)
                  .map((point) => {
                    const detected = toWallMapPoint(point.x, point.y);
                    const manual = toWallMapPoint(point.routeX ?? point.x, point.routeY ?? point.y);
                    const isFocused = isDetectedPointFocused(point, focusedPoint);
                    const isDimmed = hasFocusedPoint && !isFocused;
                    return (
                      <line
                        key={`line-${point.holdId}`}
                        className={`wall-map-link${isFocused ? ' is-focused' : ''}${isDimmed ? ' is-dimmed' : ''}`}
                        x1={detected.x}
                        y1={detected.y}
                        x2={manual.x}
                        y2={manual.y}
                        stroke={scatterLineColor(point.matchDistance ?? null)}
                        strokeWidth="2"
                        opacity="0.95"
                      />
                    );
                  })}

                {routeHolds.map((hold) => {
                  const point = toWallMapPoint(hold.x, hold.y);
                  const isFocused = isManualPointFocused(hold, focusedPoint);
                  const isDimmed = hasFocusedPoint && !isFocused;
                  return (
                    <g
                      key={`manual-${hold.hold_id}`}
                      className={`wall-map-node wall-map-node-manual${isFocused ? ' is-focused' : ''}${isDimmed ? ' is-dimmed' : ''}`}
                      onClick={() => onFocusedPointChange({ routeHoldId: hold.hold_id })}
                    >
                      <circle cx={point.x} cy={point.y} r="8" fill="transparent" stroke="#e2e8f0" strokeWidth="2.5" />
                      <text x={point.x + 10} y={point.y - 10} className="wall-map-label">
                        {hold.hold_id}
                      </text>
                    </g>
                  );
                })}

                {scatterDetectedPoints.map((point) => {
                  const detected = toWallMapPoint(point.x, point.y);
                  const matched = point.routeHoldId != null;
                  const isFocused = isDetectedPointFocused(point, focusedPoint);
                  const isDimmed = hasFocusedPoint && !isFocused;
                  return (
                    <g
                      key={`detected-${point.holdId}`}
                      className={`wall-map-node wall-map-node-detected${isFocused ? ' is-focused' : ''}${isDimmed ? ' is-dimmed' : ''}`}
                      onClick={() =>
                        onFocusedPointChange({
                          detectedHoldId: point.holdId,
                          routeHoldId: point.routeHoldId,
                        })
                      }
                    >
                      <circle
                        cx={detected.x}
                        cy={detected.y}
                        r="5"
                        fill={scatterDetectedColor(point.matchDistance ?? null, matched)}
                        stroke="#ffffff"
                        strokeWidth="1.5"
                      />
                    </g>
                  );
                })}
              </svg>
              <div className="wall-map-caption">
                <span className="legend-pill legend-pill-manual">人工点</span>
                <span className="legend-pill legend-pill-detected">识别点</span>
                <span className="legend-pill legend-pill-match">匹配连线</span>
                <span className="legend-pill legend-pill-alert">偏差较大</span>
              </div>
            </div>
          ) : (
            <p className="muted">当前没有足够的数据生成点位示意图。</p>
          )}
        </section>

        <section className="result-card">
          <h2>姿态摘要</h2>
          <div className="result-grid">
            <div>
              <span className="result-label">肘角均值</span>
              <strong>{formatMetric(summary?.avg_elbow_angle)}</strong>
            </div>
            <div>
              <span className="result-label">膝角均值</span>
              <strong>{formatMetric(summary?.avg_knee_angle)}</strong>
            </div>
            <div>
              <span className="result-label">髋部偏移</span>
              <strong>{formatMetric(summary?.avg_hip_to_ankle_dx)}</strong>
            </div>
            <div>
              <span className="result-label">双手高差</span>
              <strong>{formatMetric(summary?.avg_hand_height_gap)}</strong>
            </div>
          </div>
        </section>

        <section className="result-card">
          <h2>融合点位</h2>
          <div className="legend-row">
            <span className="legend-pill legend-pill-manual">人工点</span>
            <span className="legend-pill legend-pill-detected">识别点</span>
            <span className="legend-pill legend-pill-match">正常匹配</span>
            <span className="legend-pill legend-pill-alert">偏差较大</span>
          </div>
          <div className="result-grid compact-metrics">
            <div>
              <span className="result-label">平均距离</span>
              <strong>{formatDistance(fusionStats.avgDistance)}</strong>
            </div>
            <div>
              <span className="result-label">最大距离</span>
              <strong>{formatDistance(fusionStats.maxDistance)}</strong>
            </div>
            <div>
              <span className="result-label">偏大数量</span>
              <strong>{fusionStats.warnCount}</strong>
            </div>
            <div>
              <span className="result-label">高风险数量</span>
              <strong>{fusionStats.highRiskCount}</strong>
            </div>
          </div>
          <div className="compact-row result-tools">
            <button className={showOnlyAlerts ? 'primary-button' : 'ghost-button'} type="button" onClick={onToggleAlerts}>
              {showOnlyAlerts ? '显示全部融合点' : '只看偏差较大'}
            </button>
            <span className="muted">阈值: {DISTANCE_ALERT_THRESHOLD.toFixed(3)}</span>
          </div>
          {fusionRows.length ? (
            <div className="fusion-table">
              <div className="fusion-row fusion-head">
                <span>人工点</span>
                <span>识别点</span>
                <span>主要肢体</span>
                <span>识别坐标</span>
                <span>人工坐标</span>
                <span>匹配距离</span>
                <span>风险</span>
              </div>
              {filteredFusionRows.map((row) => (
                <div
                  className={`fusion-row fusion-row-clickable ${row.distanceValue != null && row.distanceValue > DISTANCE_ALERT_THRESHOLD ? 'fusion-row-alert' : ''}${isFusionRowFocused(row, focusedPoint) ? ' fusion-row-focused' : ''}${hasFocusedPoint && !isFusionRowFocused(row, focusedPoint) ? ' fusion-row-dimmed' : ''}`}
                  key={`${row.detectedHoldId}-${row.routeHoldId}`}
                  onClick={() =>
                    onFocusedPointChange({
                      detectedHoldId: row.detectedHoldId,
                      routeHoldId: row.routeHoldId,
                    })
                  }
                >
                  <span>{row.routeHoldId}</span>
                  <span>{row.detectedHoldId}</span>
                  <span>{row.limbs}</span>
                  <span>{row.detectedPoint}</span>
                  <span>{row.routePoint}</span>
                  <span>{row.distance}</span>
                  <span className={`risk-badge ${row.riskClassName}`}>{row.riskLabel}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">当前还没有成功融合到人工路线点的识别结果。</p>
          )}
          {fusionRows.length > 0 && filteredFusionRows.length === 0 ? (
            <p className="muted">当前没有超过阈值的偏差点位。</p>
          ) : null}
        </section>

        <section className="result-card">
          <h2>未匹配识别点</h2>
          {unmatchedRows.length ? (
            <div className="fusion-table">
              <div className="fusion-row unmatched-head">
                <span>识别点</span>
                <span>识别坐标</span>
                <span>主要肢体</span>
                <span>使用次数</span>
              </div>
              {unmatchedRows.map((row) => (
                <div className="fusion-row unmatched-row" key={row.detectedHoldId}>
                  <span>{row.detectedHoldId}</span>
                  <span>{row.detectedPoint}</span>
                  <span>{row.limbs}</span>
                  <span>{row.usageCount}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">当前没有未匹配的识别点。</p>
          )}
        </section>

        <section className="result-card">
          <h2>最近动作</h2>
          {recentEvents.length ? (
            <div className="event-list">
              {recentEvents.map((event) => (
                <div className="event-item" key={`${event.frame}-${event.limb}-${event.hold}`}>
                  <strong>{event.limb}</strong>
                  <span>{event.hold}</span>
                  <span>帧 {event.frame}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">暂无动作事件。</p>
          )}
        </section>

        <section className="result-card">
          <h2>动作建议</h2>
          {feedback.length ? (
            <div className="event-list">
              {feedback.map((item) => (
                <div className="event-item" key={item.title}>
                  <strong>{item.title}</strong>
                  <span>{item.detail ?? '-'}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">暂无建议。</p>
          )}
        </section>

        <details className="result-card raw-json-card">
          <summary>查看原始 JSON</summary>
          <pre className="json-preview">
            {jsonPayload ? JSON.stringify(jsonPayload, null, 2) : '{\n  "summary": {},\n  "route_move_sequence": []\n}'}
          </pre>
        </details>
      </div>
    </aside>
  );
}
