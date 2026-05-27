import { useEffect } from 'react';
import { useBlocker } from 'react-router-dom';
import { UNSAVED_CHANGES_MESSAGE } from './model';

export function useUnsavedChangesGuard(enabled: boolean) {
  const blocker = useBlocker(enabled);

  useEffect(() => {
    if (blocker.state !== 'blocked') {
      return;
    }

    if (window.confirm(UNSAVED_CHANGES_MESSAGE)) {
      blocker.proceed();
      return;
    }

    blocker.reset();
  }, [blocker]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [enabled]);

  return {
    confirmNavigation(action: () => void) {
      if (!enabled || window.confirm(UNSAVED_CHANGES_MESSAGE)) {
        action();
      }
    },
  };
}
