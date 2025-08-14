// Vue错误边界和防护工具 - 专门解决refs和push错误
import { nextTick, type Ref } from 'vue'

// 安全访问refs，防止"Cannot read properties of null (reading 'refs')"
export const safeRef = <T>(ref: Ref<T | null>, callback: (value: T) => void, fallback?: () => void) => {
  if (ref.value) {
    try {
      callback(ref.value)
    } catch (error) {
      console.warn('refs访问错误:', error)
      fallback?.()
    }
  } else {
    fallback?.()
  }
}

// 延迟安全访问，确保DOM渲染完成
export const safeRefNextTick = async <T>(ref: Ref<T | null>, callback: (value: T) => void, fallback?: () => void) => {
  await nextTick()
  safeRef(ref, callback, fallback)
}

// 安全数组操作，防止"Cannot read properties of undefined (reading 'push')"
export const safePush = <T>(target: any, key: string, item: T): T[] => {
  if (!target) return [item]
  if (!Array.isArray(target[key])) {
    target[key] = []
  }
  target[key].push(item)
  return target[key]
}

// 安全对象属性访问
export const safeGet = (obj: any, path: string, defaultValue: any = null) => {
  try {
    return path.split('.').reduce((current, key) => current?.[key], obj) ?? defaultValue
  } catch {
    return defaultValue
  }
}

// 安全事件处理包装器
export const safeHandler = <T extends (...args: any[]) => any>(handler: T): T => {
  return ((...args: any[]) => {
    try {
      return handler(...args)
    } catch (error) {
      console.warn('事件处理错误:', error)
      return null
    }
  }) as T
}

// 安全的异步操作
export const safeAsync = async <T>(asyncFn: () => Promise<T>, fallback: T): Promise<T> => {
  try {
    return await asyncFn()
  } catch (error) {
    console.warn('异步操作错误:', error)
    return fallback
  }
}

// 防护装饰器 - 用于类方法
export const errorBoundary = (target: any, propertyKey: string, descriptor: PropertyDescriptor) => {
  const originalMethod = descriptor.value
  descriptor.value = function (...args: any[]) {
    try {
      const result = originalMethod.apply(this, args)
      if (result instanceof Promise) {
        return result.catch((error: any) => {
          console.warn(`方法${propertyKey}异步错误:`, error)
          return null
        })
      }
      return result
    } catch (error) {
      console.warn(`方法${propertyKey}同步错误:`, error)
      return null
    }
  }
  return descriptor
}

// 全局错误恢复策略
export const createErrorRecovery = () => {
  const errorCount = new Map<string, number>()

  return {
    // 记录错误并判断是否需要重置
    recordError: (key: string, maxRetries = 3) => {
      const count = (errorCount.get(key) || 0) + 1
      errorCount.set(key, count)

      if (count >= maxRetries) {
        console.warn(`错误${key}达到最大重试次数，执行重置`)
        errorCount.delete(key)
        return 'reset'
      }
      return 'retry'
    },

    // 清除错误计数
    clearError: (key: string) => {
      errorCount.delete(key)
    },

    // 获取错误统计
    getErrorStats: () => Object.fromEntries(errorCount.entries())
  }
}
