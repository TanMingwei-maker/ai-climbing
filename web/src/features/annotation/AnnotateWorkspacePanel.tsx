import { lazy, Suspense } from 'react';
import type { HoldDraft } from '../../stores/annotationStore';

const FrameCanvas = lazy(async () => ({ default: (await import('../../components/FrameCanvas')).FrameCanvas }));

type AnnotateWorkspacePanelProps = {
  videoId: string;
  frameStatus: string;
  frameUrl: string | null;
  holds: HoldDraft[];
  selectedId?: string;
  routeName: string;
  wallName: string;
  angleDeg: string;
  saveStatus: string;
  validationMessage?: string;
  isDirty: boolean;
  isSaving: boolean;
  onRouteNameChange: (value: string) => void;
  onWallNameChange: (value: string) => void;
  onAngleDegChange: (value: string) => void;
  onSave: () => void;
  onGoAnalyze: () => void;
  onAddHold: (x: number, y: number) => void;
  onMoveHold: (id: string, x: number, y: number) => void;
  onSelectHold: (id: string) => void;
};

export function AnnotateWorkspacePanel({
  videoId,
  frameStatus,
  frameUrl,
  holds,
  selectedId,
  routeName,
  wallName,
  angleDeg,
  saveStatus,
  validationMessage,
  isDirty,
  isSaving,
  onRouteNameChange,
  onWallNameChange,
  onAngleDegChange,
  onSave,
  onGoAnalyze,
  onAddHold,
  onMoveHold,
  onSelectHold,
}: AnnotateWorkspacePanelProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">标注页</p>
          <h1>视频 {videoId}</h1>
          <p className="muted">{frameStatus}</p>
          <p className="muted">{isDirty ? '当前有未保存修改' : '当前修改已同步到 route_context.json'}</p>
        </div>
        <div className="button-row compact-row">
          <button className="primary-button" type="button" onClick={onSave}>
            {isSaving ? '保存中...' : '保存标注'}
          </button>
          <button className="ghost-button" type="button" onClick={onGoAnalyze}>
            去分析页
          </button>
        </div>
      </div>

      <div className="meta-grid">
        <label>
          <span>路线名</span>
          <input value={routeName} onChange={(event) => onRouteNameChange(event.target.value)} />
        </label>
        <label>
          <span>墙面名</span>
          <input value={wallName} onChange={(event) => onWallNameChange(event.target.value)} />
        </label>
        <label>
          <span>墙角度</span>
          <input value={angleDeg} onChange={(event) => onAngleDegChange(event.target.value)} placeholder="可选" />
        </label>
      </div>

      <Suspense fallback={<div className="canvas-placeholder">正在加载标注画布...</div>}>
        <FrameCanvas
          frameUrl={frameUrl}
          holds={holds}
          selectedId={selectedId}
          onAddHold={onAddHold}
          onMoveHold={onMoveHold}
          onSelectHold={onSelectHold}
        />
      </Suspense>
      {validationMessage ? <p className="muted save-status">{validationMessage}</p> : null}
      {saveStatus ? <p className="muted save-status">{saveStatus}</p> : null}
    </section>
  );
}
