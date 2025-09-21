<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import type { FormInst, FormRules, SelectOption } from 'naive-ui';
import {
  NAlert,
  NButton,
  NCard,
  NDatePicker,
  NDrawer,
  NDrawerContent,
  NDynamicTags,
  NForm,
  NFormItem,
  NGrid,
  NGridItem,
  NInput,
  NSelect,
  NSpace,
  NSwitch
} from 'naive-ui';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchCreateDeviceMessageV2, fetchUpdateDeviceMessageV2 } from '@/service/api/health/device-message-v2';

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Health.DeviceMessageV2Detail | null;
  visible: boolean;
  deviceOptions?: SelectOption[];
  customerId?: number;
  orgUnitsTree?: Api.SystemManage.OrgUnitsTree[];
  userOptions?: SelectOption[];
}

interface Emits {
  (e: 'submitted'): void;
  (e: 'update:visible', visible: boolean): void;
  (e: 'update-user-options', options: SelectOption[]): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const visible = computed({
  get() {
    return props.visible;
  },
  set(visible) {
    emit('update:visible', visible);
  }
});

const { formRef, validate, restoreValidation } = useNaiveForm();
const { defaultRequiredRule } = useFormRules();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: '新增V2消息',
    edit: '编辑V2消息'
  };
  return titles[props.operateType];
});

type Model = Pick<
  Api.Health.DeviceMessageV2Create,
  'title' | 'message' | 'messageType' | 'senderType' | 'receiverType' | 'urgency' | 'customerId' | 'orgId' | 'userId' | 'deviceSn' | 'expiresAt'
> & {
  targets: Array<{
    targetId: string;
    targetType: 'DEVICE' | 'USER' | 'GROUP';
    channel: 'DEVICE' | 'SMS' | 'EMAIL' | 'PUSH' | 'WECHAT';
  }>;
  enableExpiration: boolean;
};

const model: Model = reactive({
  title: '',
  message: '',
  messageType: 'NOTIFICATION',
  senderType: 'SYSTEM',
  receiverType: 'USER',
  urgency: 'MEDIUM',
  customerId: props.customerId,
  orgId: null,
  userId: null,
  deviceSn: null,
  expiresAt: null,
  targets: [],
  enableExpiration: false
});

const rules: FormRules = {
  title: defaultRequiredRule,
  message: defaultRequiredRule,
  messageType: defaultRequiredRule,
  senderType: defaultRequiredRule,
  receiverType: defaultRequiredRule,
  urgency: defaultRequiredRule
};

// 选项定义
const messageTypeOptions = [
  { label: '紧急消息', value: 'EMERGENCY' },
  { label: '告警消息', value: 'ALERT' },
  { label: '警告消息', value: 'WARNING' },
  { label: '通知消息', value: 'NOTIFICATION' },
  { label: '信息消息', value: 'INFO' }
];

const senderTypeOptions = [
  { label: '系统', value: 'SYSTEM' },
  { label: '用户', value: 'USER' },
  { label: '设备', value: 'DEVICE' },
  { label: 'API', value: 'API' }
];

const receiverTypeOptions = [
  { label: '用户', value: 'USER' },
  { label: '设备', value: 'DEVICE' },
  { label: '群组', value: 'GROUP' },
  { label: '广播', value: 'BROADCAST' }
];

const urgencyOptions = [
  { label: '低', value: 'LOW' },
  { label: '中', value: 'MEDIUM' },
  { label: '高', value: 'HIGH' },
  { label: '紧急', value: 'CRITICAL' }
];

const targetTypeOptions = [
  { label: '设备', value: 'DEVICE' },
  { label: '用户', value: 'USER' },
  { label: '群组', value: 'GROUP' }
];

const channelOptions = [
  { label: '设备', value: 'DEVICE' },
  { label: '短信', value: 'SMS' },
  { label: '邮件', value: 'EMAIL' },
  { label: '推送', value: 'PUSH' },
  { label: '微信', value: 'WECHAT' }
];

// 组织树选项
const orgOptions = computed(() => {
  const options: SelectOption[] = [{ label: '请选择部门', value: null }];
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
  const options: SelectOption[] = [{ label: '请选择用户', value: null }];
  if (props.userOptions) {
    options.push(...props.userOptions);
  }
  return options;
});

// 新增分发目标
function addTarget() {
  model.targets.push({
    targetId: '',
    targetType: 'DEVICE',
    channel: 'DEVICE'
  });
}

// 移除分发目标
function removeTarget(index: number) {
  model.targets.splice(index, 1);
}

// 关闭抽屉
function closeDrawer() {
  visible.value = false;
}

// 处理初始化
function handleInitModel() {
  Object.assign(model, {
    title: '',
    message: '',
    messageType: 'NOTIFICATION',
    senderType: 'SYSTEM',
    receiverType: 'USER',
    urgency: 'MEDIUM',
    customerId: props.customerId,
    orgId: null,
    userId: null,
    deviceSn: null,
    expiresAt: null,
    targets: [],
    enableExpiration: false
  });
}

// 处理更新
function handleUpdateModelByModalType() {
  const handlers: Record<NaiveUI.TableOperateType, () => void> = {
    add: () => {
      handleInitModel();
    },
    edit: () => {
      if (props.rowData) {
        Object.assign(model, {
          title: props.rowData.title,
          message: props.rowData.message,
          messageType: props.rowData.messageType,
          senderType: props.rowData.senderType,
          receiverType: props.rowData.receiverType,
          urgency: props.rowData.urgency,
          customerId: props.rowData.customerId,
          orgId: props.rowData.orgId,
          userId: props.rowData.userId,
          deviceSn: props.rowData.deviceSn,
          expiresAt: props.rowData.expiresAt,
          targets:
            props.rowData.details?.map(detail => ({
              targetId: detail.targetId,
              targetType: detail.targetType,
              channel: detail.channel
            })) || [],
          enableExpiration: Boolean(props.rowData.expiresAt)
        });
      }
    }
  };
  handlers[props.operateType]();
}

// 提交表单
async function handleSubmit() {
  await validate();

  const submitData: Api.Health.DeviceMessageV2Create = {
    title: model.title,
    message: model.message,
    messageType: model.messageType,
    senderType: model.senderType,
    receiverType: model.receiverType,
    urgency: model.urgency,
    customerId: model.customerId!,
    orgId: model.orgId || undefined,
    userId: model.userId || undefined,
    deviceSn: model.deviceSn || undefined,
    expiresAt: model.enableExpiration ? model.expiresAt : undefined,
    targets: model.targets.length > 0 ? model.targets : undefined
  };

  const handlers: Record<NaiveUI.TableOperateType, () => Promise<void>> = {
    add: async () => {
      const { error } = await fetchCreateDeviceMessageV2(submitData);
      if (!error) {
        window.$message?.success('新增成功');
      }
    },
    edit: async () => {
      if (props.rowData) {
        const { error } = await fetchUpdateDeviceMessageV2(props.rowData.id, submitData);
        if (!error) {
          window.$message?.success('更新成功');
        }
      }
    }
  };

  try {
    await handlers[props.operateType]();
    emit('submitted');
    closeDrawer();
  } catch (error) {
    console.error('提交失败:', error);
  }
}

watch(visible, () => {
  if (visible.value) {
    handleUpdateModelByModalType();
    restoreValidation();
  }
});

// 监听过期时间开关
watch(
  () => model.enableExpiration,
  enabled => {
    if (!enabled) {
      model.expiresAt = null;
    }
  }
);
</script>

<template>
  <NDrawer v-model:show="visible" :width="800" :closable="false" class="enhanced-drawer device-theme">
    <NDrawerContent :title="title" closable @close="closeDrawer" class="enhanced-drawer device-theme">
      <NForm ref="formRef" :model="model" :rules="rules" label-placement="left" :label-width="120">
        <div class="space-y-16px">
          <!-- 基本信息 -->
          <NCard title="基本信息" size="small">
            <NGrid :cols="2" :x-gap="16" :y-gap="16">
              <NGridItem>
                <NFormItem label="消息标题" path="title">
                  <NInput v-model:value="model.title" placeholder="请输入消息标题" maxlength="255" show-count />
                </NFormItem>
              </NGridItem>

              <NGridItem>
                <NFormItem label="消息类型" path="messageType">
                  <NSelect v-model:value="model.messageType" :options="messageTypeOptions" placeholder="请选择消息类型" />
                </NFormItem>
              </NGridItem>

              <NGridItem>
                <NFormItem label="紧急程度" path="urgency">
                  <NSelect v-model:value="model.urgency" :options="urgencyOptions" placeholder="请选择紧急程度" />
                </NFormItem>
              </NGridItem>

              <NGridItem>
                <NFormItem label="发送者类型" path="senderType">
                  <NSelect v-model:value="model.senderType" :options="senderTypeOptions" placeholder="请选择发送者类型" />
                </NFormItem>
              </NGridItem>

              <NGridItem :span="2">
                <NFormItem label="消息内容" path="message">
                  <NInput v-model:value="model.message" type="textarea" placeholder="请输入消息内容" :rows="4" maxlength="2000" show-count />
                </NFormItem>
              </NGridItem>
            </NGrid>
          </NCard>

          <!-- 接收者信息 -->
          <NCard title="接收者信息" size="small">
            <NGrid :cols="2" :x-gap="16" :y-gap="16">
              <NGridItem>
                <NFormItem label="接收者类型">
                  <NSelect v-model:value="model.receiverType" :options="receiverTypeOptions" placeholder="请选择接收者类型" />
                </NFormItem>
              </NGridItem>

              <NGridItem>
                <NFormItem label="所属部门">
                  <NSelect v-model:value="model.orgId" :options="orgOptions" placeholder="请选择部门" filterable clearable />
                </NFormItem>
              </NGridItem>

              <NGridItem v-if="model.receiverType === 'USER'">
                <NFormItem label="目标用户">
                  <NSelect v-model:value="model.userId" :options="allUserOptions" placeholder="请选择用户" filterable clearable />
                </NFormItem>
              </NGridItem>

              <NGridItem v-if="model.receiverType === 'DEVICE'">
                <NFormItem label="设备序列号">
                  <NInput v-model:value="model.deviceSn" placeholder="请输入设备序列号" />
                </NFormItem>
              </NGridItem>
            </NGrid>
          </NCard>

          <!-- 分发目标 -->
          <NCard title="分发目标" size="small">
            <template #header-extra>
              <NButton type="primary" dashed size="small" @click="addTarget">添加目标</NButton>
            </template>

            <div v-if="model.targets.length === 0" class="py-20 text-center text-gray-400">
              <div>暂未添加分发目标</div>
              <div class="mt-4 text-xs">系统将根据接收者类型自动分发</div>
            </div>

            <div v-else class="space-y-12px">
              <div v-for="(target, index) in model.targets" :key="index" class="flex items-center gap-12px border border-gray-200 rounded-lg p-12px">
                <NSelect v-model:value="target.targetType" :options="targetTypeOptions" placeholder="目标类型" style="width: 100px" />

                <NInput v-model:value="target.targetId" placeholder="目标ID（设备SN、用户ID等）" style="flex: 1" />

                <NSelect v-model:value="target.channel" :options="channelOptions" placeholder="分发渠道" style="width: 100px" />

                <NButton type="error" quaternary size="small" @click="removeTarget(index)">移除</NButton>
              </div>
            </div>
          </NCard>

          <!-- 高级选项 -->
          <NCard title="高级选项" size="small">
            <NGrid :cols="2" :x-gap="16" :y-gap="16">
              <NGridItem>
                <NFormItem label="启用过期时间">
                  <NSwitch v-model:value="model.enableExpiration" />
                </NFormItem>
              </NGridItem>

              <NGridItem v-if="model.enableExpiration">
                <NFormItem label="过期时间">
                  <NDatePicker
                    v-model:value="model.expiresAt"
                    type="datetime"
                    placeholder="请选择过期时间"
                    format="yyyy-MM-dd HH:mm:ss"
                    style="width: 100%"
                  />
                </NFormItem>
              </NGridItem>
            </NGrid>

            <NAlert type="info" show-icon class="mt-16px">
              <div class="text-sm space-y-4px">
                <div>• 如果未设置分发目标，系统会根据接收者类型自动确定分发范围</div>
                <div>• 紧急和高优先级消息会使用更快的分发渠道</div>
                <div>• 设置过期时间后，过期的消息将不会继续分发</div>
              </div>
            </NAlert>
          </NCard>
        </div>
      </NForm>

      <template #footer>
        <div class="flex justify-end gap-8px">
          <NButton @click="closeDrawer">取消</NButton>
          <NButton type="primary" @click="handleSubmit">
            {{ props.operateType === 'add' ? '新增' : '更新' }}
          </NButton>
        </div>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped>
:deep(.n-form-item-label__text) {
  font-weight: 500;
}

:deep(.n-card .n-card__content) {
  padding-top: 16px;
}

:deep(.n-grid-item) {
  min-width: 0; /* 防止内容溢出 */
}

.space-y-16px > :not([hidden]) ~ :not([hidden]) {
  margin-top: 16px;
}

.space-y-12px > :not([hidden]) ~ :not([hidden]) {
  margin-top: 12px;
}

.space-y-4px > :not([hidden]) ~ :not([hidden]) {
  margin-top: 4px;
}
</style>
