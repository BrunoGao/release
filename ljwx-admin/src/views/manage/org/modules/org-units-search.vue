<script setup lang="ts">
import { computed } from 'vue';
import { $t } from '@/locales';
import { useDict } from '@/hooks/business/dict';
import { useAuthStore } from '@/store/modules/auth';

defineOptions({
  name: 'OrgUnitsSearch'
});

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.SystemManage.OrgUnitsSearchParams>('model', { required: true });

const { dictOptions } = useDict();
const authStore = useAuthStore();

// 判断是否是超级管理员（admin用户，可以管理所有租户）
const isAdmin = computed(() => {
  return authStore.userInfo?.userName === 'admin';
});

// 动态标签，管理员看到的是租户，普通用户看到的是部门
const nameLabel = computed(() => {
  return isAdmin.value ? $t('page.manage.orgUnits.name') : $t('page.manage.orgUnits.dept.name');
});

const namePlaceholder = computed(() => {
  return isAdmin.value ? $t('page.manage.orgUnits.form.name') : $t('page.manage.orgUnits.dept.form.name');
});

const statusLabel = computed(() => {
  return isAdmin.value ? $t('page.manage.orgUnits.status') : $t('page.manage.orgUnits.dept.status');
});

const statusPlaceholder = computed(() => {
  return isAdmin.value ? $t('page.manage.orgUnits.form.status') : $t('page.manage.orgUnits.dept.form.status');
});

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
            <NFormItemGi span="24 s:8 m:6" :label="nameLabel" path="roleName">
              <NInput v-model:value="model.name" size="small" :placeholder="namePlaceholder" />
            </NFormItemGi>

            <NFormItemGi span="24 s:8 m:6" :label="statusLabel" path="status">
              <NSelect v-model:value="model.status" size="small" :placeholder="statusPlaceholder" :options="dictOptions('status')" clearable />
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
