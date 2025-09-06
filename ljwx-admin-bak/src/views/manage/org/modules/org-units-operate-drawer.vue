<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddOrgUnits, fetchUpdateOrgUnits } from '@/service/api';
import { getLevelAndAncestors } from '@/views/manage/org/modules/shared';
import { useDict } from '@/hooks/business/dict';
import { useAuthStore } from '@/store/modules/auth';

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

const { formRef, validate, restoreValidation } = useNaiveForm();
const { defaultRequiredRule } = useFormRules();

// 判断是否是超级管理员（admin用户，可以管理所有租户）
const isAdmin = computed(() => {
  return authStore.userInfo?.userName === 'admin';
});

// 判断当前操作是否为租户操作（只有管理员创建顶级组织才算租户）
const isTenantOperation = computed(() => {
  return isAdmin.value && (props.operateType === 'add' || (props.operateType === 'edit' && props.rowData?.level === 1));
});

// 判断是否为部门操作
const isDeptOperation = computed(() => {
  return !isTenantOperation.value;
});

const title = computed(() => {
  if (props.operateType === 'addChild') {
    return $t('page.manage.orgUnits.addChildOrgUnits');
  }

  if (isDeptOperation.value) {
    return props.operateType === 'add' ? $t('page.manage.orgUnits.dept.addDept') : $t('page.manage.orgUnits.dept.editDept');
  }
  return props.operateType === 'add' ? $t('page.manage.orgUnits.addOrgUnits') : $t('page.manage.orgUnits.editOrgUnits');
});

type Model = Api.SystemManage.OrgUnitsEdit;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    id: '0',
    parentId: 0,
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

  // 如果不是管理员，且是新增操作，设置parentId为当前用户的部门ID
  if (!isAdmin.value && props.operateType === 'add') {
    const currentUserOrgId = authStore.userInfo?.customerId;
    if (currentUserOrgId) {
      model.parentId = Number(currentUserOrgId);
      model.level = 2; // 假设当前用户部门是level 1，新建的部门就是level 2
      model.ancestors = `0,${currentUserOrgId}`;
    }
  }

  if (!props.rowData) return;

  if (props.operateType === 'edit' && props.rowData) {
    Object.assign(model, props.rowData);
  }

  if (props.operateType === 'addChild') {
    const { id } = props.rowData;
    const { level, ancestors } = getLevelAndAncestors(props.rowData);
    Object.assign(model, { parentId: id, level, ancestors });
  }
}

function closeDrawer() {
  visible.value = false;
}

const isAdd = computed(() => props.operateType === 'add' || props.operateType === 'addChild');

async function handleSubmit() {
  await validate();
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
        <NSpace>
          <NButton quaternary @click="closeDrawer">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>
