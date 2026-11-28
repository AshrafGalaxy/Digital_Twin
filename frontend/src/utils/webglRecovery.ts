export interface WebGLContextRecoveryHandlers {
  onLost: (event: Event) => void;
  onRestored: (event: Event) => void;
}

export interface CanvasListenerTarget {
  addEventListener: (type: string, listener: EventListenerOrEventListenerObject, options?: boolean | AddEventListenerOptions) => void;
  removeEventListener: (type: string, listener: EventListenerOrEventListenerObject, options?: boolean | EventListenerOptions) => void;
}

/**
 * Attaches webglcontextlost and webglcontextrestored listeners to a WebGL canvas.
 * Calls event.preventDefault() on webglcontextlost so the browser allows restoration.
 * Returns a cleanup callback that detaches both listeners.
 */
export function attachWebGLContextListeners(
  canvas: CanvasListenerTarget | null | undefined,
  handlers: WebGLContextRecoveryHandlers
): () => void {
  if (
    !canvas ||
    typeof canvas.addEventListener !== 'function' ||
    typeof canvas.removeEventListener !== 'function'
  ) {
    return () => {};
  }

  const handleLost = (event: Event): void => {
    if (typeof event.preventDefault === 'function') {
      event.preventDefault();
    }
    handlers.onLost(event);
  };

  const handleRestored = (event: Event): void => {
    handlers.onRestored(event);
  };

  canvas.addEventListener('webglcontextlost', handleLost, false);
  canvas.addEventListener('webglcontextrestored', handleRestored, false);

  return () => {
    canvas.removeEventListener('webglcontextlost', handleLost, false);
    canvas.removeEventListener('webglcontextrestored', handleRestored, false);
  };
}
