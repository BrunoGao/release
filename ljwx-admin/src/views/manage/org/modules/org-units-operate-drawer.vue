<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddOrgUnits, fetchUpdateOrgUnits } from '@/service/api';
import { getLevelAndAncestors } from '@/views/manage/org/modules/shared';
import { useDict } from '@/hooks/business/dict';
import { useAuthStore } from '@/store/modules/auth';
import { useCustomer } from '@/hooks/business/customer';

defineOptions({
  name: 'OrgUnitsOperateDrawer'
});

export type OperateType = NaiveUI.TableOperateType | 'addChild';

interface Props {
  /** the type of operation */
  operateType: OperateType;
  /** the edit row data */
  rowData?: Api.SystemManage.OrgUnits | null;
}

const props = defineProps<Props>();

interface Emits {
  (e: 'submitted'): void;
}

const emit = defineEmits<Emits>();

const visible = defineModel<boolean>('visible', {
  default: false
});

const { dictOptions } = useDict();
const authStore = useAuthStore();
const { currentCustomerId: globalCustomerId } = useCustomer();

const { formRef, validate, restoreValidation } = useNaiveForm();
const { defaultRequiredRule } = useFormRules();

// 获取当前租户ID（使用全局租户ID）
const currentCustomerId = computed(() => {
  const id = globalCustomerId.value || '0';
  console.log('[Debug Drawer] currentCustomerId:', id, 'globalCustomerId:', globalCustomerId.value);
  return id;
});

// 所有操作都是部门操作（不再区分租户和部门）
const isDeptOperation = computed(() => true);

// 判断是否选择了租户
const hasSelectedTenant = computed(() => currentCustomerId.value && currentCustomerId.value !== '0');

const title = computed(() => {
  if (props.operateType === 'addChild') {
    return $t('page.manage.orgUnits.addChildDepartment');
  }
  return props.operateType === 'add' ? $t('page.manage.orgUnits.dept.addDept') : $t('page.manage.orgUnits.dept.editDept');
});

type Model = Api.SystemManage.OrgUnitsEdit;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    id: '0',
    parentId: '0', // 改为字符串避免精度丢失
    name: '',
    code: '',
    abbr: '',
    level: 1,
    ancestors: '0',
    description: '',
    sort: 1,
    status: '1'
  };
}

type RuleKey = Exclude<keyof Model, 'id' | 'parentId' | 'abbr' | 'level' | 'ancestors' | 'description' | 'i18nKey' | 'sort'>;

const rules: Record<RuleKey, App.Global.FormRule> = {
  code: defaultRequiredRule,
  name: defaultRequiredRule,
  status: defaultRequiredRule
};

function handleInitModel() {
  Object.assign(model, createDefaultModel());

  if (!props.rowData && props.operateType === 'edit') return;

  if (props.operateType === 'edit' && props.rowData) {
    // 编辑现有记录
    Object.assign(model, props.rowData);
    console.log('[Debug Drawer] Edit mode, model:', model);
  } else if (props.operateType === 'add') {
    // 顶级新增：在租户下添加一级部门
    if (hasSelectedTenant.value) {
      model.parentId = currentCustomerId.value;  // 保持字符串格式避免精度丢失
      model.level = 1; // 租户是 level 0，一级部门是 level 1
      model.ancestors = `0,${currentCustomerId.value}`;
      console.log('[Debug Drawer] Add top-level department, model:', {
        parentId: model.parentId,
        level: model.level,
        ancestors: model.ancestors
      });
    }
  } else if (props.operateType === 'addChild' && props.rowData) {
    // 子级新增：在现有部门下添加子部门
    const { id } = props.rowData;
    const { level, ancestors } = getLevelAndAncestors(props.rowData);
    Object.assign(model, { 
      parentId: id,    // 保持字符串格式避免精度丢失
      level, 
      ancestors 
    });
    console.log('[Debug Drawer] Add child department, parent:', props.rowData);
    console.log('[Debug Drawer] Calculated hierarchy:', { parentId: id, level, ancestors });
    console.log('[Debug Drawer] Final model:', model);
  }
}

function closeDrawer() {
  visible.value = false;
}

const isAdd = computed(() => props.operateType === 'add' || props.operateType === 'addChild');

async function handleSubmit() {
  await validate();
  console.log('[Debug Drawer] handleSubmit called, model:', model);
  const func = isAdd.value ? fetchAddOrgUnits : fetchUpdateOrgUnits;
  const { error, data } = await func(model);
  if (!error && data) {
    window.$message?.success(isAdd.value ? $t('common.addSuccess') : $t('common.updateSuccess'));
    closeDrawer();
    emit('submitted');
  }
}

watch(visible, () => {
  if (visible.value) {
    handleInitModel();
    restoreValidation();
  }
});
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="360">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="model" :rules="rules">
        <NFormItem :label="isDeptOperation ? $t('page.manage.orgUnits.dept.name') : $t('page.manage.orgUnits.name')" path="name">
          <NInput
            v-model:value="model.name"
            :placeholder="isDeptOperation ? $t('page.manage.orgUnits.dept.form.name') : $t('page.manage.orgUnits.form.name')"
          />
        </NFormItem>
        <NFormItem :label="isDeptOperation ? $t('page.manage.orgUnits.dept.code') : $t('page.manage.orgUnits.code')" path="code">
          <NInput
            v-model:value="model.code"
            :placeholder="isDeptOperation ? $t('page.manage.orgUnits.dept.form.code') : $t('page.manage.orgUnits.form.code')"
          />
        </NFormItem>
        <NFormItem :label="isDeptOperation ? $t('page.manage.orgUnits.dept.abbr') : $t('page.manage.orgUnits.abbr')" path="abbr">
          <NInput
            v-model:value="model.abbr"
            :placeholder="isDeptOperation ? $t('page.manage.orgUnits.dept.form.abbr') : $t('page.manage.orgUnits.form.abbr')"
          />
        </NFormItem>
        <NFormItem :label="isDeptOperation ? $t('page.manage.orgUnits.dept.status') : $t('page.manage.orgUnits.status')" path="status">
          <NRadioGroup v-model:value="model.status">
            <NRadio v-for="item in dictOptions('status')" :key="item.value" :value="item.value" :label="item.label" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.manage.orgUnits.sort')" path="sort">
          <NInputNumber v-model:value="model.sort" :placeholder="$t('page.manage.orgUnits.form.sort')" />
        </NFormItem>
        <NFormItem :label="isDeptOperation ? $t('page.manage.orgUnits.dept.description') : $t('page.manage.orgUnits.description')" path="description">
          <NInput
            v-model:value="model.description"
            :placeholder="isDeptOperation ? $t('page.manage.orgUnits.dept.form.description') : $t('page.manage.orgUnits.form.description')"
          />
        </NFormItem>
      </NForm>
      <template #footer>
        <div style="padding: 16px; background: #f0f0f0; border-top: 1px solid #d9d9d9;">
          <NSpace justify="end">
            <NButton quaternary @click="closeDrawer">{{ $t('common.cancel') }}</NButton>
            <NButton type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</NButton>
          </NSpace>
        </div>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>
