<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddAlertConfigWechat, fetchUpdateAlertConfigWechatInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import { useAuthStore } from '@/store/modules/auth';

defineOptions({
  name: 'AlertConfigWechatOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Health.AlertConfigWechat | null;
  /** wechat type: enterprise or official */
  type?: string;
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
const { formRef, validate, restoreValidation } = useNaiveForm();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;

const title = computed(() => {
  const typeText = props.type === 'enterprise' ? '企业微信' : '微信公众号';
  const operationText = props.operateType === 'add' ? '新增' : '编辑';
  return `${operationText}${typeText}配置`;
});

type Model = Api.Health.AlertConfigWechat;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    type: props.type || 'enterprise',
    customerId: customerId,
    corpId: '',
    agentId: '',
    secret: '',
    appid: '',
    appsecret: '',
    templateId: '',
    enabled: true,
    createUser: '',
    createTime: '',
    id: '',
    updateUser: '',
    updateTime: ''
  };
}

function handleInitModel() {
  Object.assign(model, createDefaultModel());

  if (!props.rowData) return;

  if (props.operateType === 'edit' && props.rowData) {
    Object.assign(model, props.rowData);
  }
}

function closeDrawer() {
  visible.value = false;
}

const isAdd = computed(() => props.operateType === 'add');

async function handleSubmit() {
  await validate();
  const func = isAdd.value ? fetchAddAlertConfigWechat : fetchUpdateAlertConfigWechatInfo;
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
  <NDrawer v-model:show="visible" display-directive="show" :width="480">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="model" label-placement="left" :label-width="100">
        <!-- 企业微信配置 -->
        <template v-if="props.type === 'enterprise'">
          <NFormItem label="企业ID" path="corpId" required>
            <NInput v-model:value="model.corpId" placeholder="请输入企业微信企业ID" />
          </NFormItem>
          <NFormItem label="应用ID" path="agentId" required>
            <NInput v-model:value="model.agentId" placeholder="请输入企业微信应用ID" />
          </NFormItem>
          <NFormItem label="应用Secret" path="secret" required>
            <NInput v-model:value="model.secret" type="password" placeholder="请输入企业微信应用Secret" />
          </NFormItem>
        </template>
        
        <!-- 微信公众号配置 -->
        <template v-else>
          <NFormItem label="AppID" path="appid" required>
            <NInput v-model:value="model.appid" placeholder="请输入微信公众号AppID" />
          </NFormItem>
          <NFormItem label="AppSecret" path="appsecret" required>
            <NInput v-model:value="model.appsecret" type="password" placeholder="请输入微信公众号AppSecret" />
          </NFormItem>
        </template>
        
        <!-- 通用配置 -->
        <NFormItem label="模板ID" path="templateId" required>
          <NInput v-model:value="model.templateId" placeholder="请输入消息模板ID" />
        </NFormItem>
        
        <NFormItem label="启用状态" path="enabled">
          <NSwitch v-model:value="model.enabled" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace :size="16">
          <NButton @click="closeDrawer">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>
