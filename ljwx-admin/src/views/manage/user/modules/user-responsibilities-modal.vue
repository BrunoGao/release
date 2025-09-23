<script setup lang="ts">
import { computed, reactive, shallowRef, watch } from 'vue';
import {
  fetchGetAllPositions,
  fetchGetAllRoles,
  fetchGetOrgUnitsTree,
  fetchGetUserResponsibilities,
  fetchSaveUserResponsibilities
} from '@/service/api';
import { useAuthStore } from '@/store/modules/auth';
import { $t } from '@/locales';
import { extractOptionsFromTree } from './shared';
import SvgIcon from '@/components/custom/svg-icon.vue';

defineOptions({
  name: 'UserResponsibilitiesSetting'
});

interface Props {
  userId: string;
}

interface Emits {
  (e: 'submitted'): void;
}

const authStore = useAuthStore();

const emit = defineEmits<Emits>();

const props = defineProps<Props>();

const visible = defineModel<boolean>('visible', {
  default: false
});

// 加载状态
const loading = reactive({
  init: false,
  submit: false
});

type Model = Api.SystemManage.UserResponsibilities;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    userId: props.userId,
    roleIds: [],
    positionIds: [],
    orgUnitsIds: [],
    orgUnitsPrincipalIds: []
  };
}

/** org units type */
type OrgUnitsTree = Api.SystemManage.OrgUnitsTree;

/** the enabled role options */
const roleOptions = shallowRef<CommonType.Option[]>([]);

/** the enabled position options */
const positionOptions = shallowRef<CommonType.Option[]>([]);

const customerId = computed(() => authStore.userInfo?.customerId);
/** org units tree data */
const orgUnitsTree = shallowRef<OrgUnitsTree[]>([]);
/** org units principal options */
const orgUnitsPrincipalOptions = computed(() => extractOptionsFromTree(orgUnitsTree.value, model.orgUnitsIds));

/** init options */
async function handleInitOptions() {
  try {
    loading.init = true;
    const roleResult = await fetchGetAllRoles();
    if (!roleResult.error && roleResult.data) {
      roleOptions.value = roleResult.data;
    }

    const positionResult = await fetchGetAllPositions(customerId.value);
    if (!positionResult.error && positionResult.data) {
      positionOptions.value = positionResult.data;
    }

    const orgResult = await fetchGetOrgUnitsTree(customerId.value);
    if (!orgResult.error && orgResult.data) {
      orgUnitsTree.value = orgResult.data;
    }
  } catch (error) {
    console.error('初始化选项失败:', error);
    window.$message?.error('加载数据失败，请重试');
  } finally {
    loading.init = false;
  }
}

/** init model */
async function handleInitModel() {
  Object.assign(model, createDefaultModel());
  await handleInitOptions();
  await handleUseResponsibilities();
}

/** get user responsibilities */
async function handleUseResponsibilities() {
  try {
    const { error, data } = await fetchGetUserResponsibilities(props.userId);
    if (!error && data) {
      Object.assign(model, data);
    }
  } catch (error) {
    console.error('获取用户权限职责失败:', error);
  }
}

/** update org units principal ids */
function handleOrgUnitsPrincipalIdsUpdate(value: string[]) {
  model.orgUnitsPrincipalIds = model.orgUnitsPrincipalIds.filter(id => value.includes(id));
}

/** submit */
async function handleSubmit() {
  try {
    loading.submit = true;
    const { error, data } = await fetchSaveUserResponsibilities(model);
    if (!error && data) {
      window.$message?.success($t('common.updateSuccess'));
      emit('submitted');
      closeModal();
    }
  } catch (error) {
    console.error('保存权限职责失败:', error);
    window.$message?.error('保存失败，请重试');
  } finally {
    loading.submit = false;
  }
}

function closeModal() {
  visible.value = false;
}

watch(visible, () => {
  if (visible.value) {
    handleInitModel();
  }
});
</script>

<template>
  <NModal 
    v-model:show="visible" 
    preset="card" 
    :segmented="false" 
    class="user-responsibilities-modal"
    :style="{ width: '900px', maxWidth: '90vw' }"
    :mask-closable="false"
  >
    <template #header>
      <div class="modal-header">
        <div class="header-icon">
          <SvgIcon icon="material-symbols:admin-panel-settings" class="text-24px text-blue-500" />
        </div>
        <div class="header-content">
          <h3 class="header-title">权限职责设置</h3>
          <p class="header-subtitle">配置用户的角色权限、职位分工和组织管理权限</p>
        </div>
      </div>
    </template>

    <div class="modal-content" v-loading="loading.init">
      <!-- 角色与职位配置区域 -->
      <div class="config-section">
        <div class="section-header">
          <SvgIcon icon="material-symbols:badge" class="section-icon" />
          <h4 class="section-title">角色与职位</h4>
          <span class="section-description">设置用户的系统角色和工作职位</span>
        </div>
        
        <NGrid :x-gap="16" :y-gap="16">
          <NFormItemGi span="12" :label="$t('page.manage.user.userRole')" class="form-item-enhanced">
            <template #label>
              <div class="label-with-icon">
                <SvgIcon icon="material-symbols:person-check" class="label-icon text-blue-500" />
                <span>{{ $t('page.manage.user.userRole') }}</span>
              </div>
            </template>
            <NSelect
              v-model:value="model.roleIds"
              multiple
              filterable
              :options="roleOptions"
              :max-tag-count="3"
              :placeholder="$t('page.manage.user.form.userRole')"
              :loading="loading.init"
              class="enhanced-select"
              size="large"
              clearable
            >
              <template #empty>
                <div class="empty-state">
                  <SvgIcon icon="material-symbols:search-off" class="text-32px text-gray-400" />
                  <span class="text-gray-500">暂无角色数据</span>
                </div>
              </template>
            </NSelect>
          </NFormItemGi>
          
          <NFormItemGi span="12" :label="$t('page.manage.user.userPosition')" class="form-item-enhanced">
            <template #label>
              <div class="label-with-icon">
                <SvgIcon icon="material-symbols:work" class="label-icon text-green-500" />
                <span>{{ $t('page.manage.user.userPosition') }}</span>
              </div>
            </template>
            <NSelect
              v-model:value="model.positionIds"
              multiple
              filterable
              :options="positionOptions"
              :max-tag-count="3"
              :placeholder="$t('page.manage.user.form.userPosition')"
              :loading="loading.init"
              class="enhanced-select"
              size="large"
              clearable
            >
              <template #empty>
                <div class="empty-state">
                  <SvgIcon icon="material-symbols:search-off" class="text-32px text-gray-400" />
                  <span class="text-gray-500">暂无职位数据</span>
                </div>
              </template>
            </NSelect>
          </NFormItemGi>
        </NGrid>
      </div>

      <!-- 组织架构配置区域 -->
      <div class="config-section">
        <div class="section-header">
          <SvgIcon icon="material-symbols:account-tree" class="section-icon" />
          <h4 class="section-title">组织架构</h4>
          <span class="section-description">配置用户所属的组织单位和管理权限</span>
        </div>
        
        <NGrid :x-gap="16" :y-gap="16">
          <NFormItemGi span="24" :label="$t('page.manage.user.userOrgUnits')" class="form-item-enhanced">
            <template #label>
              <div class="label-with-icon">
                <SvgIcon icon="material-symbols:corporate-fare" class="label-icon text-purple-500" />
                <span>{{ $t('page.manage.user.userOrgUnits') }}</span>
              </div>
            </template>
            <NTreeSelect
              v-model:value="model.orgUnitsIds"
              :options="orgUnitsTree"
              multiple
              checkable
              filterable
              key-field="id"
              label-field="name"
              default-expand-all
              :max-tag-count="5"
              :on-update-value="handleOrgUnitsPrincipalIdsUpdate"
              :placeholder="$t('page.manage.user.form.userOrgUnits')"
              :loading="loading.init"
              class="enhanced-tree-select"
              size="large"
              clearable
            >
              <template #empty>
                <div class="empty-state">
                  <SvgIcon icon="material-symbols:folder-off" class="text-32px text-gray-400" />
                  <span class="text-gray-500">暂无组织架构数据</span>
                </div>
              </template>
            </NTreeSelect>
          </NFormItemGi>
          
          <NFormItemGi span="24" :label="$t('page.manage.user.manageOrganization')" class="form-item-enhanced">
            <template #label>
              <div class="label-with-icon">
                <SvgIcon icon="material-symbols:supervisor-account" class="label-icon text-orange-500" />
                <span>{{ $t('page.manage.user.manageOrganization') }}</span>
                <NTooltip>
                  <template #trigger>
                    <SvgIcon icon="material-symbols:info" class="text-14px text-gray-400 ml-4px cursor-help" />
                  </template>
                  选择用户可以管理的组织单位，需要先选择所属组织
                </NTooltip>
              </div>
            </template>
            <NSelect
              v-model:value="model.orgUnitsPrincipalIds"
              multiple
              filterable
              :max-tag-count="5"
              :options="orgUnitsPrincipalOptions"
              :placeholder="$t('page.manage.user.form.userOrgUnits')"
              :disabled="!model.orgUnitsIds || model.orgUnitsIds.length === 0"
              class="enhanced-select"
              size="large"
              clearable
            >
              <template #empty>
                <div class="empty-state">
                  <SvgIcon icon="material-symbols:manage-accounts-off" class="text-32px text-gray-400" />
                  <span class="text-gray-500">
                    {{ !model.orgUnitsIds || model.orgUnitsIds.length === 0 ? '请先选择所属组织' : '暂无可管理的组织' }}
                  </span>
                </div>
              </template>
            </NSelect>
          </NFormItemGi>
        </NGrid>
      </div>

      <!-- 权限预览区域 -->
      <div class="config-section preview-section">
        <div class="section-header">
          <SvgIcon icon="material-symbols:preview" class="section-icon" />
          <h4 class="section-title">配置预览</h4>
          <span class="section-description">当前权限配置概览</span>
        </div>
        
        <div class="preview-grid">
          <div class="preview-card">
            <div class="preview-header">
              <SvgIcon icon="material-symbols:badge" class="text-blue-500" />
              <span>角色权限</span>
            </div>
            <div class="preview-content">
              <span class="preview-count">{{ model.roleIds?.length || 0 }}</span>
              <span class="preview-label">个角色</span>
            </div>
          </div>
          
          <div class="preview-card">
            <div class="preview-header">
              <SvgIcon icon="material-symbols:work" class="text-green-500" />
              <span>职位分工</span>
            </div>
            <div class="preview-content">
              <span class="preview-count">{{ model.positionIds?.length || 0 }}</span>
              <span class="preview-label">个职位</span>
            </div>
          </div>
          
          <div class="preview-card">
            <div class="preview-header">
              <SvgIcon icon="material-symbols:corporate-fare" class="text-purple-500" />
              <span>所属组织</span>
            </div>
            <div class="preview-content">
              <span class="preview-count">{{ model.orgUnitsIds?.length || 0 }}</span>
              <span class="preview-label">个部门</span>
            </div>
          </div>
          
          <div class="preview-card">
            <div class="preview-header">
              <SvgIcon icon="material-symbols:supervisor-account" class="text-orange-500" />
              <span>管理权限</span>
            </div>
            <div class="preview-content">
              <span class="preview-count">{{ model.orgUnitsPrincipalIds?.length || 0 }}</span>
              <span class="preview-label">个部门</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="modal-footer">
        <NButton 
          quaternary 
          size="large" 
          @click="closeModal"
          :disabled="loading.submit"
          class="cancel-btn"
        >
          <template #icon>
            <SvgIcon icon="material-symbols:close" />
          </template>
          {{ $t('common.cancel') }}
        </NButton>
        <NButton 
          type="primary" 
          size="large" 
          @click="handleSubmit"
          :loading="loading.submit"
          class="submit-btn"
        >
          <template #icon>
            <SvgIcon icon="material-symbols:check" />
          </template>
          {{ loading.submit ? '保存中...' : $t('common.confirm') }}
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
/* 弹窗整体样式 */
.user-responsibilities-modal {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.user-responsibilities-modal :deep(.n-card) {
  border-radius: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
}

/* 弹窗头部样式 */
.modal-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
}

.header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
}

.header-content {
  flex: 1;
}

.header-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.4;
}

.header-subtitle {
  margin: 4px 0 0 0;
  font-size: 14px;
  color: #6b7280;
  line-height: 1.4;
}

/* 内容区域样式 */
.modal-content {
  max-height: 70vh;
  overflow-y: auto;
  padding: 4px;
}

/* 配置区域样式 */
.config-section {
  margin-bottom: 32px;
  padding: 24px;
  border-radius: 12px;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.config-section:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.config-section:last-child {
  margin-bottom: 0;
}

/* 区域头部样式 */
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f3f4f6;
}

.section-icon {
  font-size: 20px;
  color: #3b82f6;
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.section-description {
  margin-left: auto;
  font-size: 12px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 4px 8px;
  border-radius: 4px;
}

/* 表单项样式 */
.form-item-enhanced {
  margin-bottom: 20px;
}

.form-item-enhanced :deep(.n-form-item-label) {
  font-weight: 500;
  color: #374151;
}

.label-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.label-icon {
  font-size: 16px;
}

/* 增强选择器样式 */
.enhanced-select,
.enhanced-tree-select {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.enhanced-select :deep(.n-base-selection),
.enhanced-tree-select :deep(.n-base-selection) {
  border-radius: 8px;
  border: 2px solid #e5e7eb;
  background: #ffffff;
  transition: all 0.3s ease;
}

.enhanced-select :deep(.n-base-selection:hover),
.enhanced-tree-select :deep(.n-base-selection:hover) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.enhanced-select :deep(.n-base-selection.n-base-selection--focus),
.enhanced-tree-select :deep(.n-base-selection.n-base-selection--focus) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

/* 空状态样式 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 32px;
  color: #6b7280;
}

/* 预览区域样式 */
.preview-section {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 2px solid #bae6fd;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.preview-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e0f2fe;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
  transition: all 0.3s ease;
}

.preview-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.15);
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.preview-content {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.preview-count {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
}

.preview-label {
  font-size: 12px;
  color: #6b7280;
}

/* 弹窗底部样式 */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 0 0 0;
  border-top: 1px solid #e5e7eb;
}

.cancel-btn {
  border-radius: 8px;
  border: 2px solid #e5e7eb;
  transition: all 0.3s ease;
}

.cancel-btn:hover {
  border-color: #6b7280;
  background: #f9fafb;
}

.submit-btn {
  border-radius: 8px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  font-weight: 500;
  transition: all 0.3s ease;
}

.submit-btn:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-responsibilities-modal {
    margin: 16px;
  }
  
  .config-section {
    padding: 16px;
    margin-bottom: 20px;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .section-description {
    margin-left: 0;
    align-self: stretch;
    text-align: center;
  }
  
  .preview-grid {
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  
  .preview-card {
    padding: 16px;
  }
  
  .modal-footer {
    flex-direction: column-reverse;
    gap: 8px;
  }
  
  .cancel-btn,
  .submit-btn {
    width: 100%;
  }
}

/* 加载状态优化 */
.modal-content[v-loading] {
  position: relative;
  min-height: 400px;
}

/* 滚动条样式 */
.modal-content::-webkit-scrollbar {
  width: 6px;
}

.modal-content::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.modal-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.modal-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
