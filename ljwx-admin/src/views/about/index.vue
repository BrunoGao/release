<script setup lang="ts">
import { computed } from 'vue';
import { $t } from '@/locales';
import { useAppStore } from '@/store/modules/app';
import pkg from '~/package.json';

const appStore = useAppStore();

const column = computed(() => (appStore.isMobile ? 1 : 2));

interface PkgJson {
  name: string;
  version: string;
  dependencies: PkgVersionInfo[];
  devDependencies: PkgVersionInfo[];
}

interface PkgVersionInfo {
  name: string;
  version: string;
}

const { name, version, dependencies, devDependencies } = pkg;

function transformVersionData(tuple: [string, string]): PkgVersionInfo {
  const [$name, $version] = tuple;
  return {
    name: $name,
    version: $version
  };
}

const pkgJson: PkgJson = {
  name,
  version,
  dependencies: Object.entries(dependencies).map(item => transformVersionData(item)),
  devDependencies: Object.entries(devDependencies).map(item => transformVersionData(item))
};

const latestBuildTime = BUILD_TIME;

// 系统核心功能特性
const systemFeatures = [
  { name: '智能设备监测', description: '支持多种智能穿戴设备实时数据监测' },
  { name: '健康数据分析', description: '心率、血压、血氧等多维度健康指标分析' },
  { name: '告警管理', description: '智能告警规则配置和微信消息推送' },
  { name: '多租户架构', description: '完整的租户隔离和权限管理体系' },
  { name: '大屏可视化', description: 'Python Flask 驱动的实时数据大屏展示' },
  { name: '移动端支持', description: '跨平台移动应用和手表应用开发' }
];

// 技术栈信息
const techStack = {
  frontend: [
    { name: 'Vue 3', version: '3.4+', description: '现代化响应式前端框架' },
    { name: 'TypeScript', version: '5.0+', description: '类型安全的JavaScript超集' },
    { name: 'Vite', version: '5.0+', description: '极速前端构建工具' },
    { name: 'Naive UI', version: '2.39+', description: '现代化Vue 3组件库' },
    { name: 'UnoCSS', version: '0.58+', description: '即时按需CSS引擎' }
  ],
  backend: [
    { name: 'Spring Boot', version: '3.3.2', description: 'Java企业级应用框架' },
    { name: 'MyBatis Plus', version: '3.5+', description: 'MyBatis增强工具' },
    { name: 'SaToken', version: '1.37+', description: '轻量级权限认证框架' },
    { name: 'MySQL', version: '8.0+', description: '关系型数据库' },
    { name: 'Redis', version: '7.0+', description: '内存数据库和缓存' }
  ]
};
</script>

<template>
  <NSpace vertical :size="16">
    <NCard :title="$t('page.about.title')" :bordered="false" size="small" segmented class="card-wrapper">
      <p>{{ $t('page.about.introduction') }}</p>
    </NCard>

    <NCard :title="$t('page.about.projectInfo.title')" :bordered="false" size="small" segmented class="card-wrapper">
      <NDescriptions label-placement="left" bordered size="small" :column="column">
        <NDescriptionsItem :label="$t('page.about.projectInfo.version')">
          <NTag type="primary">{{ pkgJson.version }}</NTag>
        </NDescriptionsItem>
        <NDescriptionsItem :label="$t('page.about.projectInfo.latestBuildTime')">
          <NTag type="primary">{{ latestBuildTime }}</NTag>
        </NDescriptionsItem>
        <NDescriptionsItem :label="$t('page.about.projectInfo.githubLink')">
          <a class="text-primary" :href="pkg.homepage" target="_blank" rel="noopener noreferrer">
            {{ $t('page.about.projectInfo.githubLink') }}
          </a>
        </NDescriptionsItem>
        <NDescriptionsItem :label="$t('page.about.projectInfo.previewLink')">
          <a class="text-primary" :href="pkg.website || pkg.homepage" target="_blank" rel="noopener noreferrer">
            {{ $t('page.about.projectInfo.previewLink') }}
          </a>
        </NDescriptionsItem>
      </NDescriptions>
    </NCard>

    <NCard title="系统核心功能" :bordered="false" size="small" segmented class="card-wrapper">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="feature in systemFeatures" :key="feature.name" class="p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
          <div class="flex items-center gap-2 mb-2">
            <NIcon size="16" color="#18a058">
              <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
            </NIcon>
            <span class="font-medium text-primary">{{ feature.name }}</span>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-300">{{ feature.description }}</p>
        </div>
      </div>
    </NCard>

    <NCard title="前端技术栈" :bordered="false" size="small" segmented class="card-wrapper">
      <NDescriptions label-placement="left" bordered size="small" :column="column">
        <NDescriptionsItem v-for="tech in techStack.frontend" :key="tech.name" :label="tech.name">
          <div class="flex flex-col gap-1">
            <NTag type="info" size="small">{{ tech.version }}</NTag>
            <span class="text-xs text-gray-500">{{ tech.description }}</span>
          </div>
        </NDescriptionsItem>
      </NDescriptions>
    </NCard>

    <NCard title="后端技术栈" :bordered="false" size="small" segmented class="card-wrapper">
      <NDescriptions label-placement="left" bordered size="small" :column="column">
        <NDescriptionsItem v-for="tech in techStack.backend" :key="tech.name" :label="tech.name">
          <div class="flex flex-col gap-1">
            <NTag type="success" size="small">{{ tech.version }}</NTag>
            <span class="text-xs text-gray-500">{{ tech.description }}</span>
          </div>
        </NDescriptionsItem>
      </NDescriptions>
    </NCard>

    <NCard :title="$t('page.about.prdDep')" :bordered="false" size="small" segmented class="card-wrapper">
      <NDescriptions label-placement="left" bordered size="small" :column="column">
        <NDescriptionsItem v-for="item in pkgJson.dependencies" :key="item.name" :label="item.name">
          {{ item.version }}
        </NDescriptionsItem>
      </NDescriptions>
    </NCard>

    <NCard :title="$t('page.about.devDep')" :bordered="false" size="small" segmented class="card-wrapper">
      <NDescriptions label-placement="left" bordered size="small" :column="column">
        <NDescriptionsItem v-for="item in pkgJson.devDependencies" :key="item.name" :label="item.name">
          {{ item.version }}
        </NDescriptionsItem>
      </NDescriptions>
    </NCard>
  </NSpace>
</template>

<style scoped></style>
