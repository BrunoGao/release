<script setup lang="ts">
import { computed, h, reactive, ref, watch } from 'vue';
import type { FormInst, FormRules } from 'naive-ui';
import SvgIcon from '@/components/custom/svg-icon.vue';
import IconSelectModal from './icon-select-modal.vue';

interface MenuFormModel {
  id?: number;
  parentId?: number;
  type: string;
  name: string;
  title: string;
  i18nKey?: string;
  routeName?: string;
  routePath?: string;
  component?: string;
  icon?: string;
  iconType: string;
  status: string;
  hide: string;
  href?: string;
  iframeUrl?: string;
  sort: number;
  permission?: string;
  requireAuth: boolean;
  keepAlive: boolean;
  description?: string;
}

interface Props {
  visible: boolean;
  menuData?: any;
  operationType: 'add' | 'edit';
  parentMenuOptions?: any[];
}

interface Emits {
  (e: 'update:visible', visible: boolean): void;
  (e: 'confirm', formData: MenuFormModel): void;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  operationType: 'add',
  parentMenuOptions: () => []
});

const emit = defineEmits<Emits>();

// 响应式数据
const formRef = ref<FormInst>();
const iconSelectVisible = ref(false);

const modalVisible = computed({
  get: () => props.visible,
  set: value => emit('update:visible', value)
});

const isEdit = computed(() => props.operationType === 'edit');

// 表单模型
const formModel = reactive<MenuFormModel>({
  type: '2',
  name: '',
  title: '',
  iconType: '1',
  status: '1',
  hide: 'N',
  sort: 100,
  requireAuth: true,
  keepAlive: false
});

// 显示路由配置
const showRouteConfig = computed(() => {
  return formModel.type === '1' || formModel.type === '2';
});

// 选项数据
const typeOptions = [
  { label: '目录', value: '1' },
  { label: '菜单', value: '2' },
  { label: '按钮', value: '3' }
];

// 表单验证规则
const rules: FormRules = {
  type: {
    required: true,
    message: '请选择菜单类型',
    trigger: 'change'
  },
  name: {
    required: true,
    message: '请输入菜单名称',
    trigger: 'blur'
  },
  title: {
    required: true,
    message: '请输入显示名称',
    trigger: 'blur'
  },
  routePath: {
    required: true,
    message: '请输入路由路径',
    trigger: 'blur',
    validator: (rule, value) => {
      if (formModel.type === '2' && !value) {
        return new Error('菜单类型为菜单时，路由路径不能为空');
      }
      if (value && !value.startsWith('/')) {
        return new Error('路由路径必须以/开头');
      }
      return true;
    }
  },
  component: {
    required: true,
    message: '请输入组件路径',
    trigger: 'blur',
    validator: (rule, value) => {
      if (formModel.type === '2' && !value) {
        return new Error('菜单类型为菜单时，组件路径不能为空');
      }
      return true;
    }
  },
  sort: {
    type: 'number',
    required: true,
    message: '请输入排序值',
    trigger: 'blur'
  }
};

// 事件处理
function handleTypeChange(type: string) {
  // 根据类型自动设置一些默认值
  if (type === '3') {
    formModel.routePath = '';
    formModel.component = '';
  }
}

function handleNameBlur() {
  // 如果显示名称为空，自动填入菜单名称
  if (!formModel.title && formModel.name) {
    formModel.title = formModel.name;
  }

  // 如果国际化键为空，自动生成
  if (!formModel.i18nKey && formModel.name) {
    formModel.i18nKey = `menu.${formModel.name.toLowerCase().replace(/\s+/g, '_')}`;
  }
}

function handleIconSelect() {
  iconSelectVisible.value = true;
}

function handleIconConfirm(icon: string) {
  formModel.icon = icon;
  iconSelectVisible.value = false;
}

async function handleConfirm() {
  try {
    await formRef.value?.validate();
    emit('confirm', { ...formModel });
  } catch (error) {
    console.error('表单验证失败:', error);
  }
}

// 监听菜单数据变化，初始化表单
watch(
  () => props.menuData,
  menuData => {
    if (menuData) {
      Object.assign(formModel, {
        id: menuData.id,
        parentId: menuData.parentId,
        type: menuData.type || '2',
        name: menuData.name || '',
        title: menuData.title || '',
        i18nKey: menuData.i18nKey || '',
        routeName: menuData.routeName || '',
        routePath: menuData.routePath || '',
        component: menuData.component || '',
        icon: menuData.icon || '',
        iconType: menuData.iconType || '1',
        status: menuData.status || '1',
        hide: menuData.hide || 'N',
        href: menuData.href || '',
        iframeUrl: menuData.iframeUrl || '',
        sort: menuData.sort || 100,
        permission: menuData.permission || '',
        requireAuth: menuData.requireAuth ?? true,
        keepAlive: menuData.keepAlive ?? false,
        description: menuData.description || ''
      });
    } else {
      // 重置表单
      Object.assign(formModel, {
        id: undefined,
        parentId: undefined,
        type: '2',
        name: '',
        title: '',
        i18nKey: '',
        routeName: '',
        routePath: '',
        component: '',
        icon: '',
        iconType: '1',
        status: '1',
        hide: 'N',
        href: '',
        iframeUrl: '',
        sort: 100,
        permission: '',
        requireAuth: true,
        keepAlive: false,
        description: ''
      });
    }
  },
  { immediate: true }
);

// 监听visible变化，重置验证状态
watch(
  () => props.visible,
  visible => {
    if (!visible) {
      formRef.value?.restoreValidation();
    }
  }
);
</script>

<template>
  <NModal v-model:show="modalVisible" :mask-closable="false" preset="card" :title="isEdit ? '编辑菜单' : '新增菜单'" class="max-h-700px w-800px">
    <NForm ref="formRef" :model="formModel" :rules="rules" label-placement="left" label-width="120px" require-mark-placement="left">
      <NGrid :cols="2" x-gap="16">
        <!-- 基础信息 -->
        <NGridItem :span="2">
          <div class="mb-12px text-base font-medium">基础信息</div>
        </NGridItem>

        <NGridItem>
          <NFormItem label="菜单类型" path="type">
            <NSelect v-model:value="formModel.type" :options="typeOptions" placeholder="请选择菜单类型" @update:value="handleTypeChange" />
          </NFormItem>
        </NGridItem>

        <NGridItem>
          <NFormItem label="父级菜单" path="parentId">
            <NTreeSelect
              v-model:value="formModel.parentId"
              :options="parentMenuOptions"
              key-field="id"
              label-field="name"
              children-field="children"
              placeholder="请选择父级菜单（不选为顶级菜单）"
              clearable
              filterable
            />
          </NFormItem>
        </NGridItem>

        <NGridItem>
          <NFormItem label="菜单名称" path="name">
            <NInput v-model:value="formModel.name" placeholder="请输入菜单名称" @blur="handleNameBlur" />
          </NFormItem>
        </NGridItem>

        <NGridItem>
          <NFormItem label="显示名称" path="title">
            <NInput v-model:value="formModel.title" placeholder="请输入显示名称" />
          </NFormItem>
        </NGridItem>

        <NGridItem>
          <NFormItem label="国际化键" path="i18nKey">
            <NInput v-model:value="formModel.i18nKey" placeholder="请输入国际化键值" />
          </NFormItem>
        </NGridItem>

        <NGridItem>
          <NFormItem label="排序值" path="sort">
            <NInputNumber v-model:value="formModel.sort" placeholder="排序值" :min="0" :max="9999" class="w-full" />
          </NFormItem>
        </NGridItem>

        <!-- 路由配置 -->
        <NGridItem :span="2">
          <div class="mb-12px mt-16px text-base font-medium">路由配置</div>
        </NGridItem>

        <NGridItem v-if="showRouteConfig">
          <NFormItem label="路由名称" path="routeName">
            <NInput v-model:value="formModel.routeName" placeholder="请输入路由名称" />
          </NFormItem>
        </NGridItem>

        <NGridItem v-if="showRouteConfig">
          <NFormItem label="路由路径" path="routePath">
            <NInput v-model:value="formModel.routePath" placeholder="请输入路由路径，如：/system/user" />
          </NFormItem>
        </NGridItem>

        <NGridItem v-if="showRouteConfig">
          <NFormItem label="组件路径" path="component">
            <NInput v-model:value="formModel.component" placeholder="请输入组件路径" />
          </NFormItem>
        </NGridItem>

        <NGridItem v-if="formModel.type === '2'">
          <NFormItem label="外链地址" path="href">
            <NInput v-model:value="formModel.href" placeholder="外链地址（可选）" />
          </NFormItem>
        </NGridItem>

        <NGridItem v-if="formModel.type === '2'">
          <NFormItem label="iframe地址" path="iframeUrl">
            <NInput v-model:value="formModel.iframeUrl" placeholder="iframe地址（可选）" />
          </NFormItem>
        </NGridItem>

        <!-- 图标配置 -->
        <NGridItem :span="2">
          <div class="mb-12px mt-16px text-base font-medium">图标配置</div>
        </NGridItem>

        <NGridItem>
          <NFormItem label="图标" path="icon">
            <div class="w-full flex-y-center gap-8px">
              <NInput v-model:value="formModel.icon" placeholder="请输入图标名称" class="flex-1" />
              <NButton @click="handleIconSelect">选择</NButton>
            </div>
          </NFormItem>
        </NGridItem>

        <NGridItem>
          <NFormItem label="图标预览">
            <div class="flex-y-center gap-8px">
              <SvgIcon v-if="formModel.icon" :icon="formModel.icon" class="text-24px" />
              <span v-else class="text-gray-400">暂无图标</span>
            </div>
          </NFormItem>
        </NGridItem>

        <NGridItem>
          <NFormItem label="图标类型" path="iconType">
            <NRadioGroup v-model:value="formModel.iconType">
              <NRadio value="1">Iconify图标</NRadio>
              <NRadio value="2">本地图标</NRadio>
            </NRadioGroup>
          </NFormItem>
        </NGridItem>

        <!-- 状态配置 -->
        <NGridItem :span="2">
          <div class="mb-12px mt-16px text-base font-medium">状态配置</div>
        </NGridItem>

        <NGridItem>
          <NFormItem label="菜单状态" path="status">
            <NRadioGroup v-model:value="formModel.status">
              <NRadio value="1">启用</NRadio>
              <NRadio value="0">禁用</NRadio>
            </NRadioGroup>
          </NFormItem>
        </NGridItem>

        <NGridItem>
          <NFormItem label="是否隐藏" path="hide">
            <NRadioGroup v-model:value="formModel.hide">
              <NRadio value="N">显示</NRadio>
              <NRadio value="Y">隐藏</NRadio>
            </NRadioGroup>
          </NFormItem>
        </NGridItem>

        <!-- 权限配置 -->
        <NGridItem :span="2">
          <div class="mb-12px mt-16px text-base font-medium">权限配置</div>
        </NGridItem>

        <NGridItem>
          <NFormItem label="权限标识" path="permission">
            <NInput v-model:value="formModel.permission" placeholder="请输入权限标识，如：sys:user:list" />
          </NFormItem>
        </NGridItem>

        <NGridItem>
          <NFormItem label="是否需要认证" path="requireAuth">
            <NSwitch v-model:value="formModel.requireAuth" />
          </NFormItem>
        </NGridItem>

        <NGridItem>
          <NFormItem label="是否缓存" path="keepAlive">
            <NSwitch v-model:value="formModel.keepAlive" />
          </NFormItem>
        </NGridItem>

        <!-- 其他配置 -->
        <NGridItem :span="2">
          <div class="mb-12px mt-16px text-base font-medium">其他配置</div>
        </NGridItem>

        <NGridItem :span="2">
          <NFormItem label="菜单描述" path="description">
            <NInput v-model:value="formModel.description" type="textarea" placeholder="请输入菜单描述" :rows="3" />
          </NFormItem>
        </NGridItem>
      </NGrid>
    </NForm>

    <template #footer>
      <div class="flex justify-end gap-12px">
        <NButton @click="modalVisible = false">取消</NButton>
        <NButton type="primary" @click="handleConfirm">确定</NButton>
      </div>
    </template>

    <!-- 图标选择器模态框 -->
    <IconSelectModal v-model:visible="iconSelectVisible" @confirm="handleIconConfirm" />
  </NModal>
</template>

<style scoped>
:deep(.n-form-item-label__text) {
  font-size: 13px;
}

:deep(.n-input) {
  font-size: 13px;
}

:deep(.n-select) {
  font-size: 13px;
}
</style>
