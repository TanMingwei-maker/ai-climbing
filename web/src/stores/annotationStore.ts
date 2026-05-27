import { create } from 'zustand';

export type HoldDraft = {
  id: string;
  x: number;
  y: number;
  role?: 'start' | 'top' | 'finish';
};

type AnnotationState = {
  holds: HoldDraft[];
  selectedId?: string;
  setHolds: (holds: HoldDraft[]) => void;
  addHold: (hold: HoldDraft) => void;
  updateHold: (id: string, patch: Partial<HoldDraft>) => void;
  removeHold: (id: string) => void;
  setSelectedId: (id?: string) => void;
  reset: () => void;
};

export const useAnnotationStore = create<AnnotationState>((set) => ({
  holds: [],
  selectedId: undefined,
  setHolds: (holds) => set({ holds, selectedId: holds[0]?.id }),
  addHold: (hold) =>
    set((state) => ({
      holds: [...state.holds, hold],
      selectedId: hold.id,
    })),
  updateHold: (id, patch) =>
    set((state) => ({
      holds: state.holds.map((hold) => (hold.id === id ? { ...hold, ...patch } : hold)),
    })),
  removeHold: (id) =>
    set((state) => {
      const nextHolds = state.holds.filter((hold) => hold.id !== id);
      return {
        holds: nextHolds,
        selectedId: state.selectedId === id ? nextHolds[0]?.id : state.selectedId,
      };
    }),
  setSelectedId: (id) => set({ selectedId: id }),
  reset: () => set({ holds: [], selectedId: undefined }),
}));
