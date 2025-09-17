<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { NDropdown, NButton, NInput, NSpace, NSpin, NEmpty, NTag, NAvatar } from 'naive-ui';
import type { DropdownOption } from 'naive-ui';
import { useCustomerStore } from '@/store/modules/customer';
import { useAuthStore } from '@/store/modules/auth';
import { $t } from '@/locales';

defineOptions({
  name: 'CustomerSwitcher'
});

const customerStore = useCustomerStore();
const authStore = useAuthStore();
const searchValue = ref('');
const dropdownVisible = ref(false);

// 计算属性
const currentCustomer = computed(() => customerStore.currentCustomer);
const canSwitch = computed(() => {
  // 只有 admin 用户可以切换客户
  return authStore.userInfo?.userName === 'admin' && customerStore.canSwitchCustomer;
});

// 过滤后的客户列表
const filteredCustomers = computed(() => {
  const list = customerStore.availableCustomers;
  if (!searchValue.value) return list;
  
  return list.filter(customer => 
    customer.name.toLowerCase().includes(searchValue.value.toLowerCase()) ||
    customer.code?.toLowerCase().includes(searchValue.value.toLowerCase())
  );
});

// 最近访问的客户
const recentCustomers = computed(() => customerStore.recentCustomerList);

// 下拉选项
const dropdownOptions = computed((): DropdownOption[] => {
  const options: DropdownOption[] = [];
  
  // 当前客户
  if (currentCustomer.value) {
    options.push({
      key: 'current',
      type: 'group',
      label: '当前客户',
      children: [{
        key: `current-${currentCustomer.value.id}`,
        label: currentCustomer.value.name,
        disabled: true,
        icon: () => h('div', { class: 'i-material-symbols:check-circle text-green-500' })
      }]
    });
  }
  
  // 最近访问
  if (recentCustomers.value.length > 0) {
    options.push({
      key: 'recent',
      type: 'group', 
      label: '最近访问',
      children: recentCustomers.value
        .filter(customer => customer.id !== currentCustomer.value?.id)
        .slice(0, 3)
        .map(customer => ({
          key: `recent-${customer.id}`,
          label: customer.name,
          props: {
            onClick: () => handleCustomerSwitch(customer.id)
          }
        }))
    });
  }
  
  // 所有客户
  if (filteredCustomers.value.length > 0) {
    options.push({
      key: 'all',
      type: 'group',
      label: searchValue.value ? '搜索结果' : '所有客户',
      children: filteredCustomers.value
        .filter(customer => customer.id !== currentCustomer.value?.id)
        .map(customer => ({
          key: `all-${customer.id}`,
          label: customer.name,
          props: {
            onClick: () => handleCustomerSwitch(customer.id)
          }
        }))
    });
  }
  
  return options;
});

// 处理客户切换
const handleCustomerSwitch = async (customerId: number) => {
  try {
    await customerStore.switchCustomer(customerId);
    dropdownVisible.value = false;
    searchValue.value = '';
  } catch (error) {
    console.error('切换客户失败:', error);
    // 这里可以添加错误提示
  }
};

// 处理下拉框显示
const handleDropdownShow = () => {
  dropdownVisible.value = true;
  searchValue.value = '';
  
  // 确保客户列表已加载
  if (customerStore.customerList.length === 0) {
    customerStore.loadCustomerList();
  }
};

// 搜索框聚焦
const handleSearchFocus = () => {
  // 阻止下拉框关闭
};

// 获取客户头像
const getCustomerAvatar = (customer: typeof currentCustomer.value) => {
  if (customer?.logo) return customer.logo;
  return customer?.name?.charAt(0).toUpperCase() || '?';
};

onMounted(() => {
  // 组件挂载时加载客户列表（如果有权限）
  if (canSwitch.value && customerStore.customerList.length === 0) {
    customerStore.loadCustomerList();
  }
});
</script>

<template>
  <!-- 只有超级管理员可以看到客户切换器 -->
  <div v-if="canSwitch" class="customer-switcher">
    <NDropdown
      v-model:show="dropdownVisible"
      :options="dropdownOptions"
      placement="bottom-start"
      trigger="click"
      size="medium"
      :show-arrow="false"
      @show="handleDropdownShow"
    >
      <template #default>
        <NButton
          class="customer-switcher-trigger"
          :loading="customerStore.loading"
          quaternary
          size="medium"
        >
          <template #icon>
            <NAvatar
              v-if="currentCustomer"
              :src="currentCustomer.logo"
              :size="24"
              round
              class="mr-2"
            >
              {{ getCustomerAvatar(currentCustomer) }}
            </NAvatar>
            <div v-else class="i-material-symbols:business text-lg" />
          </template>
          
          <span class="customer-name">
            {{ currentCustomer?.name || '请选择客户' }}
          </span>
          
          <div class="i-material-symbols:expand-more ml-1 transition-transform" :class="{ 'rotate-180': dropdownVisible }" />
        </NButton>
      </template>
      
      <template #header>
        <div class="p-2">
          <NInput
            v-model:value="searchValue"
            size="small"
            placeholder="搜索客户..."
            clearable
            @focus="handleSearchFocus"
          >
            <template #prefix>
              <div class="i-material-symbols:search" />
            </template>
          </NInput>
        </div>
      </template>
      
      <template #empty>
        <div class="p-4">
          <NEmpty
            size="small"
            description="暂无可用客户"
          />
        </div>
      </template>
    </NDropdown>
  </div>
</template>

<style scoped>
.customer-switcher {
  @apply inline-block;
}

.customer-switcher-trigger {
  @apply flex items-center px-3 py-2 rounded-lg transition-all;
  @apply hover:bg-gray-100 dark:hover:bg-gray-800;
  @apply border border-transparent hover:border-gray-200 dark:hover:border-gray-700;
  min-width: 200px;
  justify-content: flex-start;
}

.customer-name {
  @apply font-medium text-gray-700 dark:text-gray-300;
  @apply truncate max-w-40;
}

:deep(.n-dropdown-menu) {
  min-width: 280px;
  max-height: 400px;
  overflow-y: auto;
}

:deep(.n-dropdown-option) {
  @apply py-2 px-3;
}

:deep(.n-dropdown-option:hover) {
  @apply bg-blue-50 dark:bg-blue-900/20;
}

:deep(.n-dropdown-option-body__prefix) {
  @apply mr-3;
}

:deep(.n-dropdown-divider) {
  @apply my-1;
}

/* 加载状态 */
.rotate-180 {
  transform: rotate(180deg);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .customer-switcher-trigger {
    min-width: 150px;
  }
  
  .customer-name {
    @apply max-w-20;
  }
}
</style>