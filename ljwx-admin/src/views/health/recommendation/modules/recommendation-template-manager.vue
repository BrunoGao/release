<script setup lang="tsx">
import { ref, computed, h } from 'vue';
import { 
  NModal, 
  NCard, 
  NDataTable, 
  NButton, 
  NTag, 
  NSpace,
  NPopconfirm,
  NAlert,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NDivider,
  useMessage
} from 'naive-ui';

defineOptions({
  name: 'RecommendationTemplateManager'
});

const emit = defineEmits<{
  (e: 'template-updated'): void;
}>();

const visible = defineModel<boolean>('visible', { default: false });
const message = useMessage();

// 模板数据
const templates = ref([
  {
    id: 'T001',
    name: '睡眠改善模板',
    type: 'lifestyle',
    category: '生活方式',
    title: '改善睡眠质量建议',
    content: '建议您调整作息时间，每天保证7-8小时的睡眠，睡前1小时避免使用电子设备，创造安静舒适的睡眠环境。可以尝试睡前进行轻松的伸展运动或冥想练习。',
    tags: ['睡眠', '作息', '生活习惯'],
    usageCount: 156,
    effectiveness: 4.2,
    status: 'active',
    createdAt: '2024-01-15',
    updatedAt: '2024-01-20'
  },
  {
    id: 'T002',
    name: '有氧运动计划模板',
    type: 'exercise',
    category: '运动健身',
    title: '个人有氧运动计划建议',
    content: '建议每周进行3-4次中等强度有氧运动，如快走、游泳或骑行，每次30-45分钟。运动前进行5-10分钟热身，运动后进行拉伸放松。根据个人体质逐步增加运动强度。',
    tags: ['有氧运动', '运动计划', '健身'],
    usageCount: 203,
    effectiveness: 4.5,
    status: 'active',
    createdAt: '2024-01-10',
    updatedAt: '2024-01-18'
  },
  {
    id: 'T003',
    name: '营养饮食指导模板',
    type: 'nutrition',
    category: '营养饮食',
    title: '健康饮食调理建议',
    content: '建议增加新鲜蔬菜水果摄入，每天至少5种不同颜色的果蔬。减少加工食品和高盐食物，控制油脂摄入。保持饮食规律，三餐定时定量，避免暴饮暴食。',
    tags: ['营养', '饮食', '健康食谱'],
    usageCount: 89,
    effectiveness: 4.1,
    status: 'active',
    createdAt: '2024-01-12',
    updatedAt: '2024-01-19'
  },
  {
    id: 'T004',
    name: '压力管理模板',
    type: 'mental',
    category: '心理健康',
    title: '压力管理与心理调适建议',
    content: '建议学习和练习放松技巧，如深呼吸、渐进式肌肉放松或正念冥想。保持工作与生活的平衡，适当参与社交活动。如压力持续严重，建议寻求专业心理咨询。',
    tags: ['压力管理', '心理健康', '放松技巧'],
    usageCount: 134,
    effectiveness: 4.3,
    status: 'active',
    createdAt: '2024-01-08',
    updatedAt: '2024-01-21'
  },
  {
    id: 'T005',
    name: '心血管保健模板',
    type: 'medical',
    category: '医疗建议',
    title: '心血管健康维护建议',
    content: '建议定期监测血压和心率，保持适量的有氧运动。戒烟限酒，减少饱和脂肪摄入。如出现胸闷、心悸等症状，请及时就医咨询专业医生。',
    tags: ['心血管', '血压', '医疗保健'],
    usageCount: 67,
    effectiveness: 4.4,
    status: 'draft',
    createdAt: '2024-01-16',
    updatedAt: '2024-01-16'
  }
]);

const editingTemplate = ref(null);
const isEditing = ref(false);
const editForm = ref({
  id: '',
  name: '',
  type: 'lifestyle',
  title: '',
  content: '',
  tags: []
});

// 模板类型选项
const typeOptions = [
  { label: '生活方式', value: 'lifestyle' },
  { label: '运动健身', value: 'exercise' },
  { label: '营养饮食', value: 'nutrition' },
  { label: '医疗建议', value: 'medical' },
  { label: '心理健康', value: 'mental' }
];

// 表格列定义
const columns = [
  {
    key: 'name',
    title: '模板名称',
    width: 180,
    render: (row: any) => (
      <div>
        <div class="font-medium">{row.name}</div>
        <div class="text-xs text-gray-500">{row.id}</div>
      </div>
    )
  },
  {
    key: 'category',
    title: '类别',
    width: 100,
    render: (row: any) => (
      <NTag type="info" size="small">{row.category}</NTag>
    )
  },
  {
    key: 'title',
    title: '建议标题',
    width: 200,
    ellipsis: {
      tooltip: true
    }
  },
  {
    key: 'tags',
    title: '标签',
    width: 150,
    render: (row: any) => (
      <NSpace size="small">
        {row.tags.slice(0, 2).map((tag: string) => (
          <NTag key={tag} type="default" size="small">{tag}</NTag>
        ))}
        {row.tags.length > 2 && (
          <NTag type="default" size="small">+{row.tags.length - 2}</NTag>
        )}
      </NSpace>
    )
  },
  {
    key: 'usageCount',
    title: '使用次数',
    width: 100,
    align: 'center'
  },
  {
    key: 'effectiveness',
    title: '有效性',
    width: 100,
    align: 'center',
    render: (row: any) => `${row.effectiveness}/5`
  },
  {
    key: 'status',
    title: '状态',
    width: 100,
    align: 'center',
    render: (row: any) => {
      const statusMap = {
        active: { type: 'success', text: '启用' },
        draft: { type: 'warning', text: '草稿' },
        disabled: { type: 'error', text: '禁用' }
      } as const;
      const status = statusMap[row.status as keyof typeof statusMap];
      return h(NTag, { type: status.type, size: 'small' }, () => status.text);
    }
  },
  {
    key: 'updatedAt',
    title: '更新时间',
    width: 120
  },
  {
    key: 'operate',
    title: '操作',
    width: 200,
    render: (row: any) => (
      <NSpace size="small">
        <NButton 
          size="small" 
          type="info" 
          quaternary 
          onClick={() => viewTemplate(row)}
        >
          预览
        </NButton>
        <NButton 
          size="small" 
          type="primary" 
          quaternary 
          onClick={() => editTemplate(row)}
        >
          编辑
        </NButton>
        <NButton 
          size="small" 
          type={row.status === 'active' ? 'warning' : 'success'}
          quaternary 
          onClick={() => toggleStatus(row)}
        >
          {row.status === 'active' ? '禁用' : '启用'}
        </NButton>
        <NPopconfirm onPositiveClick={() => deleteTemplate(row.id)}>
          {{
            default: () => '确认删除此模板？',
            trigger: () => (
              <NButton size="small" type="error" quaternary>
                删除
              </NButton>
            )
          }}
        </NPopconfirm>
      </NSpace>
    )
  }
];

const templateStats = computed(() => {
  return {
    total: templates.value.length,
    active: templates.value.filter(t => t.status === 'active').length,
    draft: templates.value.filter(t => t.status === 'draft').length,
    avgEffectiveness: templates.value.reduce((acc, t) => acc + t.effectiveness, 0) / templates.value.length
  };
});

function createNewTemplate() {
  isEditing.value = true;
  editForm.value = {
    id: '',
    name: '',
    type: 'lifestyle',
    title: '',
    content: '',
    tags: []
  };
}

function editTemplate(template: any) {
  isEditing.value = true;
  editingTemplate.value = template;
  editForm.value = {
    id: template.id,
    name: template.name,
    type: template.type,
    title: template.title,
    content: template.content,
    tags: [...template.tags]
  };
}

function viewTemplate(template: any) {
  message.info(`查看模板: ${template.name}`);
}

function toggleStatus(template: any) {
  const newStatus = template.status === 'active' ? 'disabled' : 'active';
  const index = templates.value.findIndex(t => t.id === template.id);
  if (index > -1) {
    templates.value[index].status = newStatus;
    message.success(`模板已${newStatus === 'active' ? '启用' : '禁用'}`);
    emit('template-updated');
  }
}

function deleteTemplate(id: string) {
  const index = templates.value.findIndex(t => t.id === id);
  if (index > -1) {
    templates.value.splice(index, 1);
    message.success('模板已删除');
    emit('template-updated');
  }
}

function saveTemplate() {
  if (!editForm.value.name || !editForm.value.title || !editForm.value.content) {
    message.error('请填写完整的模板信息');
    return;
  }

  if (editForm.value.id) {
    // 编辑现有模板
    const index = templates.value.findIndex(t => t.id === editForm.value.id);
    if (index > -1) {
      Object.assign(templates.value[index], {
        name: editForm.value.name,
        type: editForm.value.type,
        title: editForm.value.title,
        content: editForm.value.content,
        tags: editForm.value.tags,
        category: typeOptions.find(opt => opt.value === editForm.value.type)?.label,
        updatedAt: new Date().toISOString().split('T')[0]
      });
      message.success('模板更新成功');
    }
  } else {
    // 创建新模板
    const newTemplate = {
      id: `T${String(templates.value.length + 1).padStart(3, '0')}`,
      name: editForm.value.name,
      type: editForm.value.type,
      category: typeOptions.find(opt => opt.value === editForm.value.type)?.label,
      title: editForm.value.title,
      content: editForm.value.content,
      tags: editForm.value.tags,
      usageCount: 0,
      effectiveness: 0,
      status: 'draft',
      createdAt: new Date().toISOString().split('T')[0],
      updatedAt: new Date().toISOString().split('T')[0]
    };
    templates.value.push(newTemplate);
    message.success('模板创建成功');
  }

  isEditing.value = false;
  editingTemplate.value = null;
  emit('template-updated');
}

function cancelEdit() {
  isEditing.value = false;
  editingTemplate.value = null;
}
</script>

<template>
  <NModal v-model:show="visible" preset="card" title="建议模板管理" class="w-full max-w-7xl">
    <template #header-extra>
      <NButton type="primary" @click="createNewTemplate">
        <template #icon>
          <div class="i-mdi:plus" />
        </template>
        创建模板
      </NButton>
    </template>

    <div class="space-y-4">
      <!-- 统计卡片 -->
      <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <NCard size="small">
          <div class="text-center">
            <div class="text-2xl font-bold text-primary">{{ templateStats.total }}</div>
            <div class="text-sm text-gray-600">总模板数</div>
          </div>
        </NCard>
        
        <NCard size="small">
          <div class="text-center">
            <div class="text-2xl font-bold text-success">{{ templateStats.active }}</div>
            <div class="text-sm text-gray-600">启用模板</div>
          </div>
        </NCard>
        
        <NCard size="small">
          <div class="text-center">
            <div class="text-2xl font-bold text-warning">{{ templateStats.draft }}</div>
            <div class="text-sm text-gray-600">草稿模板</div>
          </div>
        </NCard>
        
        <NCard size="small">
          <div class="text-center">
            <div class="text-2xl font-bold text-info">{{ templateStats.avgEffectiveness.toFixed(1) }}/5</div>
            <div class="text-sm text-gray-600">平均有效性</div>
          </div>
        </NCard>
      </div>

      <!-- 模板列表 -->
      <NCard v-if="!isEditing">
        <template #header>
          <span class="text-lg font-semibold">模板列表</span>
        </template>
        
        <NDataTable
          :data="templates"
          :columns="columns"
          :row-key="(row: any) => row.id"
          size="small"
          striped
        />
      </NCard>

      <!-- 编辑模板表单 -->
      <NCard v-if="isEditing" title="编辑模板">
        <NForm :model="editForm" label-placement="top">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <NFormItem label="模板名称" required>
              <NInput 
                v-model:value="editForm.name" 
                placeholder="请输入模板名称"
                maxlength="50"
                show-count
              />
            </NFormItem>

            <NFormItem label="模板类型" required>
              <NSelect 
                v-model:value="editForm.type" 
                :options="typeOptions" 
                placeholder="请选择模板类型" 
              />
            </NFormItem>
          </div>

          <NFormItem label="建议标题" required>
            <NInput 
              v-model:value="editForm.title" 
              placeholder="请输入建议标题"
              maxlength="100"
              show-count
            />
          </NFormItem>

          <NFormItem label="建议内容" required>
            <NInput
              type="textarea"
              v-model:value="editForm.content" 
              placeholder="请输入详细的建议内容"
              :rows="4"
              maxlength="1000"
              show-count
            />
          </NFormItem>

          <NFormItem label="标签">
            <NInput 
              v-model:value="editForm.tags" 
              placeholder="请输入标签，用逗号分隔"
              @blur="() => {
                if (typeof editForm.tags === 'string') {
                  editForm.tags = editForm.tags.split(',').map(s => s.trim()).filter(s => s);
                }
              }"
            />
          </NFormItem>
        </NForm>

        <NDivider />

        <div class="flex justify-end gap-3">
          <NButton @click="cancelEdit">取消</NButton>
          <NButton type="primary" @click="saveTemplate">
            {{ editForm.id ? '更新模板' : '创建模板' }}
          </NButton>
        </div>
      </NCard>
    </div>
  </NModal>
</template>

<style scoped>
.text-primary {
  color: var(--primary-color);
}

.text-success {
  color: var(--success-color);
}

.text-info {
  color: var(--info-color);
}

.text-warning {
  color: var(--warning-color);
}
</style>