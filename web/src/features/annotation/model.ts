import type { HoldDraft } from '../../stores/annotationStore';

export const DEFAULT_ROUTE_NAME = '未命名路线';
export const UNSAVED_CHANGES_MESSAGE = '当前标注还没有保存，离开后将丢失本次修改。确定继续吗？';

type AnnotationValidationInput = {
  routeName: string;
  angleDeg: string;
  holds: HoldDraft[];
};

type AnnotationSnapshotInput = {
  routeName: string;
  wallName: string;
  angleDeg: string;
  holds: HoldDraft[];
};

export function buildAnnotationSnapshot({ routeName, wallName, angleDeg, holds }: AnnotationSnapshotInput) {
  return JSON.stringify({
    routeName,
    wallName,
    angleDeg,
    holds: holds.map((hold) => ({
      id: hold.id,
      x: hold.x,
      y: hold.y,
      role: hold.role ?? null,
    })),
  });
}

export function validateAnnotationDraft({ routeName, angleDeg, holds }: AnnotationValidationInput) {
  const errors: string[] = [];
  const normalizedRouteName = routeName.trim();

  if (!normalizedRouteName) {
    errors.push('请先填写路线名。');
  }

  if (holds.length === 0) {
    errors.push('请至少标注一个人工点位。');
  }

  const ids = holds.map((hold) => hold.id.trim());
  if (ids.some((id) => !id)) {
    errors.push('点位 ID 不能为空。');
  }

  const duplicateIds = ids.filter((id, index) => id && ids.indexOf(id) !== index);
  if (duplicateIds.length > 0) {
    const uniqueDuplicates = [...new Set(duplicateIds)];
    errors.push(`点位 ID 不能重复: ${uniqueDuplicates.join(', ')}`);
  }

  const invalidCoords = holds.find(
    (hold) => !Number.isFinite(hold.x) || !Number.isFinite(hold.y) || hold.x < 0 || hold.x > 1 || hold.y < 0 || hold.y > 1,
  );
  if (invalidCoords) {
    errors.push(`点位 ${invalidCoords.id} 的坐标必须位于 0 到 1 之间。`);
  }

  if (angleDeg.trim()) {
    const angle = Number(angleDeg);
    if (!Number.isFinite(angle)) {
      errors.push('墙角度必须是有效数字。');
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}
