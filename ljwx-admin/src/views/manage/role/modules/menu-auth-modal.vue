<script setup lang="ts">
import { computed, reactive, shallowRef, watch } from 'vue';
import type { TreeOption } from 'naive-ui';
import { $t } from '@/locales';
import { fetchAddRoleMenu, fetchGetMenuTree, fetchGetRoleMenuIds } from '@/service/api';

defineOptions({
  name: 'MenuAuthModal'
});

interface Props {
  /** the roleId */
  roleId: string;
}

const props = defineProps<Props>();

const visible = defineModel<boolean>('visible', {
  default: false
});

const title = computed(() => $t('common.edit') + $t('page.manage.role.menuAuth'));

/** menu tree data */
const tree = shallowRef<TreeOption[]>([]);

/** tree checks */
const checks = shallowRef<string[]>([]);

/** menu auth model */
const model: Api.SystemManage.RoleMenu = reactive(createDefaultModel());

function createDefaultModel(): Api.SystemManage.RoleMenu {
  return {
    roleId: props.roleId,
    menuIds: []
  };
}

/** init menu tree */
async function getTree() {
  const { error, data } = await fetchGetMenuTree();
  if (!error) {
    tree.value = data.map(recursive);
  }
}

/** init get menuIds for roleId, belong checks */
async function getMenuId() {
  const { error, data } = await fetchGetRoleMenuIds(props.roleId);
  if (!error) {
    checks.value = data;
    getTree();
  }
}

/** recursive menu tree data, add prefix transform treeOption format */
function recursive(item: Api.SystemManage.Menu): TreeOption {
  const result: TreeOption = {
    key: item.id,
    label: $t(item.i18nKey as App.I18n.I18nKey)
  };
  if (item.children) {
    result.children = item.children.map(recursive);
  }
  return result;
}

/** submit */
async function handleSubmit() {
  // request
  model.menuIds = checks.value;
  const { error, data } = await fetchAddRoleMenu(model);
  if (!error && data) {
    window.$message?.success?.($t('common.modifySuccess'));
    closeModal();
  }
}

function closeModal() {
  visible.value = false;
}

function init() {
  Object.assign(model, createDefaultModel());
  getMenuId();
}

function getAllKeys(node: TreeOption): string[] {
  const keys = [node.key as string];
  if (node.children) {
    node.children.forEach(child => {
      keys.push(...getAllKeys(child));
    });
  }
  return keys;
}

function selectAll() {
  checks.value = tree.value.map(node => getAllKeys(node)).flat();
}

watch(visible, val => {
  if (val) {
    init();
  }
});
</script>

<template>
  <NModal v-model:show="visible" :title="title" preset="card" class="w-600px enhanced-menu-modal">
    <div class="menu-auth-header">
      <NAlert type="info" :show-icon="false">
        <template #header>
          <div class="flex items-center gap-2">
            <span class="i-material-symbols:menu-book text-lg"></span>
            <span class="font-semibold">菜单权限配置</span>
          </div>
        </template>
        为该角色分配菜单访问权限，支持层级权限继承
      </NAlert>
    </div>
    
    <div class="tree-controls">
      <NSpace>
        <NButton size="small" type="info" quaternary @click="selectAll">
          全选
        </NButton>
        <NButton size="small" type="warning" quaternary @click="checks = []">
          清空
        </NButton>
      </NSpace>
      <NTag v-if="checks.length > 0" type="success">
        已选择 {{ checks.length }} 项
      </NTag>
    </div>
    
    <NTree 
      v-model:checked-keys="checks" 
      :data="tree" 
      block-line 
      expand-on-click 
      checkable 
      cascade 
      virtual-scroll 
      class="enhanced-tree" 
    />
    
    <template #footer>
      <NSpace justify="end">
        <NButton quaternary @click="closeModal">
          {{ $t('common.cancel') }}
        </NButton>
        <NButton type="primary" @click="handleSubmit">
          {{ $t('common.confirm') }}
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>


<style scoped>
.enhanced-menu-modal {
  max-height: 90vh;
}

.menu-auth-header {
  margin-bottom: 16px;
}

.tree-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.enhanced-tree {
  height: 450px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px;
  background: white;
}

.enhanced-tree :deep(.n-tree-node-content) {
  padding: 6px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.enhanced-tree :deep(.n-tree-node-content:hover) {
  background: #f3f4f6;
}

.enhanced-tree :deep(.n-tree-node-checkbox) {
  margin-right: 8px;
}
</style>