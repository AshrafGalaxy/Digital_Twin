import { useEffect, useRef } from 'react';

/**
 * useFocusTrap
 * Traps keyboard focus within an active dialog or drawer,
 * wraps Tab / Shift+Tab cycles, listens for Escape to close,
 * and restores previous focus when unmounted or deactivated.
 * Complies strictly with WCAG 2.1 AA criteria 2.1.1 (Keyboard) and 2.1.2 (No Keyboard Trap).
 */
export function useFocusTrap(
  containerRef: React.RefObject<HTMLElement | null>,
  isActive: boolean,
  onClose?: () => void
) {
  const previousActiveElement = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    // Save previous active element to restore focus when deactivated
    previousActiveElement.current = document.activeElement as HTMLElement;

    const getFocusableElements = (): HTMLElement[] => {
      if (!containerRef.current) return [];
      const focusableSelectors = [
        'a[href]',
        'button:not([disabled])',
        'textarea:not([disabled])',
        'input:not([disabled])',
        'select:not([disabled])',
        '[tabindex]:not([tabindex="-1"])'
      ].join(', ');

      return Array.from(
        containerRef.current.querySelectorAll<HTMLElement>(focusableSelectors)
      ).filter((el) => el.offsetParent !== null); // only visible elements
    };

    // Auto-focus first focusable element or container
    const focusables = getFocusableElements();
    if (focusables.length > 0) {
      focusables[0].focus();
    } else {
      containerRef.current.focus();
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        onClose?.();
        return;
      }

      if (e.key === 'Tab') {
        const elements = getFocusableElements();
        if (elements.length === 0) {
          e.preventDefault();
          return;
        }

        const firstElement = elements[0];
        const lastElement = elements[elements.length - 1];

        if (e.shiftKey) {
          if (
            document.activeElement === firstElement ||
            document.activeElement === containerRef.current
          ) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown, true);

    return () => {
      window.removeEventListener('keydown', handleKeyDown, true);
      if (
        previousActiveElement.current &&
        typeof previousActiveElement.current.focus === 'function'
      ) {
        previousActiveElement.current.focus();
      }
    };
  }, [isActive, containerRef, onClose]);
}
