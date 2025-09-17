<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import type { SelectOption } from 'naive-ui';
import { NSelect } from 'naive-ui';
import { fetchGetAllAvailableCustomers } from '@/service/api/customer/customer';
import { useAuthStore } from '@/store/modules/auth';

interface CustomerOption {
  customerId: string;
  customerName: string;
}

const emit = defineEmits<{
  change: [customerId: string | null, customerName: string | null];
}>();

const authStore = useAuthStore();
const loading = ref(false);
const customers = ref<CustomerOption[]>([]);
const selectedCustomerId = ref<string | null>(null);

// 转换为 NSelect 需要的选项格式
const customerOptions = computed<SelectOption[]>(() => {
  return customers.value.map(customer => ({
    label: customer.customerName,
    value: customer.customerId
  }));
});

// 获取客户列表
const loadCustomers = async () => {
  try {
    loading.value = true;
    const { data } = await fetchGetAllAvailableCustomers();
    // 转换 customerId 为字符串类型避免精度问题
    customers.value = (data || []).map(item => ({
      customerId: item.customerId.toString(),
      customerName: item.customerName
    }));

    // 如果当前用户有 customerId，设置为默认选中
    if (authStore.userInfo.customerId && authStore.userInfo.customerId !== 0) {
      selectedCustomerId.value = authStore.userInfo.customerId.toString();
    }
  } catch (error) {
    console.error('加载客户列表失败:', error);
    customers.value = [];
  } finally {
    loading.value = false;
  }
};

// 处理客户切换
const handleCustomerChange = (customerId: string | null) => {
  const selectedCustomer = customers.value.find(c => c.customerId === customerId);
  const customerName = selectedCustomer?.customerName || null;

  console.log('客户切换:', { customerId, customerName });

  // 发送事件给父组件
  emit('change', customerId, customerName);

  // 这里可以设置全局的 customerId
  // 例如保存到 localStorage 或者 store 中
  if (customerId) {
    localStorage.setItem('selectedCustomerId', customerId);
    localStorage.setItem('selectedCustomerName', customerName || '');
  } else {
    localStorage.removeItem('selectedCustomerId');
    localStorage.removeItem('selectedCustomerName');
  }
};

// 获取当前选中的客户信息
const getCurrentCustomer = () => {
  return customers.value.find(c => c.customerId === selectedCustomerId.value) || null;
};

// 设置选中的客户
const setSelectedCustomer = (customerId: string | null) => {
  selectedCustomerId.value = customerId;
  handleCustomerChange(customerId);
};

// 暴露方法给父组件
defineExpose({
  getCurrentCustomer,
  setSelectedCustomer,
  loadCustomers
});

onMounted(() => {
  loadCustomers();
});
</script>

<template>
  <div class="customer-selector">
    <NSelect
      v-model:value="selectedCustomerId"
      :options="customerOptions"
      :loading="loading"
      placeholder="请选择客户"
      filterable
      clearable
      @update:value="handleCustomerChange"
    >
      <template #empty>
        <div class="py-4 text-center text-gray-500">
          {{ loading ? '加载中...' : '暂无客户数据' }}
        </div>
      </template>
    </NSelect>
  </div>
</template>

<style scoped>
.customer-selector {
  min-width: 200px;
}
</style>
