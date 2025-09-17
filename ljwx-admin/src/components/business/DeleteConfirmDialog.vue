<script setup lang="tsx">
import { computed, ref } from 'vue';
import type { Ref } from 'vue';
import { 
  NAlert, 
  NButton, 
  NCard, 
  NDescriptions, 
  NDescriptionsItem, 
  NModal, 
  NSpace, 
  NTable,
  NTag
} from 'naive-ui';

interface Props {
  visible: boolean;
  preCheckData?: Api.SystemManage.DepartmentDeletePreCheck;
  loading?: boolean;
}

interface Emits {
  (e: 'update:visible', visible: boolean): void;
  (e: 'confirm'): void;
  (e: 'cancel'): void;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  loading: false
});

const emit = defineEmits<Emits>();

const modalVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => {
    emit('update:visible', value);
  }
});

// 部门表格列定义
const departmentColumns = [
  {
    key: 'orgName',
    title: '部门名称',
    width: 150
  },
  {
    key: 'level',
    title: '层级',
    width: 80
  },
  {
    key: 'userCount',
    title: '用户数量',
    width: 100,
    render: (row: any) => (
      <NTag type={row.userCount > 0 ? 'error' : 'success'} size="small">
        {row.userCount}
      </NTag>
    )
  },
  {
    key: 'deviceCount',
    title: '设备数量',
    width: 100,
    render: (row: any) => (
      <NTag type={row.deviceCount > 0 ? 'warning' : 'success'} size="small">
        {row.deviceCount}
      </NTag>
    )
  }
];

// 用户表格列定义
const userColumns = [
  {
    key: 'realName',
    title: '姓名',
    width: 120
  },
  {
    key: 'userName',
    title: '用户名',
    width: 120
  },
  {
    key: 'orgName',
    title: '所属部门',
    width: 150
  },
  {
    key: 'hasDevice',
    title: '绑定设备',
    width: 100,
    render: (row: any) => (
      <NTag type={row.hasDevice ? 'warning' : 'default'} size="small">
        {row.hasDevice ? '是' : '否'}
      </NTag>
    )
  },
  {
    key: 'deviceSn',
    title: '设备编号',
    width: 150,
    render: (row: any) => row.deviceSn || '-'
  }
];

// 设备表格列定义
const deviceColumns = [
  {
    key: 'deviceSn',
    title: '设备编号',
    width: 150
  },
  {
    key: 'deviceType',
    title: '设备类型',
    width: 120
  },
  {
    key: 'boundUserName',
    title: '绑定用户',
    width: 120,
    render: (row: any) => row.boundUserName || '-'
  },
  {
    key: 'orgName',
    title: '所属部门',
    width: 150,
    render: (row: any) => row.orgName || '-'
  }
];

const handleConfirm = () => {
  emit('confirm');
};

const handleCancel = () => {
  emit('cancel');
  modalVisible.value = false;
};

const alertType = computed(() => {
  if (!props.preCheckData) return 'info';
  return props.preCheckData.canSafeDelete ? 'warning' : 'error';
});

const alertTitle = computed(() => {
  if (!props.preCheckData) return '正在检查删除影响...';
  return props.preCheckData.canSafeDelete ? '安全删除确认' : '级联删除风险提醒';
});
</script>

<template>
  <NModal 
    v-model:show="modalVisible" 
    preset="card" 
    :title="alertTitle"
    class="max-w-90vw w-1200px max-h-80vh"
    :mask-closable="false"
    :close-on-esc="false"
  >
    <div v-if="!preCheckData || loading" class="text-center py-8">
      <div class="text-gray-500">正在分析删除影响...</div>
    </div>
    
    <div v-else class="space-y-4 max-h-60vh overflow-y-auto">
      <!-- 警告提示 -->
      <NAlert :type="alertType" :title="alertTitle" show-icon>
        <div class="mt-2">
          <p class="text-sm">{{ preCheckData.summary.warningMessage }}</p>
          <p v-if="!preCheckData.canSafeDelete" class="text-red-600 font-medium mt-2">
            ⚠️ 此操作将永久删除相关数据，且不可恢复！请谨慎操作。
          </p>
        </div>
      </NAlert>

      <!-- 影响统计 -->
      <NCard title="📊 影响范围统计" size="small">
        <NDescriptions :column="2" label-placement="left" size="small">
          <NDescriptionsItem label="将删除部门">
            <NTag type="error" size="small">{{ preCheckData.summary.totalDepartments }} 个</NTag>
          </NDescriptionsItem>
          <NDescriptionsItem label="将删除用户">
            <NTag type="error" size="small">{{ preCheckData.summary.totalUsers }} 个</NTag>
          </NDescriptionsItem>
          <NDescriptionsItem label="将释放设备">
            <NTag type="warning" size="small">{{ preCheckData.summary.totalDevices }} 个</NTag>
          </NDescriptionsItem>
          <NDescriptionsItem label="绑定设备用户">
            <NTag type="warning" size="small">{{ preCheckData.summary.usersWithDevices }} 个</NTag>
          </NDescriptionsItem>
        </NDescriptions>
      </NCard>

      <!-- 部门详情 -->
      <NCard v-if="preCheckData.departmentsToDelete.length > 0" title="🏢 将要删除的部门" size="small">
        <NTable 
          :data="preCheckData.departmentsToDelete"
          :columns="departmentColumns"
          size="small"
          max-height="200"
        />
      </NCard>

      <!-- 用户详情 -->
      <NCard v-if="preCheckData.usersToDelete.length > 0" title="👥 将要删除的用户" size="small">
        <NTable 
          :data="preCheckData.usersToDelete"
          :columns="userColumns"
          size="small"
          max-height="200"
        />
      </NCard>

      <!-- 设备详情 -->
      <NCard v-if="preCheckData.devicesToRelease.length > 0" title="📱 将要释放的设备" size="small">
        <NTable 
          :data="preCheckData.devicesToRelease"
          :columns="deviceColumns"
          size="small"
          max-height="200"
        />
      </NCard>
    </div>

    <template #footer>
      <div class="flex justify-end space-x-3">
        <NButton @click="handleCancel">取消</NButton>
        <NButton 
          v-if="preCheckData && preCheckData.canSafeDelete"
          type="warning"
          @click="handleConfirm"
        >
          确认删除
        </NButton>
        <NButton 
          v-else-if="preCheckData && !preCheckData.canSafeDelete"
          type="error"
          @click="handleConfirm"
        >
          强制级联删除
        </NButton>
      </div>
    </template>
  </NModal>
</template>