<script setup lang="ts">
import { computed, onMounted, ref, watchEffect } from 'vue';
import { NButton, NDropdown, NEmpty, NInput } from 'naive-ui';
import type { DropdownOption } from 'naive-ui';
import SvgIcon from '@/components/custom/svg-icon.vue';
import { useAuthStore } from '@/store/modules/auth';
import { useCustomerStore } from '@/store/modules/customer';

defineOptions({
  name: 'TenantInfo'
});

const authStore = useAuthStore();
const customerStore = useCustomerStore();
const searchValue = ref('');
const showDropdown = ref(false);

// 当前客户信息
const currentCustomer = computed(() => customerStore.currentCustomer);

// 是否显示租户信息（只有admin用户才显示）
const showTenantInfo = computed(() => {
  return authStore.userInfo?.userName === 'admin' && customerStore.canSwitchCustomer;
});

// 过滤后的客户列表
const filteredCustomers = computed(() => {
  const list = customerStore.availableCustomers;
  if (!searchValue.value) return list;

  return list.filter(
    customer =>
      customer.name.toLowerCase().includes(searchValue.value.toLowerCase()) || customer.code?.toLowerCase().includes(searchValue.value.toLowerCase())
  );
});

// 最近访问的客户
const recentCustomers = computed(() => customerStore.recentCustomerList);

// 下拉选项
const dropdownOptions = computed((): DropdownOption[] => {
  const options: DropdownOption[] = [];

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
          label: customer.name
        }))
    });
  }

  // 所有客户
  if (filteredCustomers.value.length > 0) {
    options.push({
      key: 'all',
      type: 'group',
      label: searchValue.value ? '搜索结果' : '所有租户',
      children: filteredCustomers.value
        .filter(customer => customer.id !== currentCustomer.value?.id)
        .map(customer => ({
          key: `all-${customer.id}`,
          label: customer.name
        }))
    });
  }

  return options;
});

// 处理客户切换
const handleCustomerSwitch = async (customerId: string) => {
  try {
    console.log('开始切换租户:', customerId);
    await customerStore.switchCustomer(customerId);
    showDropdown.value = false;
    searchValue.value = '';
    console.log('租户切换成功');
  } catch (error) {
    console.error('切换租户失败:', error);
    window.$message?.error('切换租户失败');
  }
};

// 处理下拉选择
const handleSelect = (key: string) => {
  console.log('租户选择:', key);

  // 解析客户ID
  const match = key.match(/(recent|all)-(.+)/);
  if (match) {
    const customerId = match[2];
    handleCustomerSwitch(customerId);
  }
};

// 处理下拉框显示
const handleDropdownShow = () => {
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

// 调试信息
watchEffect(() => {
  console.log('[TenantInfo] 状态更新:', {
    showTenantInfo: showTenantInfo.value,
    currentCustomer: currentCustomer.value,
    currentCustomerId: customerStore.currentCustomerId,
    userName: authStore.userInfo?.userName,
    canSwitch: customerStore.canSwitchCustomer
  });
});

onMounted(() => {
  // 组件挂载时加载客户列表（如果有权限）
  if (showTenantInfo.value && customerStore.customerList.length === 0) {
    console.log('[TenantInfo] 开始加载客户列表');
    customerStore.loadCustomerList();
  }
});
</script>

<template>
  <div v-if="showTenantInfo" class="tenant-info">
    <!-- 统一的下拉菜单，根据是否选择客户显示不同的触发器 -->
    <NDropdown
      v-model:show="showDropdown"
      :options="dropdownOptions"
      placement="bottom-start"
      trigger="click"
      size="medium"
      :show-arrow="false"
      @show="handleDropdownShow"
      @select="handleSelect"
    >
      <template #default>
        <!-- 未选择客户时显示选择按钮 -->
        <NButton v-if="!currentCustomer" quaternary type="primary">
          <template #icon>
            <SvgIcon icon="mdi:domain" />
          </template>
          请选择租户
          <template #suffix>
            <SvgIcon icon="mdi:chevron-down" />
          </template>
        </NButton>

        <!-- 已选择客户时显示租户信息 -->
        <div v-else class="tenant-badge clickable">
          <SvgIcon icon="mdi:domain" class="text-blue-500" />
          <span class="tenant-text">
            <span class="label">当前租户:</span>
            <span class="tenant-name">{{ currentCustomer.name }}</span>
            <span v-if="currentCustomer.id" class="tenant-id">(ID: {{ currentCustomer.id }})</span>
          </span>
          <SvgIcon icon="mdi:chevron-down" class="ml-2 text-gray-400" />
        </div>
      </template>

      <template #header>
        <div class="p-2">
          <NInput v-model:value="searchValue" size="small" placeholder="搜索租户..." clearable @focus="handleSearchFocus">
            <template #prefix>
              <SvgIcon icon="mdi:magnify" />
            </template>
          </NInput>
        </div>
      </template>

      <template #empty>
        <div class="p-4">
          <NEmpty size="small" description="暂无可用租户" />
        </div>
      </template>
    </NDropdown>
  </div>
</template>

<style scoped>
.tenant-info {
  @apply flex items-center;
}

.tenant-badge {
  @apply flex items-center px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-700;
  @apply text-sm font-medium transition-all;
}

.tenant-badge.clickable {
  @apply cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-800/30 hover:border-blue-300 dark:hover:border-blue-600;
}

.tenant-text {
  @apply ml-2 flex items-center space-x-1;
}

.label {
  @apply text-gray-600 dark:text-gray-400;
}

.tenant-name {
  @apply text-blue-700 dark:text-blue-300 font-semibold;
}

.tenant-id {
  @apply text-gray-500 dark:text-gray-400 text-xs;
}

/* 下拉菜单样式 */
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

/* 响应式设计 */
@media (max-width: 768px) {
  .tenant-badge {
    @apply px-2 py-1 text-xs;
  }

  .tenant-id {
    @apply hidden;
  }
}
</style>
