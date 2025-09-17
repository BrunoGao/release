<script setup lang="ts">
import { computed } from 'vue';
import { NButton, NDatePicker, NForm, NFormItem, NGrid, NGridItem, NInput, NSelect, NSpace } from 'naive-ui';
import type { SelectOption } from 'naive-ui';
import { useDict } from '@/hooks/business/dict';
import { $t } from '@/locales';

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

interface Props {
  model: Api.Health.DeviceMessageV2SearchParams;
  deviceOptions?: SelectOption[];
  customerId?: number;
  orgUnitsTree?: Api.SystemManage.OrgUnitsTree[];
  userOptions?: SelectOption[];
}

const emit = defineEmits<Emits>();
const props = defineProps<Props>();

const { dictOptions } = useDict();

// V2消息类型选项
const messageTypeV2Options = [
  { label: '紧急消息', value: 'EMERGENCY' },
  { label: '告警消息', value: 'ALERT' },
  { label: '警告消息', value: 'WARNING' },
  { label: '通知消息', value: 'NOTIFICATION' },
  { label: '信息消息', value: 'INFO' }
];

// V2消息状态选项
const messageStatusV2Options = [
  { label: '草稿', value: 'DRAFT' },
  { label: '待发送', value: 'PENDING' },
  { label: '已发送', value: 'SENT' },
  { label: '已送达', value: 'DELIVERED' },
  { label: '已确认', value: 'ACKNOWLEDGED' },
  { label: '发送失败', value: 'FAILED' },
  { label: '已过期', value: 'EXPIRED' }
];

// V2发送者类型选项
const senderTypeV2Options = [
  { label: '系统', value: 'SYSTEM' },
  { label: '用户', value: 'USER' },
  { label: '设备', value: 'DEVICE' },
  { label: 'API', value: 'API' }
];

// V2接收者类型选项
const receiverTypeV2Options = [
  { label: '用户', value: 'USER' },
  { label: '设备', value: 'DEVICE' },
  { label: '群组', value: 'GROUP' },
  { label: '广播', value: 'BROADCAST' }
];

// V2紧急程度选项
const urgencyV2Options = [
  { label: '低', value: 'LOW' },
  { label: '中', value: 'MEDIUM' },
  { label: '高', value: 'HIGH' },
  { label: '紧急', value: 'CRITICAL' }
];

// 组织树选项
const orgOptions = computed(() => {
  const options = [{ label: '全部部门', value: null }];
  if (props.orgUnitsTree) {
    const transformTree = (tree: Api.SystemManage.OrgUnitsTree[]): SelectOption[] => {
      return tree.map(item => ({
        label: item.orgName,
        value: item.id,
        children: item.children ? transformTree(item.children) : undefined
      }));
    };
    options.push(...transformTree(props.orgUnitsTree));
  }
  return options;
});

// 用户选项
const allUserOptions = computed(() => {
  const options = [{ label: '全部用户', value: null }];
  if (props.userOptions) {
    options.push(...props.userOptions);
  }
  return options;
});

// 重置搜索
function handleReset() {
  emit('reset');
}

// 执行搜索
function handleSearch() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NForm :model="model" label-placement="left" :label-width="80">
      <NGrid :cols="24" :x-gap="18">
        <!-- 基础搜索条件 -->
        <NFormItem :span="6" label="消息ID">
          <NInput v-model:value="model.messageId" placeholder="请输入消息ID" clearable />
        </NFormItem>

        <NFormItem :span="6" label="标题关键词">
          <NInput v-model:value="model.keyword" placeholder="请输入标题关键词" clearable />
        </NFormItem>

        <NFormItem :span="6" label="部门">
          <NSelect v-model:value="model.orgId" :options="orgOptions" placeholder="请选择部门" clearable filterable />
        </NFormItem>

        <NFormItem :span="6" label="用户">
          <NSelect v-model:value="model.userId" :options="allUserOptions" placeholder="请选择用户" clearable filterable />
        </NFormItem>

        <!-- 消息属性条件 -->
        <NFormItem :span="6" label="消息类型">
          <NSelect v-model:value="model.messageType" :options="messageTypeV2Options" placeholder="请选择消息类型" clearable />
        </NFormItem>

        <NFormItem :span="6" label="消息状态">
          <NSelect v-model:value="model.messageStatus" :options="messageStatusV2Options" placeholder="请选择消息状态" clearable />
        </NFormItem>

        <NFormItem :span="6" label="紧急程度">
          <NSelect v-model:value="model.urgency" :options="urgencyV2Options" placeholder="请选择紧急程度" clearable />
        </NFormItem>

        <NFormItem :span="6" label="发送者类型">
          <NSelect v-model:value="model.senderType" :options="senderTypeV2Options" placeholder="请选择发送者类型" clearable />
        </NFormItem>

        <!-- 设备相关条件 -->
        <NFormItem :span="6" label="设备序列号">
          <NInput v-model:value="model.deviceSn" placeholder="请输入设备序列号" clearable />
        </NFormItem>

        <NFormItem :span="6" label="接收者类型">
          <NSelect v-model:value="model.receiverType" :options="receiverTypeV2Options" placeholder="请选择接收者类型" clearable />
        </NFormItem>

        <!-- 时间范围条件 -->
        <NFormItem :span="6" label="创建时间">
          <NDatePicker
            v-model:value="model.startTime"
            type="datetime"
            placeholder="开始时间"
            clearable
            format="yyyy-MM-dd HH:mm:ss"
            style="width: 100%"
          />
        </NFormItem>

        <NFormItem :span="6" label="">
          <NDatePicker
            v-model:value="model.endTime"
            type="datetime"
            placeholder="结束时间"
            clearable
            format="yyyy-MM-dd HH:mm:ss"
            style="width: 100%"
          />
        </NFormItem>

        <!-- 操作按钮 -->
        <NFormItem :span="24" class="flex justify-end">
          <NSpace>
            <NButton @click="handleReset">
              {{ $t('common.reset') }}
            </NButton>
            <NButton type="primary" ghost @click="handleSearch">
              {{ $t('common.search') }}
            </NButton>
          </NSpace>
        </NFormItem>
      </NGrid>
    </NForm>
  </NCard>
</template>

<style scoped>
.card-wrapper {
  transition: all 0.3s ease;
}

.card-wrapper:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.n-form-item-label__text) {
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

:deep(.n-input__input) {
  font-size: 13px;
}

:deep(.n-select .n-base-selection-input__content) {
  font-size: 13px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  :deep(.n-grid-item) {
    grid-column: span 8 !important;
  }
}

@media (max-width: 768px) {
  :deep(.n-grid-item) {
    grid-column: span 12 !important;
  }
}

@media (max-width: 480px) {
  :deep(.n-grid-item) {
    grid-column: span 24 !important;
  }
}
</style>
