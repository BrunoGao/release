import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { SetupStoreId } from '@/enum';
import { fetchGetCustomerList, fetchCustomerIdByOrgId } from '@/service/api';

export interface CustomerInfo {
  id: number;
  name: string;
  code?: string;
  logo?: string;
  status: string;
  description?: string;
}

export interface CustomerAccess {
  canSwitch: boolean;
  defaultCustomerId: number | null;
  customerList: CustomerInfo[];
}

export const useCustomerStore = defineStore(SetupStoreId.Customer, () => {
  // 状态
  const currentCustomerId = ref<number | null>(null);
  const customerList = ref<CustomerInfo[]>([]);
  const canSwitchCustomer = ref(false);
  const recentCustomers = ref<number[]>([]);
  const loading = ref(false);

  // 计算属性
  const currentCustomer = computed(() => {
    if (!currentCustomerId.value) return null;
    return customerList.value.find(c => c.id === currentCustomerId.value) || null;
  });

  const availableCustomers = computed(() => {
    return customerList.value.filter(c => c.status === 'ACTIVE');
  });

  const recentCustomerList = computed(() => {
    return recentCustomers.value
      .map(id => customerList.value.find(c => c.id === id))
      .filter(Boolean) as CustomerInfo[];
  });

  // Actions
  const setCurrentCustomerId = (customerId: number | null) => {
    currentCustomerId.value = customerId;
    
    // 更新最近访问记录
    if (customerId && !recentCustomers.value.includes(customerId)) {
      recentCustomers.value.unshift(customerId);
      if (recentCustomers.value.length > 5) {
        recentCustomers.value = recentCustomers.value.slice(0, 5);
      }
    }
    
    // 持久化到 localStorage
    if (customerId) {
      localStorage.setItem('currentCustomerId', customerId.toString());
      localStorage.setItem('recentCustomers', JSON.stringify(recentCustomers.value));
    } else {
      localStorage.removeItem('currentCustomerId');
    }
  };

  const setCustomerAccess = (access: CustomerAccess) => {
    canSwitchCustomer.value = access.canSwitch;
    customerList.value = access.customerList;
    
    if (access.defaultCustomerId) {
      setCurrentCustomerId(access.defaultCustomerId);
    }
  };

  const loadCustomerList = async () => {
    if (!canSwitchCustomer.value) return;
    
    try {
      loading.value = true;
      const { data } = await fetchGetCustomerList({ 
        page: 1, 
        pageSize: 100,
        status: 'ACTIVE'
      });
      
      if (data?.records) {
        customerList.value = data.records;
      }
    } catch (error) {
      console.error('加载客户列表失败:', error);
    } finally {
      loading.value = false;
    }
  };

  const switchCustomer = async (customerId: number) => {
    if (!canSwitchCustomer.value) {
      console.warn('当前用户无权限切换客户');
      return;
    }

    try {
      loading.value = true;
      
      // 设置新的客户ID
      setCurrentCustomerId(customerId);
      
      // 清理相关缓存
      await clearCustomerRelatedCache();
      
      // 重新加载页面数据
      window.location.reload();
      
    } catch (error) {
      console.error('切换客户失败:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  };

  const getCustomerIdByOrgId = async (orgId: number): Promise<number> => {
    try {
      const { data } = await fetchCustomerIdByOrgId(orgId);
      return data.customerId;
    } catch (error) {
      console.error('根据组织ID获取客户ID失败:', error);
      throw error;
    }
  };

  const clearCustomerRelatedCache = async () => {
    // 清理所有与客户相关的缓存数据
    const cacheKeys = [
      'userOptions',
      'orgUnitsTree',
      'deviceOptions',
      'healthData',
      'messageCache'
    ];
    
    cacheKeys.forEach(key => {
      localStorage.removeItem(key);
      sessionStorage.removeItem(key);
    });
  };

  const initializeFromStorage = () => {
    // 从 localStorage 恢复状态
    const savedCustomerId = localStorage.getItem('currentCustomerId');
    const savedRecentCustomers = localStorage.getItem('recentCustomers');
    
    if (savedCustomerId) {
      currentCustomerId.value = parseInt(savedCustomerId);
    }
    
    if (savedRecentCustomers) {
      try {
        recentCustomers.value = JSON.parse(savedRecentCustomers);
      } catch (error) {
        console.warn('解析最近客户列表失败:', error);
        recentCustomers.value = [];
      }
    }
  };

  const reset = () => {
    currentCustomerId.value = null;
    customerList.value = [];
    canSwitchCustomer.value = false;
    recentCustomers.value = [];
    loading.value = false;
    
    // 清理存储
    localStorage.removeItem('currentCustomerId');
    localStorage.removeItem('recentCustomers');
  };

  return {
    // 状态
    currentCustomerId,
    customerList,
    canSwitchCustomer,
    recentCustomers,
    loading,

    // 计算属性
    currentCustomer,
    availableCustomers,
    recentCustomerList,

    // 方法
    setCurrentCustomerId,
    setCustomerAccess,
    loadCustomerList,
    switchCustomer,
    getCustomerIdByOrgId,
    clearCustomerRelatedCache,
    initializeFromStorage,
    reset
  };
});

export type CustomerStore = ReturnType<typeof useCustomerStore>;