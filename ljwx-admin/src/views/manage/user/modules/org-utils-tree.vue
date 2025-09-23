<script setup lang="ts">
import type { Ref } from 'vue';
import { h, onMounted, ref, shallowRef } from 'vue';
import type { TreeOption } from 'naive-ui';
import { NButton, NButtonGroup, NFlex, NPopconfirm } from 'naive-ui';
import { useBoolean } from '@sa/hooks';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { fetchDeleteOrgUnits, fetchGetOrgUnits, fetchGetOrgUnitsTree } from '@/service/api';
import SvgIcon from '@/components/custom/svg-icon.vue';
import { $t } from '@/locales';
import OrgUnitsOperateDrawer from '@/views/manage/org/modules/org-units-operate-drawer.vue';
import { transDeleteParams } from '@/utils/common';
import type { OperateType } from './shared';

defineOptions({
  name: 'UserOrgUnitsTree'
});

const name = ref<string>('');

type Emits = {
  (e: 'select', visible: boolean, item: Api.SystemManage.OrgUnitsTree): void;
};

const emit = defineEmits<Emits>();

const { hasAuth } = useAuth();

const authStore = useAuthStore();
const operateType = ref<OperateType>('add');

const orgUnitsTreeData = shallowRef<Api.SystemManage.OrgUnitsTree[]>([]);

const { bool: visible, setTrue: openDrawer } = useBoolean();

const { bool: userItemVisible, setBool: setUserItemVisible } = useBoolean();

const editingData: Ref<Api.SystemManage.OrgUnits | null> = ref(null);

/** init */
const init = async () => {
  const { data, error } = await fetchGetOrgUnitsTree();
  if (!error && data) {
    orgUnitsTreeData.value = data;
  }
};

/** add */
const handleAdd = () => {
  operateType.value = 'add';
  openDrawer();
};

/** add child */
const handleAddChild = async (item: Api.SystemManage.OrgUnitsTree) => {
  const { error, data } = await fetchGetOrgUnits(item.id);
  if (!error && data) {
    operateType.value = 'addChild';
    editingData.value = { ...data };
    openDrawer();
  }
};

/** edit */
const handleEdit = async (item: Api.SystemManage.OrgUnitsTree) => {
  const { error, data } = await fetchGetOrgUnits(item.id);
  if (!error && data) {
    operateType.value = 'edit';
    editingData.value = { ...data };
    openDrawer();
  }
};

/** delete */
const handleDelete = async (item: Api.SystemManage.OrgUnitsTree) => {
  const { error, data: result } = await fetchDeleteOrgUnits(transDeleteParams([item.id]));
  if (!error && result) {
    window.$message?.success($t('common.deleteSuccess'));
    await init();
  }
};

/** render suffix */
function renderSuffix({ option }: { option: TreeOption }) {
  const item = option as Api.SystemManage.OrgUnitsTree;
  if (item.id === '-1') return null;
  return h(
    NButtonGroup,
    {},
    {
      default: () => [
        hasAuth('sys:org:units:add') &&
          h(
            NButton,
            {
              size: 'tiny',
              quaternary: true,
              onClick: event => {
                event.stopPropagation();
                handleAddChild(item);
              }
            },
            { icon: () => h(SvgIcon, { icon: 'ic:round-playlist-add' }) }
          ),
        hasAuth('sys:org:units:update') &&
          h(
            NButton,
            {
              size: 'tiny',
              quaternary: true,
              onClick: event => {
                event.stopPropagation();
                handleEdit(item);
              }
            },
            { icon: () => h(SvgIcon, { icon: 'ic:round-edit' }) }
          ),
        hasAuth('sys:org:units:delete') &&
          h(
            NPopconfirm,
            {
              onPositiveClick: () => handleDelete(item)
            },
            {
              default: () => $t('common.confirmDelete'),
              trigger: () =>
                h(
                  NButton,
                  {
                    size: 'tiny',
                    quaternary: true,
                    onClick: event => {
                      event.stopPropagation();
                    }
                  },
                  { icon: () => h(SvgIcon, { icon: 'ic:round-delete' }) }
                )
            }
          )
      ]
    }
  );
}

/** tree select handle */
function handleSelectKeys(node: NaiveUI.TreeOption | null, action: string) {
  setUserItemVisible(action === 'select');
  emit('select', userItemVisible.value, node as Api.SystemManage.OrgUnitsTree);
}

onMounted(() => init());
</script>

<template>
  <div class="h-full-hidden">
    <NCard :bordered="false" size="small" class="h-full sm:flex-1-hidden department-tree-card" content-class="h-full-hidden">
      <template #header>
        <div class="department-header">
          <SvgIcon icon="material-symbols:corporate-fare" class="text-18px text-blue-500" />
          <span class="department-title">部门列表</span>
        </div>
      </template>
      <template #header-extra>
        <NFlex>
          <NButton v-if="hasAuth('sys:org:units:add')" ghost type="primary" @click="handleAdd()">
            {{ $t('common.add') }}
          </NButton>
          <NButton quaternary>
            <template #icon>
              <SvgIcon icon="ic:round-refresh" />
            </template>
          </NButton>
        </NFlex>
      </template>
      <NInput v-model:value="name" clearable placeholder="搜索部门名称" />
      <NTree
        :pattern="name"
        :data="orgUnitsTreeData"
        accordion
        block-line
        key-field="id"
        label-field="name"
        virtual-scroll
        :show-irrelevant-nodes="false"
        :render-suffix="renderSuffix"
        class="p-tree my-3 flex-col-stretch"
        @update-selected-keys="(_key, _option, { node, action }) => handleSelectKeys(node, action)"
      />
    </NCard>
    <OrgUnitsOperateDrawer v-model:visible="visible" :operate-type="operateType" :row-data="editingData" @submitted="init" />
  </div>
</template>

<style lang="scss" scoped>
/* 部门树卡片样式 */
.department-tree-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
}

.department-tree-card :deep(.n-card__header) {
  padding: 16px 20px 12px 20px;
  border-bottom: 2px solid #f3f4f6;
}

/* 部门头部样式 */
.department-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.department-title {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

/* 搜索框样式 */
.department-tree-card :deep(.n-input) {
  border-radius: 8px;
  margin-bottom: 12px;
}

.department-tree-card :deep(.n-input__input-el) {
  border: 2px solid #e5e7eb;
  transition: all 0.3s ease;
}

.department-tree-card :deep(.n-input:hover .n-input__input-el) {
  border-color: #3b82f6;
}

.department-tree-card :deep(.n-input.n-input--focus .n-input__input-el) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* 树节点样式优化 */
:deep(.n-tree) {
  .n-tree-node-content__suffix {
    display: none;
  }
  .n-tree-node-content:hover .n-tree-node-content__suffix {
    display: inline-flex;
  }
  
  .n-tree-node {
    border-radius: 6px;
    margin: 2px 0;
    transition: all 0.2s ease;
  }
  
  .n-tree-node:hover {
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  }
  
  .n-tree-node--selected {
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
    border: 1px solid #3b82f6;
  }
  
  .n-tree-node-content {
    padding: 8px 12px;
    border-radius: 6px;
  }
  
  .n-tree-node-content__text {
    font-weight: 500;
    color: #374151;
  }
  
  .n-tree-node--selected .n-tree-node-content__text {
    color: #1d4ed8;
    font-weight: 600;
  }
}

/* 操作按钮样式 */
:deep(.n-button-group .n-button) {
  border-radius: 4px;
  transition: all 0.2s ease;
}

:deep(.n-button-group .n-button:hover) {
  transform: scale(1.1);
}

/* 头部按钮样式 */
.department-tree-card :deep(.n-card__header-extra .n-button) {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.department-tree-card :deep(.n-card__header-extra .n-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

/* 刷新按钮特殊样式 */
.department-tree-card :deep(.n-card__header-extra .n-button[quaternary]) {
  color: #6b7280;
  border: 1px solid #e5e7eb;
}

.department-tree-card :deep(.n-card__header-extra .n-button[quaternary]:hover) {
  color: #3b82f6;
  border-color: #3b82f6;
  background: #f0f9ff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .department-tree-card :deep(.n-card__header) {
    padding: 12px 16px 8px 16px;
  }
  
  .department-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .department-title {
    font-size: 14px;
  }
  
  :deep(.n-tree .n-tree-node-content) {
    padding: 6px 8px;
  }
}
</style>
