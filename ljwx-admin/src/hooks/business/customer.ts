import { computed } from 'vue';
import { useAuthStore } from '@/store/modules/auth';
import { type CustomerAccess, useCustomerStore } from '@/store/modules/customer';
import { fetchGetAllAvailableCustomers } from '@/service/api/customer/customer';
import { fetchCustomerIdByOrgId } from '@/service/api';

/** 客户业务逻辑 Hook */
export function useCustomer() {
  const authStore = useAuthStore();
  const customerStore = useCustomerStore();

  // 当前用户角色
  const userRole = computed(() => authStore.userInfo?.roleIds?.[0] || '');
  const userInfo = computed(() => authStore.userInfo);

  // 是否是 admin 用户
  const isAdmin = computed(() => userInfo.value?.userName === 'admin');

  /** 根据用户角色确定客户访问权限 */
  const determineCustomerAccess = async (): Promise<CustomerAccess> => {
    const user = userInfo.value;

    if (!user) {
      throw new Error('用户信息不存在');
    }

    if (isAdmin.value) {
      // admin 用户：可以切换客户，需要加载所有客户列表
      const { data } = await fetchGetAllAvailableCustomers();
      const customerList = (data || []).map(item => ({
        id: item.customerId.toString(), // 转换为字符串避免精度问题
        name: item.customerName,
        code: item.customerId.toString(),
        status: 'ACTIVE',
        description: `客户ID: ${item.customerId}`
      }));

      return {
        canSwitch: true,
        defaultCustomerId: null, // 需要手动选择
        customerList
      };
    }
    // 其他用户：不能切换，使用自己的客户ID
    const customerId = user.customerId;

    // 如果用户没有直接的 customerId，尝试通过 orgId 获取
    // 注意：如果用户类型定义中没有 orgId 字段，这部分逻辑需要调整
    // if (!customerId && user.orgId && Array.isArray(user.orgId) && user.orgId.length > 0) {
    //   try {
    //     const { data } = await fetchCustomerIdByOrgId(user.orgId[0]);
    //     customerId = data.customerId;
    //   } catch (error) {
    //     console.error('根据组织ID获取客户ID失败:', error);
    //   }
    // }

    return {
      canSwitch: false,
      defaultCustomerId: customerId ? customerId.toString() : null, // 转换为字符串
      customerList: []
    };
  };

  /** 初始化客户上下文 */
  const initializeCustomerContext = async () => {
    try {
      // 从存储中恢复状态
      customerStore.initializeFromStorage();

      // 确定访问权限
      const access = await determineCustomerAccess();

      // 设置客户访问权限
      customerStore.setCustomerAccess(access);

      // 如果有默认客户ID且当前没有设置，则设置默认值
      // 注意：对于admin用户，优先使用localStorage中保存的customerId
      if (!customerStore.currentCustomerId && access.defaultCustomerId) {
        customerStore.setCurrentCustomerId(access.defaultCustomerId);
      }

      // 如果可以切换客户，加载客户列表
      if (access.canSwitch) {
        await customerStore.loadCustomerList();
      }

      return true;
    } catch (error) {
      console.error('初始化客户上下文失败:', error);
      throw error;
    }
  };

  /** 验证当前客户访问权限 */
  const validateCurrentCustomerAccess = async () => {
    const currentCustomerId = customerStore.currentCustomerId;
    const user = userInfo.value;

    if (!currentCustomerId) {
      throw new Error('未设置当前客户ID');
    }

    // 对于 admin 用户，允许访问任何客户
    if (isAdmin.value) {
      return true;
    }

    // 对于其他用户，验证是否有权限访问当前客户
    const access = await determineCustomerAccess();
    if (access.defaultCustomerId !== currentCustomerId) {
      throw new Error('无权限访问当前客户');
    }

    return true;
  };

  /** 切换客户（仅超级管理员） */
  const switchCustomer = async (customerId: string) => {
    // 改为字符串类型
    if (!customerStore.canSwitchCustomer) {
      throw new Error('当前用户无权限切换客户');
    }

    await customerStore.switchCustomer(customerId);
  };

  /** 获取当前客户统计信息 */
  const getCurrentCustomerStatistics = async () => {
    const customerId = customerStore.currentCustomerId;
    if (!customerId) {
      throw new Error('未设置当前客户ID');
    }

    // 这里可以调用统计API
    // const { data } = await fetchGetCustomerStatistics(customerId);
    // return data;

    return null;
  };

  /** 重置客户上下文（登出时调用） */
  const resetCustomerContext = () => {
    customerStore.reset();
  };

  /** 检查是否需要选择客户 */
  const needsCustomerSelection = computed(() => {
    return customerStore.canSwitchCustomer && !customerStore.currentCustomerId;
  });

  return {
    // 状态
    currentCustomerId: computed(() => customerStore.currentCustomerId),
    currentCustomer: computed(() => customerStore.currentCustomer),
    canSwitchCustomer: computed(() => customerStore.canSwitchCustomer),
    customerList: computed(() => customerStore.customerList),
    loading: computed(() => customerStore.loading),
    needsCustomerSelection,
    isAdmin,

    // 方法
    initializeCustomerContext,
    validateCurrentCustomerAccess,
    switchCustomer,
    getCurrentCustomerStatistics,
    resetCustomerContext,
    determineCustomerAccess
  };
}

/** 客户上下文验证装饰器 可以用于路由守卫等场景 */
export function withCustomerContext<T extends (...args: any[]) => any>(fn: T): T {
  return (async (...args: any[]) => {
    const { validateCurrentCustomerAccess } = useCustomer();

    try {
      await validateCurrentCustomerAccess();
      return await fn(...args);
    } catch (error) {
      console.error('客户上下文验证失败:', error);
      throw error;
    }
  }) as T;
}
