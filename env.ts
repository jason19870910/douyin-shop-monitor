export const isBrowser = (): boolean => typeof window !== 'undefined';

export const isServer = (): boolean => !isBrowser();

export const getWindow = (): Window | undefined => isBrowser() ? window : undefined;

export const getDocument = (): Document | undefined => isBrowser() ? document : undefined;

export const getLocalStorage = (): Storage | undefined => {
  if (!isBrowser()) return undefined;
  try {
    return window.localStorage;
  } catch {
    return undefined;
  }
};

export const getSessionStorage = (): Storage | undefined => {
  if (!isBrowser()) return undefined;
  try {
    return window.sessionStorage;
  } catch {
    return undefined;
  }
};

export const getNavigator = (): Navigator | undefined => isBrowser() ? navigator : undefined;

export const getLocation = (): Location | undefined => isBrowser() ? window.location : undefined;

export const getOrigin = (): string => {
  const loc = getLocation();
  return loc?.origin ?? (isServer() ? 'http://localhost' : '');
};

export const getHref = (): string => {
  const loc = getLocation();
  return loc?.href ?? '';
};

export const safeSetTimeout = (
  callback: TimerHandler,
  delay: number,
  ...args: unknown[]
): number | undefined => {
  if (!isBrowser()) return undefined;
  return window.setTimeout(callback, delay, ...args);
};

export const safeSetInterval = (
  callback: TimerHandler,
  delay: number,
  ...args: unknown[]
): number | undefined => {
  if (!isBrowser()) return undefined;
  return window.setInterval(callback, delay, ...args);
};

export const safeClearTimeout = (id: number | undefined): void => {
  if (!isBrowser() || id === undefined) return;
  window.clearTimeout(id);
};

export const safeClearInterval = (id: number | undefined): void => {
  if (!isBrowser() || id === undefined) return;
  window.clearInterval(id);
};

export const safeAddEventListener = <K extends keyof WindowEventMap>(
  type: K,
  listener: (this: Window, ev: WindowEventMap[K]) => unknown,
  options?: boolean | AddEventListenerOptions
): void => {
  if (!isBrowser()) return;
  window.addEventListener(type, listener, options);
};

export const safeRemoveEventListener = <K extends keyof WindowEventMap>(
  type: K,
  listener: (this: Window, ev: WindowEventMap[K]) => unknown,
  options?: boolean | EventListenerOptions
): void => {
  if (!isBrowser()) return;
  window.removeEventListener(type, listener, options);
};

export const requestIdleCallback = (
  callback: IdleRequestCallback,
  options?: IdleRequestOptions
): number | undefined => {
  if (!isBrowser()) return undefined;
  return window.requestIdleCallback
    ? window.requestIdleCallback(callback, options)
    : window.setTimeout(() => callback({ timeRemaining: () => 1 } as IdleDeadline), 1);
};

export const cancelIdleCallback = (id: number | undefined): void => {
  if (!isBrowser() || id === undefined) return;
  if (window.cancelIdleCallback) {
    window.cancelIdleCallback(id);
  } else {
    window.clearTimeout(id);
  }
};