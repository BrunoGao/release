// 全局安全防护工具
export const safeCall = (fn, fallback = null) => {
  try {
    return fn();
  } catch (e) {
    console.warn('安全调用拦截:', e.message);
    return fallback;
  }
};

export const safeAsync = async (fn, fallback = null) => {
  try {
    return await fn();
  } catch (e) {
    console.warn('异步安全调用拦截:', e.message);
    return fallback;
  }
};

export const safeRef = (ref, fn, fallback) => {
  if (ref?.value) {
    try {
      return fn(ref.value);
    } catch (e) {
      console.warn('refs访问拦截:', e.message);
      return fallback?.();
    }
  }
  return fallback?.();
};

export const safeArray = (arr, item) => {
  try {
    if (Array.isArray(arr)) {
      arr.push(item);
    } else {
      console.warn('数组访问拦截: 对象不是数组');
    }
  } catch (e) {
    console.warn('数组操作拦截:', e.message);
  }
};
