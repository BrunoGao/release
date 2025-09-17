import { useAuthStore } from '@/store/modules/auth';

/**
 * 检查用户是否有指定权限
 * @param permission 权限码，如 'license:management:import'
 * @returns boolean
 */
export function hasPermission(permission: string): boolean {
  const authStore = useAuthStore();
  
  // 如果没有权限数组，返回 false
  if (!authStore.userInfo.permissions || authStore.userInfo.permissions.length === 0) {
    return false;
  }
  
  // 检查权限数组中是否包含指定权限
  return authStore.userInfo.permissions.includes(permission);
}

/**
 * 检查用户是否有任意一个权限
 * @param permissions 权限码数组
 * @returns boolean
 */
export function hasAnyPermission(permissions: string[]): boolean {
  return permissions.some(permission => hasPermission(permission));
}

/**
 * 检查用户是否拥有所有指定权限
 * @param permissions 权限码数组
 * @returns boolean
 */
export function hasAllPermissions(permissions: string[]): boolean {
  return permissions.every(permission => hasPermission(permission));
}

/**
 * 检查用户是否为超级管理员
 * @returns boolean
 */
export function isSuperAdmin(): boolean {
  const authStore = useAuthStore();
  return authStore.isStaticSuper;
}