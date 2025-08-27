<script setup lang="ts">
import { computed, watch } from 'vue';
import { $t } from '@/locales';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'AlertConfigWechatSearch'
});

interface Props {
  type?: string;
}

const props = defineProps<Props>();

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Health.AlertConfigWechatSearchParams>('model', { required: true });

// 监听props.type变化，自动设置model中的type字段
watch(() => props.type, (newType) => {
  if (newType) {
    model.value.type = newType;
  }
}, { immediate: true });

const { dictOptions } = useDict();

// 计算属性处理条件字段绑定
const searchValue = computed({
  get() {
    return props.type === 'enterprise' ? model.value.corpId : model.value.appid;
  },
  set(value: string) {
    if (props.type === 'enterprise') {
      model.value.corpId = value;
    } else {
      model.value.appid = value;
    }
  }
});

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" class="card-wrapper">
    <NForm ref="queryFormRef" :model="model" label-placement="left" :label-width="80">
      <NGrid responsive="screen" item-responsive>
        <NFormItemGi span="24 s:12 m:6" :label="props.type === 'enterprise' ? '企业ID' : 'AppID'" path="corpId" class="pr-24px">
          <NInput 
            v-model:value="searchValue" 
            :placeholder="props.type === 'enterprise' ? '请输入企业ID' : '请输入AppID'" 
          />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" label="模板ID" path="templateId" class="pr-24px">
          <NInput v-model:value="model.templateId" placeholder="请输入模板ID" />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" label="启用状态" path="enabled" class="pr-24px">
          <NSelect
            v-model:value="model.enabled"
            placeholder="请选择启用状态"
            clearable
            :options="[
              { label: '启用', value: true },
              { label: '禁用', value: false }
            ]"
          />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" class="pr-24px">
          <NSpace class="w-full" justify="end">
            <NButton @click="reset">
              <template #icon>
                <icon-ic-round-refresh class="text-icon" />
              </template>
              {{ $t('common.reset') }}
            </NButton>
            <NButton type="primary" ghost @click="search">
              <template #icon>
                <icon-ic-round-search class="text-icon" />
              </template>
              {{ $t('common.search') }}
            </NButton>
          </NSpace>
        </NFormItemGi>
      </NGrid>
    </NForm>
  </NCard>
</template>

<style scoped>
.card-wrapper {
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}
</style>
