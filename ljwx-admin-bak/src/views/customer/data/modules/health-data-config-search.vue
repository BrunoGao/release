<script setup lang="ts">
import { $t } from '@/locales';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'THealthDataConfigSearch'
});

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}
interface Props {
  orgUnitsName: Array<any>;
}
const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const model = defineModel<Api.Customer.HealthDataConfigSearchParams>('model', { required: true });

const { dictOptions } = useDict();

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
            <NFormItemGi span="24 s:8 m:12" :label="$t('page.customer.config.customerName')" path="departmentName">
              <NSelect
                v-model:value="model.customerId"
                size="small"
                :placeholder="$t('page.customer.config.customerName')"
                :options="props.orgUnitsName"
              />
            </NFormItemGi>
          </NGrid>
          <NGrid responsive="screen" item-responsive :x-gap="8">
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.customer.healthDataConfig.dataType')" path="dataType">
              <NInput v-model:value="model.dataType" size="small" :placeholder="$t('page.customer.healthDataConfig.form.dataType')" />
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
