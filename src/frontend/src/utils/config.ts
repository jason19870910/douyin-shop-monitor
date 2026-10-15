export interface AppConfig {
  apiBaseUrl: string;
  isDevelopment: boolean;
  isProduction: boolean;
  enableDevTools: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
}

const getApiBaseUrl = (): string => {
  // Explicit env var takes highest priority (should NOT include /api/v1 suffix)
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) {
    // Remove trailing /api/v1 if present to avoid double prefix
    return envUrl.replace(/\/api\/v1\/?$/, '');
  }

  // In production, use relative URL without v1 prefix (axios baseURL will handle it)
  if (import.meta.env.PROD) {
    return '';
  }

  // Development: if no env var, use relative URL (Vite proxy will handle it)
  // This works for both localhost and remote dev servers
  return '';
};

const getConfig = (): AppConfig => {
  const isDev = import.meta.env.DEV;
  const isProd = import.meta.env.PROD;

  return {
    apiBaseUrl: getApiBaseUrl(),
    isDevelopment: isDev,
    isProduction: isProd,
    enableDevTools: isDev,
    logLevel: isDev ? 'debug' : 'warn',
  };
};

export const config = getConfig();

export const getApiBaseUrlPublic = (): string => config.apiBaseUrl;

export const isDevelopment = (): boolean => config.isDevelopment;

export const isProduction = (): boolean => config.isProduction;

export const log = (level: AppConfig['logLevel'], ...args: unknown[]): void => {
  const levels = { debug: 0, info: 1, warn: 2, error: 3 };
  if (levels[level] >= levels[config.logLevel]) {
    const prefix = `[${level.toUpperCase()}]`;
    if (import.meta.env.DEV) {
      switch (level) {
        case 'debug':
          // eslint-disable-next-line no-console
          console.debug(prefix, ...args);
          break;
        case 'info':
          // eslint-disable-next-line no-console
          console.info(prefix, ...args);
          break;
        case 'warn':
          // eslint-disable-next-line no-console
          console.warn(prefix, ...args);
          break;
        case 'error':
          // eslint-disable-next-line no-console
          console.error(prefix, ...args);
          break;
      }
    }
  }
};