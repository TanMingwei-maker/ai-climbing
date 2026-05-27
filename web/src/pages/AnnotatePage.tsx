import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { getRouteContext, saveRouteContext } from '../api/annotations';
import { getApiErrorMessage, toApiUrl } from '../api/client';
import { extractFrame } from '../api/frames';
import { AnnotateSidebar } from '../features/annotation/AnnotateSidebar';
import { AnnotateWorkspacePanel } from '../features/annotation/AnnotateWorkspacePanel';
import { buildAnnotationSnapshot, DEFAULT_ROUTE_NAME, validateAnnotationDraft } from '../features/annotation/model';
import { useUnsavedChangesGuard } from '../features/annotation/useUnsavedChangesGuard';
import { useAnnotationStore } from '../stores/annotationStore';

export function AnnotatePage() {
  const { videoId = 'demo-video' } = useParams();
  return <AnnotatePageView key={videoId} videoId={videoId} />;
}

type AnnotatePageViewProps = {
  videoId: string;
};

function AnnotatePageView({ videoId }: AnnotatePageViewProps) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const holds = useAnnotationStore((state) => state.holds);
  const selectedId = useAnnotationStore((state) => state.selectedId);
  const setHolds = useAnnotationStore((state) => state.setHolds);
  const addHold = useAnnotationStore((state) => state.addHold);
  const updateHold = useAnnotationStore((state) => state.updateHold);
  const removeHold = useAnnotationStore((state) => state.removeHold);
  const setSelectedId = useAnnotationStore((state) => state.setSelectedId);
  const reset = useAnnotationStore((state) => state.reset);
  const [routeNameDraft, setRouteNameDraft] = useState<string | null>(null);
  const [wallNameDraft, setWallNameDraft] = useState<string | null>(null);
  const [angleDegDraft, setAngleDegDraft] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState('');
  const [validationMessage, setValidationMessage] = useState('');
  const focusHoldId = searchParams.get('focusHoldId')?.trim() || null;

  useEffect(() => {
    reset();
    return () => reset();
  }, [reset]);

  const routeContextQuery = useQuery({
    queryKey: ['route-context', videoId],
    queryFn: () => getRouteContext(videoId),
    staleTime: Infinity,
  });
  const frameQuery = useQuery({
    queryKey: ['frame', videoId, 'default'],
    queryFn: () => extractFrame(videoId),
    staleTime: Infinity,
  });
  const saveMutation = useMutation({
    mutationFn: () =>
      saveRouteContext(videoId, {
        wall: {
          name: wallName,
          angle_deg: angleDeg ? Number(angleDeg) : null,
        },
        route: {
          name: routeName,
        },
        holds,
      }),
    onSuccess: (payload) => {
      queryClient.setQueryData(['route-context', videoId], payload);
      setRouteNameDraft(null);
      setWallNameDraft(null);
      setAngleDegDraft(null);
      setHolds(payload.holds);
      setValidationMessage('');
      setSaveStatus('已保存 route_context.json');
    },
    onError: (error) => {
      setSaveStatus(getApiErrorMessage(error, '保存失败'));
    },
  });

  useEffect(() => {
    if (!routeContextQuery.data) {
      return;
    }

    setHolds(routeContextQuery.data.holds);
  }, [routeContextQuery.data, setHolds]);

  useEffect(() => {
    if (!focusHoldId || !holds.some((hold) => hold.id === focusHoldId)) {
      return;
    }

    setSelectedId(focusHoldId);
  }, [focusHoldId, holds, setSelectedId]);

  const routeName = routeNameDraft ?? routeContextQuery.data?.route.name ?? DEFAULT_ROUTE_NAME;
  const wallName = wallNameDraft ?? routeContextQuery.data?.wall.name ?? '默认墙面';
  const angleDeg = angleDegDraft ?? routeContextQuery.data?.wall.angle_deg?.toString() ?? '';
  const frameUrl = frameQuery.data
    ? toApiUrl(frameQuery.data.frame_url.replace('http://127.0.0.1:8000', ''))
    : null;
  const frameStatus = frameQuery.error
    ? getApiErrorMessage(frameQuery.error, '抽帧失败')
    : frameQuery.data
      ? `已抽取第 ${frameQuery.data.frame_index} 帧，可直接点击画面新增点位`
      : '正在加载标定帧...';

  const initialSnapshot = useMemo(
    () =>
      routeContextQuery.data
        ? buildAnnotationSnapshot({
            routeName: routeContextQuery.data.route.name ?? DEFAULT_ROUTE_NAME,
            wallName: routeContextQuery.data.wall.name ?? '默认墙面',
            angleDeg: routeContextQuery.data.wall.angle_deg?.toString() ?? '',
            holds: routeContextQuery.data.holds,
          })
        : null,
    [routeContextQuery.data],
  );
  const currentSnapshot = useMemo(
    () =>
      buildAnnotationSnapshot({
        routeName,
        wallName,
        angleDeg,
        holds,
      }),
    [angleDeg, holds, routeName, wallName],
  );
  const isDirty = initialSnapshot != null && initialSnapshot !== currentSnapshot;
  const { confirmNavigation } = useUnsavedChangesGuard(isDirty);

  const clearTransientStatus = () => {
    setSaveStatus('');
    setValidationMessage('');
  };

  const validation = useMemo(
    () =>
      validateAnnotationDraft({
        routeName,
        angleDeg,
        holds,
      }),
    [angleDeg, holds, routeName],
  );
  const focusStatus = useMemo(() => {
    if (!focusHoldId) {
      return '';
    }
    if (holds.length === 0) {
      return '';
    }
    return holds.some((hold) => hold.id === focusHoldId)
      ? `已定位到点位 ${focusHoldId}`
      : `未找到点位 ${focusHoldId}，请确认结果页与当前标注是否一致。`;
  }, [focusHoldId, holds]);

  const handleAddHold = (x: number, y: number) => {
    clearTransientStatus();
    addHold({
      id: `H${holds.length + 1}`,
      x,
      y,
    });
  };

  const handleSave = async () => {
    if (!validation.isValid) {
      setValidationMessage(validation.errors[0]);
      return;
    }
    setSaveStatus('正在保存...');
    await saveMutation.mutateAsync();
  };

  return (
    <main className="page two-column annotate-layout">
      <AnnotateWorkspacePanel
        videoId={videoId}
        frameStatus={frameStatus}
          frameUrl={frameUrl}
          holds={holds}
          selectedId={selectedId}
        routeName={routeName}
        wallName={wallName}
        angleDeg={angleDeg}
        saveStatus={saveStatus}
        validationMessage={validationMessage || focusStatus}
        isDirty={isDirty}
        isSaving={saveMutation.isPending}
        onRouteNameChange={(value) => {
          clearTransientStatus();
          setRouteNameDraft(value);
        }}
        onWallNameChange={(value) => {
          clearTransientStatus();
          setWallNameDraft(value);
        }}
        onAngleDegChange={(value) => {
          clearTransientStatus();
          setAngleDegDraft(value);
        }}
        onSave={() => void handleSave()}
        onGoAnalyze={() => {
          if (!validation.isValid) {
            setValidationMessage(validation.errors[0]);
            return;
          }
          if (isDirty) {
            setValidationMessage('请先保存标注，再进入分析页。');
            return;
          }
          confirmNavigation(() => navigate(`/analyze/${videoId}`));
        }}
        onAddHold={handleAddHold}
        onMoveHold={(id, x, y) => {
          clearTransientStatus();
          updateHold(id, { x, y });
        }}
        onSelectHold={setSelectedId}
      />
      <AnnotateSidebar
        holds={holds}
        selectedId={selectedId}
        onSelectHold={setSelectedId}
        onUpdateHold={(id, patch) => {
          clearTransientStatus();
          updateHold(id, patch);
        }}
        onRemoveHold={(id) => {
          clearTransientStatus();
          removeHold(id);
        }}
      />
    </main>
  );
}
