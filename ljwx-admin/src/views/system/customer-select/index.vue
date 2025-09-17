<template>
  <div class="h-full overflow-hidden">
    <NCard title="客户选择" class="h-full shadow-sm">
      <div class="space-y-6">
        <!-- 当前客户信息 -->
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 class="text-lg font-medium text-blue-900 mb-2">当前选中客户</h3>
          <div v-if="currentCustomer" class="text-blue-700">
            <p><span class="font-medium">客户ID:</span> {{ currentCustomer.customerId }}</p>
            <p><span class="font-medium">客户名称:</span> {{ currentCustomer.customerName }}</p>
          </div>
          <div v-else class="text-gray-500">
            未选择客户
          </div>
        </div>

        <!-- API 请求信息 -->
        <div class="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 class="text-lg font-medium text-green-900 mb-2">API 请求参数</h3>
          <div class="text-green-700">
            <p><span class="font-medium">当前用户角色:</span> {{ userInfo?.userName || 'N/A' }}</p>
            <p><span class="font-medium">用户原始customerId:</span> {{ userInfo?.customerId || 'N/A' }}</p>
            <p><span class="font-medium">选择器选中customerId:</span> {{ customerStore.currentCustomerId || 'N/A' }}</p>
            <p><span class="font-medium">实际使用customerId:</span> {{ getEffectiveCustomerId() }}</p>
            <p class="text-sm text-green-600 mt-2">
              说明：{{ getCustomerIdExplanation() }}
            </p>
          </div>
        </div>

        <!-- 客户选择器 -->
        <div class="space-y-4">
          <h3 class="text-lg font-medium text-gray-900">选择客户</h3>
          <div class="flex items-center space-x-4">
            <label class="text-sm font-medium text-gray-700 whitespace-nowrap">
              客户:
            </label>
            <div class="flex-1 max-w-md">
              <CustomerSelector
                ref="customerSelectorRef"
                @change="handleCustomerChange"
              />
            </div>
          </div>
        </div>

        <!-- 操作说明 */
        <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h3 class="text-lg font-medium text-gray-900 mb-2">功能说明</h3>
          <ul class="text-sm text-gray-600 space-y-1">
            <li>• 管理员可以切换不同的客户进行管理</li>
            <li>• 选择的客户ID会全局生效，影响后续的数据查询</li>
            <li>• 客户信息会保存在本地存储中</li>
            <li>• 普通用户只能看到自己所属的客户</li>
          </ul>
        </div>

        <!-- 操作按钮 */
        <div class="flex space-x-4">
          <NButton type="primary" @click="refreshCustomerList">
            <template #icon>
              <SvgIcon icon="mdi:refresh" />
            </template>
            刷新客户列表
          </NButton>
          
          <NButton @click="clearSelection">
            <template #icon>
              <SvgIcon icon="mdi:close" />
            </template>
            清除选择
          </NButton>

          <NButton type="info" @click="testApiCall">
            <template #icon>
              <SvgIcon icon="mdi:api" />
            </template>
            测试API调用
          </NButton>
        </div>

        <!-- 调试信息 -->
        <div v-if="showDebug" class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 class="text-lg font-medium text-yellow-900 mb-2">调试信息</h3>
          <pre class="text-xs text-yellow-700 overflow-auto">{{ debugInfo }}</pre>
        </div>
      </div>
    </NCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { NCard, NButton } from 'naive-ui';
import SvgIcon from '@/components/custom/svg-icon.vue';
import CustomerSelector from '@/components/business/CustomerSelector.vue';
import { useAuthStore } from '@/store/modules/auth';
import { useCustomerStore } from '@/store/modules/customer';
import { fetchGetAllAvailableCustomers } from '@/service/api/customer/customer';

// Store
const authStore = useAuthStore();
const customerStore = useCustomerStore();

// 组件引用
const customerSelectorRef = ref<InstanceType<typeof CustomerSelector>>();

// 当前选中的客户信息
const currentCustomer = ref<{ customerId: string; customerName: string } | null>(null);

// 用户信息
const userInfo = computed(() => authStore.userInfo);

// 是否显示调试信息
const showDebug = ref(false);

// 调试信息
const debugInfo = computed(() => {
  return {
    currentCustomer: currentCustomer.value,
    localStorage: {
      selectedCustomerId: localStorage.getItem('selectedCustomerId'),
      selectedCustomerName: localStorage.getItem('selectedCustomerName')
    },
    timestamp: new Date().toISOString()
  };
});

// 处理客户切换
const handleCustomerChange = (customerId: string | null, customerName: string | null) => {
  console.log('客户切换事件:', { customerId, customerName });
  
  if (customerId && customerName) {
    currentCustomer.value = { customerId, customerName };
    window.$message?.success(`已切换到客户: ${customerName} (ID: ${customerId})`);
  } else {
    currentCustomer.value = null;
    window.$message?.info('已清除客户选择');
  }
};

// 刷新客户列表
const refreshCustomerList = () => {
  customerSelectorRef.value?.loadCustomers();
  window.$message?.info('正在刷新客户列表...');
};

// 清除选择
const clearSelection = () => {
  customerSelectorRef.value?.setSelectedCustomer(null);
  currentCustomer.value = null;
};

// 获取实际生效的 customerId
const getEffectiveCustomerId = () => {
  const userCustomerId = userInfo.value?.customerId;
  const selectedCustomerId = customerStore.currentCustomerId;
  
  if (userInfo.value?.userName === 'admin' && selectedCustomerId) {
    return selectedCustomerId;
  }
  return userCustomerId || 'N/A';
};

// 获取 customerId 使用说明
const getCustomerIdExplanation = () => {
  if (userInfo.value?.userName === 'admin') {
    if (customerStore.currentCustomerId) {
      return 'Admin用户，使用选择器选中的客户ID';
    } else {
      return 'Admin用户，未选择客户时使用用户原始ID';
    }
  } else {
    return '普通用户，使用用户自身的客户ID';
  }
};

// 测试API调用
const testApiCall = async () => {
  try {
    console.log('测试API调用开始');
    const response = await fetchGetAllAvailableCustomers();
    console.log('API响应:', response);
    window.$message?.success(`API调用成功，返回${response.data?.length || 0}个客户`);
  } catch (error) {
    console.error('API调用失败:', error);
    window.$message?.error('API调用失败');
  }
};

// 开发模式下显示调试信息
if (import.meta.env.DEV) {
  showDebug.value = true;
}
</script>


<style scoped>
/* 可以添加一些自定义样式 */
</style>