/** 用户管理权限配置 */
export const USER_PERMISSIONS = {
  // 基础用户权限
  USER_VIEW: 'sys:user:view',
  USER_ADD: 'sys:user:add',
  USER_UPDATE: 'sys:user:update',
  USER_DELETE: 'sys:user:delete',
  USER_RESET_PASSWORD: 'sys:user:resetPassword',
  USER_RESPONSIBILITIES: 'sys:user:responsibilities',

  // 管理员专用权限
  ADMIN_MANAGE: 'sys:user:manage:admin', // 管理管理员权限
  ADMIN_VIEW_ALL: 'sys:admin:view:all', // 查看所有管理员
  ADMIN_EDIT: 'sys:admin:edit', // 编辑管理员
  ADMIN_DELETE: 'sys:admin:delete', // 删除管理员

  // 视图模式权限
  VIEW_MODE_ALL: 'sys:user:viewMode:all',
  VIEW_MODE_EMPLOYEE: 'sys:user:viewMode:employee',
  VIEW_MODE_ADMIN: 'sys:user:viewMode:admin'
} as const;

/** 权限组合配置 */
export const PERMISSION_GROUPS = {
  // 基础员工管理
  EMPLOYEE_MANAGER: [
    USER_PERMISSIONS.USER_VIEW,
    USER_PERMISSIONS.USER_ADD,
    USER_PERMISSIONS.USER_UPDATE,
    USER_PERMISSIONS.USER_DELETE,
    USER_PERMISSIONS.VIEW_MODE_EMPLOYEE
  ]
} as const;

// 完整用户管理（包含管理员）- 单独定义避免循环依赖
export const FULL_USER_MANAGER_PERMISSIONS = [
  ...PERMISSION_GROUPS.EMPLOYEE_MANAGER,
  USER_PERMISSIONS.ADMIN_MANAGE,
  USER_PERMISSIONS.ADMIN_VIEW_ALL,
  USER_PERMISSIONS.ADMIN_EDIT,
  USER_PERMISSIONS.ADMIN_DELETE,
  USER_PERMISSIONS.VIEW_MODE_ALL,
  USER_PERMISSIONS.VIEW_MODE_ADMIN
] as const;

/** 基于用户类型的操作权限检查 */
export const getOperationPermissions = (currentUserIsAdmin: boolean, targetUserIsAdmin: boolean) => {
  return {
    canEdit: currentUserIsAdmin || !targetUserIsAdmin,
    canDelete: currentUserIsAdmin || !targetUserIsAdmin,
    canResetPassword: true, // 所有用户都可以重置密码
    canManageResponsibilities: currentUserIsAdmin || !targetUserIsAdmin,
    canViewProfile: true // 所有用户都可以查看档案
  };
};

/** 视图模式访问权限 */
export const VIEW_MODE_ACCESS = {
  all: ['ADMIN', 'MANAGER'], // 全部视图：管理员和管理者
  employee: ['ADMIN', 'MANAGER', 'HR'], // 员工视图：管理员、管理者、HR
  admin: ['ADMIN'] // 管理员视图：仅管理员
} as const;
