import { request } from '@/service/request';

// =============== Cache Begin ===============

/** get cache with redis */
export function fetchGetCacheRedisInfo() {
  return request<Api.Monitor.RedisInfo>({
    url: '/mon_cache/redis',
    method: 'get'
  });
}

/** clear all cache */
export function fetchClearAllCache() {
  return request({
    url: '/mon_cache/clear-all',
    method: 'post'
  });
}

/** clear specific cache by pattern */
export function fetchClearCacheByPattern(pattern: string) {
  return request({
    url: '/mon_cache/clear-pattern',
    method: 'post',
    data: { pattern }
  });
}

/** clear cache by keys */
export function fetchClearCacheByKeys(keys: string[]) {
  return request({
    url: '/mon_cache/clear-keys',
    method: 'post',
    data: { keys }
  });
}

// =============== Cache End ===============
