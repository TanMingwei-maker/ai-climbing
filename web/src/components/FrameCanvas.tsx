import type Konva from 'konva';
import { useEffect, useMemo, useState } from 'react';
import { Circle, Group, Image as KonvaImage, Layer, Rect, Stage, Text } from 'react-konva';
import type { HoldDraft } from '../stores/annotationStore';

const MAX_STAGE_WIDTH = 760;

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

function useStageImage(src: string | null) {
  const [image, setImage] = useState<HTMLImageElement | null>(() => null);

  useEffect(() => {
    if (!src) {
      return;
    }

    const nextImage = new window.Image();
    nextImage.crossOrigin = 'anonymous';
    nextImage.src = src;
    nextImage.onload = () => setImage(nextImage);
    return () => {
      nextImage.onload = null;
    };
  }, [src]);

  return image;
}

type FrameCanvasProps = {
  frameUrl: string | null;
  holds: HoldDraft[];
  selectedId?: string;
  onAddHold: (x: number, y: number) => void;
  onMoveHold: (id: string, x: number, y: number) => void;
  onSelectHold: (id: string) => void;
};

export function FrameCanvas({
  frameUrl,
  holds,
  selectedId,
  onAddHold,
  onMoveHold,
  onSelectHold,
}: FrameCanvasProps) {
  const image = useStageImage(frameUrl);

  const size = useMemo(() => {
    if (!image) {
      return { width: MAX_STAGE_WIDTH, height: 420 };
    }
    const scale = Math.min(MAX_STAGE_WIDTH / image.width, 1);
    return {
      width: Math.round(image.width * scale),
      height: Math.round(image.height * scale),
    };
  }, [image]);

  const handleStagePointerDown = (event: Konva.KonvaEventObject<MouseEvent>) => {
    const stage = event.target.getStage();
    if (!stage || !image) {
      return;
    }

    const clickedOnMarker = event.target.hasName('hold-marker') || event.target.getParent()?.hasName('hold-marker');
    if (clickedOnMarker) {
      return;
    }

    const pointer = stage.getPointerPosition();
    if (!pointer) {
      return;
    }

    onAddHold(clamp(pointer.x / size.width, 0, 1), clamp(pointer.y / size.height, 0, 1));
  };

  return (
    <div className="canvas-shell">
      {image ? (
        <Stage width={size.width} height={size.height} onMouseDown={handleStagePointerDown}>
          <Layer>
            <KonvaImage image={image} width={size.width} height={size.height} listening />
            {holds.map((hold) => {
              const x = hold.x * size.width;
              const y = hold.y * size.height;
              const isSelected = hold.id === selectedId;
              const labelWidth = Math.max(48, hold.id.length * 12);

              return (
                <Group
                  key={hold.id}
                  x={x}
                  y={y}
                  draggable
                  name="hold-marker"
                  onClick={() => onSelectHold(hold.id)}
                  onTap={() => onSelectHold(hold.id)}
                  onDragEnd={(dragEvent) => {
                    const nextX = clamp(dragEvent.target.x() / size.width, 0, 1);
                    const nextY = clamp(dragEvent.target.y() / size.height, 0, 1);
                    onMoveHold(hold.id, nextX, nextY);
                  }}
                >
                  <Circle
                    radius={12}
                    fill="rgba(37, 99, 235, 0.22)"
                    stroke={isSelected ? '#f8fafc' : '#60a5fa'}
                    strokeWidth={isSelected ? 3 : 2}
                  />
                  <Circle radius={4} fill="#60a5fa" />
                  <Rect
                    x={16}
                    y={-30}
                    width={labelWidth}
                    height={24}
                    cornerRadius={12}
                    fill="rgba(15, 23, 42, 0.88)"
                    stroke={isSelected ? '#f8fafc' : '#60a5fa'}
                    strokeWidth={1.5}
                  />
                  <Text x={28} y={-24} text={hold.id} fontSize={13} fill="#f8fafc" />
                </Group>
              );
            })}
          </Layer>
        </Stage>
      ) : (
        <div className="canvas-placeholder">上传并抽帧后在这里标点</div>
      )}
    </div>
  );
}
