import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { toApiUrl } from '../api/client';
import { getVideo } from '../api/videos';
import { ResultInsightsPanel } from '../features/result/ResultInsightsPanel';
import { ResultVideoPanel } from '../features/result/ResultVideoPanel';
import {
  DISTANCE_ALERT_THRESHOLD,
  buildFusionRows,
  buildFusionStats,
  buildRecentEvents,
  buildUnmatchedRows,
  fetchResultJson,
  getOptionalResult,
  getResultStatusMessage,
  type FocusTarget,
  type ScatterDetectedPoint,
} from '../features/result/model';

export function ResultPage() {
  const { videoId = 'demo-video' } = useParams();
  const [showOnlyAlerts, setShowOnlyAlerts] = useState(false);
  const [focusedPoint, setFocusedPoint] = useState<FocusTarget | null>(null);
  const videoQuery = useQuery({
    queryKey: ['video', videoId],
    queryFn: () => getVideo(videoId),
    retry: false,
  });
  const resultQuery = useQuery({
    queryKey: ['analysis-result', videoId],
    queryFn: () => getOptionalResult(videoId),
    retry: false,
  });
  const jsonQuery = useQuery({
    queryKey: ['analysis-result-json', videoId, resultQuery.data?.result_json_url],
    queryFn: () => fetchResultJson(resultQuery.data!.result_json_url),
    enabled: Boolean(resultQuery.data?.result_json_url),
    retry: false,
  });

  const hasResult = Boolean(resultQuery.data);
  const status = getResultStatusMessage({
    isPending: videoQuery.isPending || resultQuery.isPending || jsonQuery.isPending,
    videoError: videoQuery.error,
    resultError: resultQuery.error,
    jsonError: jsonQuery.error,
    hasResult,
  });
  const videoUrl = resultQuery.data ? toApiUrl(resultQuery.data.result_video_url) : null;
  const jsonPayload = jsonQuery.data ?? null;

  const summary = jsonPayload?.summary;
  const routeContext = jsonPayload?.route_context;
  const holds = jsonPayload?.holds ?? [];
  const routeHolds = routeContext?.holds ?? [];
  const fusionRows = buildFusionRows(holds);
  const unmatchedRows = buildUnmatchedRows(holds);
  const fusionStats = buildFusionStats(fusionRows);
  const filteredFusionRows = showOnlyAlerts
    ? fusionRows.filter((row) => row.distanceValue != null && row.distanceValue > DISTANCE_ALERT_THRESHOLD)
    : fusionRows;
  const recentEvents = buildRecentEvents(jsonPayload?.route_move_sequence ?? []);
  const feedback = jsonPayload?.feedback ?? [];
  const scatterDetectedPoints: ScatterDetectedPoint[] = holds.map((hold) => ({
    holdId: hold.hold_id,
    x: hold.x,
    y: hold.y,
    routeHoldId: hold.route_hold_id,
    routeX: hold.route_x,
    routeY: hold.route_y,
    matchDistance: hold.match_distance,
  }));

  return (
    <main className="page two-column">
      <ResultVideoPanel videoId={videoId} status={status} videoUrl={videoUrl} hasResult={hasResult} />
      <ResultInsightsPanel
        videoId={videoId}
        summary={summary}
        routeContext={routeContext}
        routeHolds={routeHolds}
        fusionRows={fusionRows}
        fusionStats={fusionStats}
        filteredFusionRows={filteredFusionRows}
        unmatchedRows={unmatchedRows}
        recentEvents={recentEvents}
        feedback={feedback}
        jsonPayload={jsonPayload}
        scatterDetectedPoints={scatterDetectedPoints}
        showOnlyAlerts={showOnlyAlerts}
        focusedPoint={focusedPoint}
        onToggleAlerts={() => setShowOnlyAlerts((value) => !value)}
        onFocusedPointChange={setFocusedPoint}
      />
    </main>
  );
}
