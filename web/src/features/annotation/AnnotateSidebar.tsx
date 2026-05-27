import type { HoldDraft } from '../../stores/annotationStore';

type AnnotateSidebarProps = {
  holds: HoldDraft[];
  selectedId?: string;
  onSelectHold: (id: string) => void;
  onUpdateHold: (id: string, patch: Partial<HoldDraft>) => void;
  onRemoveHold: (id: string) => void;
};

export function AnnotateSidebar({
  holds,
  selectedId,
  onSelectHold,
  onUpdateHold,
  onRemoveHold,
}: AnnotateSidebarProps) {
  const selectedHold = holds.find((hold) => hold.id === selectedId);

  return (
    <aside className="panel side-panel">
      <p className="eyebrow">路线点位</p>
      <div className="list point-list">
        {holds.length === 0 ? <p className="muted">点击左侧图片任意位置新增点位</p> : null}
        {holds.map((hold) => (
          <button
            key={hold.id}
            className={`list-item selectable ${hold.id === selectedId ? 'selected' : ''}`}
            type="button"
            onClick={() => onSelectHold(hold.id)}
          >
            <strong>{hold.id}</strong>
            <span>
              ({hold.x.toFixed(3)}, {hold.y.toFixed(3)})
            </span>
          </button>
        ))}
      </div>

      {selectedHold ? (
        <div className="editor-card">
          <h2>编辑点位</h2>
          <label>
            <span>ID</span>
            <input value={selectedHold.id} onChange={(event) => onUpdateHold(selectedHold.id, { id: event.target.value })} />
          </label>
          <label>
            <span>角色</span>
            <select
              value={selectedHold.role ?? ''}
              onChange={(event) =>
                onUpdateHold(selectedHold.id, {
                  role: event.target.value ? (event.target.value as 'start' | 'top' | 'finish') : undefined,
                })
              }
            >
              <option value="">普通点</option>
              <option value="start">start</option>
              <option value="top">top</option>
              <option value="finish">finish</option>
            </select>
          </label>
          <div className="coord-row">
            <label>
              <span>X</span>
              <input
                type="number"
                min="0"
                max="1"
                step="0.001"
                value={selectedHold.x}
                onChange={(event) => onUpdateHold(selectedHold.id, { x: Number(event.target.value) })}
              />
            </label>
            <label>
              <span>Y</span>
              <input
                type="number"
                min="0"
                max="1"
                step="0.001"
                value={selectedHold.y}
                onChange={(event) => onUpdateHold(selectedHold.id, { y: Number(event.target.value) })}
              />
            </label>
          </div>
          <button className="danger-button" type="button" onClick={() => onRemoveHold(selectedHold.id)}>
            删除当前点位
          </button>
        </div>
      ) : null}
    </aside>
  );
}
