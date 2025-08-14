<script setup lang="ts">
import { watch } from 'vue';
import { $t } from '@/locales';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'TAlertRulesSearch'
});

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Health.AlertRulesSearchParams>('model', { required: true });

const { dictOptions } = useDict();

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
watch(
  () => [model.value.ruleType, model.value.physicalSign],
  ([ruleType_val, physicalSign_val]) => {
    if (ruleType_val === 'all') model.value.ruleType = null;
    if (physicalSign_val === 'all') model.value.physicalSign = null;
  }
);
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NForm :model="model" label-placement="left" :show-feedback="false" :label-width="80">
      <NGrid responsive="screen" item-responsive :x-gap="8" :y-gap="8" cols="1 s:1 m:5 l:5 xl:5 2xl:5">
        <NGridItem span="4">
          <NGrid responsive="screen" item-responsive :x-gap="8">
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.alert.rules.ruleType')" path="ruleType">
              <NSelect
                v-model:value="model.ruleType"
                size="small"
                :placeholder="$t('page.health.alert.rules.form.ruleType')"
                :options="[{ label: '全部', value: 'all' }, ...dictOptions('alert_type')]"
                clearable
              />
            </NFormItemGi>
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.alert.rules.physicalSign')" path="physicalSign">
              <NSelect
                v-model:value="model.physicalSign"
                size="small"
                :placeholder="$t('page.health.alert.rules.form.physicalSign')"
                :options="[{ label: '全部', value: 'all' }, ...dictOptions('health_data_type')]"
                clearable
              />
            </NFormItemGi>
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.alert.rules.thresholdMin')" path="thresholdMin">
              <NInput v-model:value="model.thresholdMin" size="small" :placeholder="$t('page.health.alert.rules.form.thresholdMin')" />
            </NFormItemGi>
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.alert.rules.thresholdMax')" path="thresholdMax">
              <NInput v-model:value="model.thresholdMax" size="small" :placeholder="$t('page.health.alert.rules.form.thresholdMax')" />
            </NFormItemGi>
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.alert.rules.trendDuration')" path="trendDuration">
              <NInput v-model:value="model.trendDuration" size="small" :placeholder="$t('page.health.alert.rules.form.trendDuration')" />
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
