/**
 * 安全访问工具函数 - 修复ljwx-admin中的refs和数组访问错误
 */

/**
 * 安全的ref访问
 */
export const safeRef = <T>(ref: { value: T | null }, fallback: T): T => {
  return ref?.value ?? fallback;
};

/**
 * 安全的数组push操作
 */
export const safePush = <T>(arr: T[] | undefined | null, item: T): T[] => {
  if (!Array.isArray(arr)) {
    return [item];
  }
  arr.push(item);
  return arr;
};

/**
 * 安全的对象属性访问
 */
export const safeGet = <T>(obj: any, path: string, defaultValue: T): T => {
  if (!obj || typeof obj !== 'object') return defaultValue;

  const keys = path.split('.');
  let result = obj;

  for (const key of keys) {
    if (result === null || result === undefined) {
      return defaultValue;
    }
    result = result[key];
  }

  return result ?? defaultValue;
};

/**
 * 安全的API响应数据访问
 */
export const safeApiData = <T>(response: any, defaultValue: T): T => {
  return response?.data ?? defaultValue;
};

/**
 * 安全的健康数据格式化
 */
export const safeFormatHealthData = (data: any) => {
  if (!data || typeof data !== 'object') return null;

  const formatValue = (value: any, unit = '') =>
    value !== null && value !== undefined ? `${value}${unit}` : '无数据';

  return {
    heartRate: formatValue(data.heartRate || data.heart_rate, ' bpm'),
    bloodPressure: `${formatValue(data.pressureHigh || data.pressure_high)} / ${formatValue(data.pressureLow || data.pressure_low)} mmHg`,
    temperature: formatValue(data.temperature, '°C'),
    bloodOxygen: formatValue(data.bloodOxygen || data.blood_oxygen, '%'),
    stress: formatValue(data.stress),
    step: formatValue(data.step),
    location: `${formatValue(data.latitude, '°')}, ${formatValue(data.longitude, '°')}, ${formatValue(data.altitude, 'm')}`
  };
};

/**
 * 安全的组件props访问
 */
export const safeProps = <T extends Record<string, any>>(props: T, defaults: Partial<T>): T => {
  return { ...defaults, ...props };
};

/**
 * 安全的本地存储操作
 */
export const safeStorage = {
  get: <T>(key: string, defaultValue: T): T => {
    try {
      const value = localStorage.getItem(key);
      return value ? JSON.parse(value) : defaultValue;
    } catch {
      return defaultValue;
    }
  },
  set: (key: string, value: any): boolean => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch {
      return false;
    }
  }
};

/**
 * 防抖安全执行
 */
export const safeDebounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;

  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      try {
        func(...args);
      } catch (error) {
        console.error('防抖函数执行错误:', error);
      }
    }, wait);
  };
};

/**
 * 安全的异步执行
 */
export const safeAsync = async <T>(
  asyncFn: () => Promise<T>,
  errorHandler?: (error: any) => T
): Promise<T | null> => {
  try {
    return await asyncFn();
  } catch (error) {
    console.error('异步操作错误:', error);
    return errorHandler ? errorHandler(error) : null;
  }
};
