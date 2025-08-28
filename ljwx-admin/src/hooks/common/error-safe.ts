// @ts-nocheck
// 安全的Vue组合式函数 - 处理refs和异步错误
import { nextTick, onBeforeUnmount, ref } from 'vue';

// 安全的异步数据加载Hook
export const useSafeAsync = (defaultValue = null) => {
  const data = ref(defaultValue);
  const loading = ref(false);
  const error = ref(null);

  const execute = async asyncFn => {
    loading.value = true;
    error.value = null;

    try {
      const result = await asyncFn();
      data.value = result;
      return result;
    } catch (err) {
      const errorMsg = err?.message || '操作失败';
      error.value = errorMsg;
      console.warn('异步操作安全拦截:', errorMsg);
      return defaultValue;
    } finally {
      loading.value = false;
    }
  };

  return { data, loading, error, execute };
};

// 安全的refs访问Hook
export const useSafeRef = (initialValue = null) => {
  const elementRef = ref(initialValue);
  const isDestroyed = ref(false);

  onBeforeUnmount(() => {
    isDestroyed.value = true;
  });

  const safeAccess = (callback, fallback) => {
    if (isDestroyed.value) {
      console.warn('组件已销毁，跳过refs访问');
      fallback?.();
      return;
    }

    if (elementRef.value) {
      try {
        callback(elementRef.value);
      } catch (err) {
        console.warn('refs访问安全拦截:', err?.message);
        fallback?.();
      }
    } else {
      fallback?.();
    }
  };

  const safeAccessNextTick = async (callback, fallback) => {
    if (isDestroyed.value) return;

    await nextTick();
    safeAccess(callback, fallback);
  };

  return {
    elementRef,
    safeAccess,
    safeAccessNextTick,
    isDestroyed: () => isDestroyed.value
  };
};

// 安全的数组操作Hook
export const useSafeArray = (initialValue = []) => {
  const arrayRef = ref([...initialValue]);

  const safePush = (...items) => {
    try {
      if (!Array.isArray(arrayRef.value)) {
        arrayRef.value = [];
      }
      arrayRef.value.push(...items);
    } catch (err) {
      console.warn('数组操作安全拦截:', err?.message);
      arrayRef.value = [...initialValue, ...items];
    }
  };

  const safeSet = newArray => {
    try {
      arrayRef.value = Array.isArray(newArray) ? [...newArray] : [];
    } catch (err) {
      console.warn('数组设置安全拦截:', err?.message);
      arrayRef.value = [];
    }
  };

  const safeClear = () => {
    try {
      arrayRef.value = [];
    } catch (err) {
      console.warn('数组清空安全拦截:', err?.message);
      arrayRef.value = [];
    }
  };

  return {
    arrayRef,
    safePush,
    safeSet,
    safeClear,
    get length() {
      return arrayRef.value?.length || 0;
    }
  };
};
