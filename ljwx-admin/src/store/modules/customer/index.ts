import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { SetupStoreId } from '@/enum';
import { fetchGetAllAvailableCustomers } from '@/service/api/customer/customer';
import { fetchCustomerIdByOrgId } from '@/service/api';

export interface CustomerInfo {
  id: string; // 改为字符串类型避免精度问题
  name: string;
  code?: string;
  logo?: string;
  status: string;
  description?: string;
}

export interface CustomerAccess {
  canSwitch: boolean;
  defaultCustomerId: string | null; // 改为字符串类型
  customerList: CustomerInfo[];
}

export const useCustomerStore = defineStore(SetupStoreId.Customer, () => {
  // 状态
  const currentCustomerId = ref<string | null>(null); // 改为字符串类型
  const customerList = ref<CustomerInfo[]>([]);
  const canSwitchCustomer = ref(false);
  const recentCustomers = ref<string[]>([]); // 改为字符串数组
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
  const setCurrentCustomerId = (customerId: string | null) => { // 改为字符串类型
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
      localStorage.setItem('currentCustomerId', customerId); // 直接存储字符串
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
      const { data } = await fetchGetAllAvailableCustomers();
      
      // 转换数据格式
      if (data) {
        customerList.value = data.map(item => ({
          id: item.customerId.toString(), // 转换为字符串避免精度问题
          name: item.customerName,
          code: item.customerId.toString(),
          status: 'ACTIVE', // 接口返回的都是可用的客户
          description: `客户ID: ${item.customerId}`
        }));
      }
    } catch (error) {
      console.error('加载客户列表失败:', error);
    } finally {
      loading.value = false;
    }
  };

  const switchCustomer = async (customerId: string) => { // 改为字符串类型
    if (!canSwitchCustomer.value) {
      console.warn('当前用户无权限切换客户');
      return;
    }

    try {
      loading.value = true;
      
      console.log('切换客户: customerId =', customerId);
      
      // 设置新的客户ID
      setCurrentCustomerId(customerId);
      
      // 清理相关缓存
      await clearCustomerRelatedCache();
      
      // 显示成功消息
      const customerName = customerList.value.find(c => c.id === customerId)?.name || customerId;
      window.$message?.success(`已切换到客户: ${customerName}`);
      
      // 延迟一下再重新加载页面，让用户看到成功消息
      setTimeout(() => {
        window.location.reload();
      }, 500);
      
    } catch (error) {
      console.error('切换客户失败:', error);
      window.$message?.error('切换客户失败');
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
      currentCustomerId.value = savedCustomerId; // 直接使用字符串，不进行数字转换
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