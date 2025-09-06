<script setup lang="ts">
import { ref, toRaw, watch } from 'vue';
import { $t } from '@/locales';
import { useDict } from '@/hooks/business/dict';
import { handleBindUsersByOrgId } from '@/utils/deviceUtils';

defineOptions({
  name: 'Tdevice.messageSearch'
});

interface Props {
  orgUnitsTree: Array<any>;
}

const props = defineProps<Props>();

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Health.DeviceMessageSearchParams>('model', { required: true });

const { dictOptions } = useDict();

// 添加一个新的 ref 来存储完整的部门信息

// Watch for changes in model.value.departmentName

const userOptions = ref<Array<any>>([]);
watch(
  () => model.value.orgId,
  async (newValue, oldValue) => {
    // console.log('search props.orgUnitsTree', props.orgUnitsTree);
    console.log('model.departmentName changed from', oldValue, 'to', newValue);
    if (newValue) {
      const result = await handleBindUsersByOrgId(newValue);
      console.log('handleBindUsers.result', result);
      if (Array.isArray(result)) {
        userOptions.value = result;
      } else {
        console.error('Failed to fetch user options');
      }
    }
  }
);

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NForm :model="model" label-placement="left" :show-feedback="false" :label-width="80">
      <NGrid responsive="screen" item-responsive :x-gap="8" :y-gap="8" cols="1 s:1 m:5 l:5 xl:5 2xl:5">
        <NGridItem span="4">
          <NGrid responsive="screen" item-responsive :x-gap="8">
            <NFormItemGi span="24 s:8 m:12" :label="$t('page.health.device.message.departmentName')" path="orgId">
              <NTreeSelect
                v-model:value="model.orgId"
                size="small"
                checkable
                filterable
                key-field="id"
                label-field="name"
                default-expand-all
                :max-tag-count="7"
                :placeholder="$t('page.health.device.message.form.departmentName')"
                :options="props.orgUnitsTree"
              />
            </NFormItemGi>
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.message.userName')" path="userName">
              <NSelect
                v-model:value="model.userId"
                size="small"
                :placeholder="$t('page.health.device.message.form.userName')"
                :options="userOptions"
              />
            </NFormItemGi>

            <NFormItemGi span="24 s:8 m:6" :label="$t('page.job.messageStatus')" path="messageStatus">
              <NSelect
                v-model:value="model.messageStatus"
                size="small"
                :placeholder="$t('page.job.form.messageStatus')"
                :options="dictOptions('message_status')"
              />
            </NFormItemGi>
          </NGrid>
        </NGridItem>
        <NGridItem>
          <NFormItemGi span="24 s:8 m:6">
            <NSpace class="w-full" justify="end">
              <NButton type="primary" ghost @click="search">
                <template #icon>
                  <icon-ic-round-search class="text-icon" />
                </template>
                {{ $t('common.search') }}
              </NButton>
              <NButton quaternary @click="reset">
                <template #icon>
                  <icon-ic-round-refresh class="text-icon" />
                </template>
                {{ $t('common.reset') }}
              </NButton>
            </NSpace>
          </NFormItemGi>
        </NGridItem>
      </NGrid>
    </NForm>
  </NCard>
</template>

<style scoped></style>
