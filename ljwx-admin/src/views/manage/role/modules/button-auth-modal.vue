<script setup lang="ts">
import { computed, reactive, shallowRef, watch } from 'vue';
import { $t } from '@/locales';
import { fetchAddRolePermission, fetchGetMenuPermission, fetchGetRolePermissionIds } from '@/service/api';

defineOptions({
  name: 'ButtonAuthModal'
});

interface Props {
  /** the roleId */
  roleId: string;
}

const props = defineProps<Props>();

const visible = defineModel<boolean>('visible', {
  default: false
});

const title = computed(() => $t('common.edit') + $t('page.manage.role.buttonAuth'));

/** tree checks */
const checks = shallowRef<string[]>([]);

/** menu auth model */
const model: Api.SystemManage.RolePermission = reactive(createDefaultModel());

function createDefaultModel(): Api.SystemManage.RolePermission {
  return {
    roleId: props.roleId,
    permissionIds: []
  };
}

/** menu permission data */
const permissionData = shallowRef<Api.SystemManage.MenuPermission[]>([]);

// 数据加载状态
const dataLoading = shallowRef(false);

async function getPermissionData() {
  try {
    dataLoading.value = true;
    const { error, data } = await fetchGetMenuPermission();
    if (!error && data) {
      permissionData.value = data;
      console.log('按钮权限数据加载完成:', data);
    } else {
      console.error('获取按钮权限数据失败:', error);
      permissionData.value = [];
    }
  } catch (error) {
    console.error('加载按钮权限数据异常:', error);
    permissionData.value = [];
  } finally {
    dataLoading.value = false;
  }
}

/** init get permissionIds for roleId, belong checks */
async function getPermissionIds() {
  try {
    dataLoading.value = true;
    
    // 首先获取角色已有的权限
    const { error: roleError, data: roleData } = await fetchGetRolePermissionIds(props.roleId);
    if (!roleError && roleData) {
      checks.value = roleData;
      console.log('当前角色已有权限:', roleData);
    } else {
      checks.value = [];
    }
    
    // 然后获取所有可用的权限数据
    await getPermissionData();
    
  } catch (error) {
    console.error('获取角色权限失败:', error);
    checks.value = [];
    window.$message?.error?.('获取权限数据失败，请重试');
  } finally {
    dataLoading.value = false;
  }
}

function closeModal() {
  visible.value = false;
}

async function handleSubmit() {
  model.permissionIds = checks.value;
  const { error, data } = await fetchAddRolePermission(model);
  if (!error && data) {
    window.$message?.success?.($t('common.modifySuccess'));
    closeModal();
  }
}

function selectAll() {
  // 确保permissionData已加载且有数据
  if (!permissionData.value || permissionData.value.length === 0) {
    console.warn('权限数据未加载或为空');
    window.$message?.warning?.('权限数据未加载，请稍后再试');
    return;
  }
  
  const allButtonIds: string[] = [];
  
  // 遍历所有菜单的按钮权限
  permissionData.value.forEach(item => {
    if (item.buttons && Array.isArray(item.buttons)) {
      item.buttons.forEach(button => {
        if (button.id) {
          allButtonIds.push(String(button.id));
        }
      });
    }
  });
  
  console.log('全选按钮权限ID列表:', allButtonIds);
  console.log('当前选中权限:', checks.value);
  
  // 更新选中状态
  checks.value = [...allButtonIds];
  
  console.log('全选后选中权限:', checks.value);
  window.$message?.success?.(`已选中 ${allButtonIds.length} 项按钮权限`);
}

function clearAll() {
  checks.value = [];
  console.log('清空所有选中权限');
  window.$message?.success?.('已清空所有选中的按钮权限');
}

watch(visible, () => {
  if (visible.value) {
    Object.assign(model, createDefaultModel());
    getPermissionIds();
  }
});
</script>

<template>
  <NModal v-model:show="visible" :title="title" preset="card" :segmented="false" class="enhanced-button-modal w-1080px">
    <div class="button-auth-header">
      <NAlert type="info" :show-icon="false">
        <template #header>
          <div class="flex items-center gap-2">
            <span class="i-material-symbols:smart-button text-lg"></span>
            <span class="font-semibold">按钮权限配置</span>
          </div>
        </template>
        为该角色分配按钮操作权限，精确控制功能访问范围
      </NAlert>
    </div>

    <div class="permission-stats">
      <NSpace>
        <NTag type="primary" size="small">已选择 {{ checks.length }} 项权限</NTag>
        <NButton 
          size="small" 
          type="info" 
          quaternary 
          :loading="dataLoading"
          :disabled="dataLoading || !permissionData?.length"
          @click="selectAll"
        >
          全选
        </NButton>
        <NButton 
          size="small" 
          type="warning" 
          quaternary 
          :disabled="!checks.length"
          @click="clearAll"
        >
          清空
        </NButton>
      </NSpace>
    </div>

    <NCheckboxGroup v-model:value="checks" class="permission-container">
      <NSpin :show="dataLoading" :description="dataLoading ? '正在加载权限数据...' : ''">
        <NDescriptions 
          v-if="permissionData && permissionData.length > 0" 
          label-placement="left" 
          bordered 
          :column="1" 
          class="permission-descriptions"
        >
          <NDescriptionsItem v-for="item in permissionData" :key="item.menuId" :label="$t(item.i18nKey)" class="menu-permission-item">
            <div class="button-permission-grid">
              <div v-for="button in item.buttons" :key="button.id" class="button-permission-card">
                <NCheckbox :value="button.id" :label="button.name" class="enhanced-checkbox">
                  <template #default>
                    <div class="button-info">
                      <span class="button-name">{{ button.name }}</span>
                      <NTag size="tiny" type="info">{{ button.code }}</NTag>
                    </div>
                  </template>
                </NCheckbox>
              </div>
            </div>
          </NDescriptionsItem>
        </NDescriptions>
        
        <NEmpty 
          v-else-if="!dataLoading" 
          description="暂无按钮权限数据" 
          class="empty-state"
        />
      </NSpin>
    </NCheckboxGroup>

    <template #footer>
      <NSpace justify="end" class="enhanced-footer">
        <NButton size="small" quaternary @click="closeModal">
          {{ $t('common.cancel') }}
        </NButton>
        <NButton type="primary" size="small" @click="handleSubmit">
          {{ $t('common.confirm') }}
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<style scoped>
.enhanced-button-modal {
  max-height: 90vh;
}

.button-auth-header {
  margin-bottom: 16px;
}

.permission-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.permission-container {
  max-height: 500px;
  overflow-y: auto;
  padding: 8px;
}

.permission-descriptions {
  background: white;
  border-radius: 8px;
}

.menu-permission-item {
  padding: 12px;
}

.button-permission-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  padding: 8px;
}

.button-permission-card {
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fafafa;
  transition: all 0.3s ease;
}

.button-permission-card:hover {
  border-color: #3b82f6;
  background: #f0f9ff;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
}

.enhanced-checkbox {
  width: 100%;
}

.button-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 4px 0;
}

.button-name {
  font-weight: 500;
  color: #374151;
  font-size: 13px;
}

.enhanced-footer {
  padding-top: 8px;
  border-top: 1px solid #e5e7eb;
}

/* 滚动条优化 */
.permission-container::-webkit-scrollbar {
  width: 6px;
}

.permission-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.permission-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.permission-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 空状态样式 */
.empty-state {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 14px;
}

/* 加载状态优化 */
.permission-container :deep(.n-spin-content) {
  min-height: 200px;
}

.permission-container :deep(.n-spin-description) {
  color: #6b7280;
  font-size: 13px;
  margin-top: 8px;
}
</style>
