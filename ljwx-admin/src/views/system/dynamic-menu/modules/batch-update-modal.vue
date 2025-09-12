<template>
  <NModal
    v-model:show="modalVisible"
    :mask-closable="false"
    preset="card"
    title="批量操作菜单"
    class="w-600px"
  >
    <div class="space-y-16px">
      <!-- 操作类型选择 -->
      <div>
        <div class="text-sm font-medium mb-8px">操作类型</div>
        <NRadioGroup v-model:value="formModel.operation" @update:value="handleOperationChange">
          <NGrid :cols="2" :x-gap="12" :y-gap="8">
            <NGridItem>
              <NRadio value="update">更新字段</NRadio>
            </NGridItem>
            <NGridItem>
              <NRadio value="enable">批量启用</NRadio>
            </NGridItem>
            <NGridItem>
              <NRadio value="disable">批量禁用</NRadio>
            </NGridItem>
            <NGridItem>
              <NRadio value="move">移动菜单</NRadio>
            </NGridItem>
            <NGridItem>
              <NRadio value="delete">批量删除</NRadio>
            </NGridItem>
          </NGrid>
        </NRadioGroup>
      </div>

      <!-- 选中的菜单信息 -->
      <div>
        <div class="text-sm font-medium mb-8px">选中菜单</div>
        <div class="p-12px bg-gray-50 rounded-8px">
          <div class="text-sm text-gray-600">
            已选择 <span class="font-medium text-primary">{{ selectedKeys.length }}</span> 个菜单进行操作
          </div>
        </div>
      </div>

      <!-- 操作配置 -->
      <div v-if="showOperationConfig">
        <!-- 字段更新配置 -->
        <div v-if="formModel.operation === 'update'">
          <div class="text-sm font-medium mb-8px">更新字段</div>
          <div class="space-y-12px">
            <div class="flex-y-center gap-12px">
              <NCheckbox v-model:checked="updateFields.status.enabled" @update:checked="handleFieldToggle('status')">
                状态
              </NCheckbox>
              <NSelect
                v-model:value="updateFields.status.value"
                :disabled="!updateFields.status.enabled"
                :options="statusOptions"
                placeholder="选择状态"
                class="w-120px"
              />
            </div>
            
            <div class="flex-y-center gap-12px">
              <NCheckbox v-model:checked="updateFields.hide.enabled" @update:checked="handleFieldToggle('hide')">
                显示隐藏
              </NCheckbox>
              <NSelect
                v-model:value="updateFields.hide.value"
                :disabled="!updateFields.hide.enabled"
                :options="hideOptions"
                placeholder="选择显示状态"
                class="w-120px"
              />
            </div>
            
            <div class="flex-y-center gap-12px">
              <NCheckbox v-model:checked="updateFields.icon.enabled" @update:checked="handleFieldToggle('icon')">
                图标
              </NCheckbox>
              <NInput
                v-model:value="updateFields.icon.value"
                :disabled="!updateFields.icon.enabled"
                placeholder="输入图标名称"
                class="flex-1"
              />
              <NButton
                :disabled="!updateFields.icon.enabled"
                @click="handleIconSelect"
              >
                选择
              </NButton>
            </div>
          </div>
        </div>

        <!-- 移动配置 -->
        <div v-if="formModel.operation === 'move'">
          <div class="text-sm font-medium mb-8px">移动配置</div>
          <div class="space-y-12px">
            <NFormItem label="目标父菜单" class="mb-0">
              <NTreeSelect
                v-model:value="formModel.targetParentId"
                :options="parentMenuOptions"
                key-field="id"
                label-field="name"
                children-field="children"
                placeholder="选择目标父菜单"
                clearable
                filterable
                class="w-full"
              />
            </NFormItem>
            
            <NFormItem label="插入位置" class="mb-0">
              <NRadioGroup v-model:value="formModel.position">
                <NRadio value="first">最前</NRadio>
                <NRadio value="last">最后</NRadio>
                <NRadio value="before">指定位置前</NRadio>
                <NRadio value="after">指定位置后</NRadio>
              </NRadioGroup>
            </NFormItem>
            
            <NFormItem 
              v-if="formModel.position === 'before' || formModel.position === 'after'"
              label="参考菜单"
              class="mb-0"
            >
              <NSelect
                v-model:value="formModel.referenceMenuId"
                :options="referenceMenuOptions"
                placeholder="选择参考菜单"
                class="w-full"
              />
            </NFormItem>
          </div>
        </div>

        <!-- 删除配置 -->
        <div v-if="formModel.operation === 'delete'">
          <div class="text-sm font-medium mb-8px">删除配置</div>
          <div class="space-y-12px">
            <NCheckbox v-model:checked="formModel.recursive">
              递归删除子菜单
            </NCheckbox>
            <NCheckbox v-model:checked="formModel.force">
              强制删除（忽略警告）
            </NCheckbox>
            
            <NAlert type="warning" class="text-sm">
              <template #icon>
                <SvgIcon icon="mdi:alert" />
              </template>
              删除操作不可逆，请谨慎操作！
            </NAlert>
          </div>
        </div>
      </div>

      <!-- 操作原因 -->
      <div v-if="needReason">
        <div class="text-sm font-medium mb-8px">操作原因</div>
        <NInput
          v-model:value="formModel.reason"
          type="textarea"
          placeholder="请输入操作原因（可选）"
          :rows="3"
        />
      </div>
    </div>

    <template #footer>
      <div class="flex gap-12px justify-end">
        <NButton @click="modalVisible = false">取消</NButton>
        <NButton
          type="primary"
          :disabled="!canConfirm"
          @click="handleConfirm"
        >
          确定执行
        </NButton>
      </div>
    </template>

    <!-- 图标选择器模态框 -->
    <IconSelectModal
      v-model:visible="iconSelectVisible"
      @confirm="handleIconConfirm"
    />
  </NModal>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import SvgIcon from '@/components/custom/svg-icon.vue';
import IconSelectModal from './icon-select-modal.vue';

interface BatchUpdateFormModel {
  operation: string;
  updateFields?: Record<string, any>;
  targetParentId?: number;
  position: string;
  referenceMenuId?: number;
  recursive: boolean;
  force: boolean;
  reason?: string;
}

interface Props {
  visible: boolean;
  selectedKeys: number[];
  parentMenuOptions?: any[];
}

interface Emits {
  (e: 'update:visible', visible: boolean): void;
  (e: 'confirm', formData: BatchUpdateFormModel): void;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  selectedKeys: () => [],
  parentMenuOptions: () => []
});

const emit = defineEmits<Emits>();

// 响应式数据
const iconSelectVisible = ref(false);

const modalVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
});

// 表单模型
const formModel = reactive<BatchUpdateFormModel>({
  operation: 'update',
  position: 'last',
  recursive: false,
  force: false
});

// 更新字段配置
const updateFields = reactive({
  status: { enabled: false, value: '1' },
  hide: { enabled: false, value: 'N' },
  icon: { enabled: false, value: '' }
});

// 计算属性
const showOperationConfig = computed(() => {
  return ['update', 'move', 'delete'].includes(formModel.operation);
});

const needReason = computed(() => {
  return ['delete', 'move'].includes(formModel.operation);
});

const canConfirm = computed(() => {
  if (props.selectedKeys.length === 0) return false;
  
  switch (formModel.operation) {
    case 'update':
      return Object.values(updateFields).some(field => field.enabled);
    case 'move':
      return formModel.targetParentId !== undefined;
    case 'delete':
    case 'enable':
    case 'disable':
      return true;
    default:
      return false;
  }
});

// 选项数据
const statusOptions = [
  { label: '启用', value: '1' },
  { label: '禁用', value: '0' }
];

const hideOptions = [
  { label: '显示', value: 'N' },
  { label: '隐藏', value: 'Y' }
];

const referenceMenuOptions = computed(() => {
  // TODO: 根据目标父菜单获取同级菜单选项
  return [];
});

// 事件处理
function handleOperationChange(operation: string) {
  // 重置相关配置
  if (operation !== 'update') {
    Object.values(updateFields).forEach(field => {
      field.enabled = false;
    });
  }
  
  if (operation !== 'move') {
    formModel.targetParentId = undefined;
    formModel.position = 'last';
    formModel.referenceMenuId = undefined;
  }
  
  if (operation !== 'delete') {
    formModel.recursive = false;
    formModel.force = false;
  }
}

function handleFieldToggle(fieldName: string) {
  const field = updateFields[fieldName as keyof typeof updateFields];
  if (!field.enabled) {
    // 清空值
    field.value = fieldName === 'status' ? '1' : (fieldName === 'hide' ? 'N' : '');
  }
}

function handleIconSelect() {
  iconSelectVisible.value = true;
}

function handleIconConfirm(icon: string) {
  updateFields.icon.value = icon;
  iconSelectVisible.value = false;
}

function handleConfirm() {
  const data: BatchUpdateFormModel = {
    operation: formModel.operation,
    position: formModel.position,
    recursive: formModel.recursive,
    force: formModel.force,
    reason: formModel.reason
  };

  // 根据操作类型添加特定字段
  if (formModel.operation === 'update') {
    const fields: Record<string, any> = {};
    Object.entries(updateFields).forEach(([key, field]) => {
      if (field.enabled && field.value !== '') {
        fields[key] = field.value;
      }
    });
    data.updateFields = fields;
  }

  if (formModel.operation === 'move') {
    data.targetParentId = formModel.targetParentId;
    data.referenceMenuId = formModel.referenceMenuId;
  }

  emit('confirm', data);
}
</script>

<style scoped>
:deep(.n-form-item) {
  margin-bottom: 0;
}

:deep(.n-form-item-label) {
  min-width: 80px;
}
</style>