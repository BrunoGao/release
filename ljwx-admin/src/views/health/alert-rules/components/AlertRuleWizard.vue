<template>
  <div class="alert-rule-wizard">
    <!-- 步骤导航 -->
    <el-steps :active="currentStep" align-center>
      <el-step title="基础信息" />
      <el-step title="规则类型" />
      <el-step title="条件配置" />
      <el-step title="通知设置" />
      <el-step title="生效时间" />
      <el-step title="预览确认" />
    </el-steps>
    
    <!-- 基础信息步骤 -->
    <div v-show="currentStep === 0" class="step-content">
      <el-card header="基础信息">
        <el-form :model="ruleConfig" :rules="basicRules" ref="basicFormRef" label-width="120px">
          <el-form-item label="规则名称" prop="ruleName" required>
            <el-input 
              v-model="ruleConfig.ruleName" 
              placeholder="请输入规则名称" 
              maxlength="100"
              show-word-limit
            />
          </el-form-item>
          
          <el-form-item label="规则描述" prop="ruleDescription">
            <el-input 
              type="textarea" 
              v-model="ruleConfig.ruleDescription" 
              placeholder="请描述此规则的用途"
              :rows="3"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
          
          <el-form-item label="优先级" prop="priorityLevel" required>
            <el-select v-model="ruleConfig.priorityLevel" placeholder="选择优先级">
              <el-option label="最高 (1)" :value="1">
                <span style="color: #f56c6c;">🔴 最高 (1) - 紧急处理</span>
              </el-option>
              <el-option label="高 (2)" :value="2">
                <span style="color: #e6a23c;">🟠 高 (2) - 重要关注</span>
              </el-option>
              <el-option label="中 (3)" :value="3">
                <span style="color: #409eff;">🔵 中 (3) - 常规处理</span>
              </el-option>
              <el-option label="低 (4)" :value="4">
                <span style="color: #67c23a;">🟢 低 (4) - 一般关注</span>
              </el-option>
              <el-option label="最低 (5)" :value="5">
                <span style="color: #909399;">⚪ 最低 (5) - 信息记录</span>
              </el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item label="规则标签">
            <el-tag 
              v-for="tag in ruleConfig.ruleTags" 
              :key="tag" 
              closable 
              @close="removeTag(tag)"
              style="margin-right: 8px; margin-bottom: 8px;"
            >
              {{ tag }}
            </el-tag>
            <el-input 
              v-if="inputVisible"
              v-model="inputValue"
              ref="InputRef"
              size="small"
              @keyup.enter="handleInputConfirm"
              @blur="handleInputConfirm"
              style="width: 120px;"
            />
            <el-button v-else size="small" @click="showInput">+ 添加标签</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
    
    <!-- 规则类型选择 -->
    <div v-show="currentStep === 1" class="step-content">
      <el-card header="选择规则类型">
        <div class="rule-type-grid">
          <div 
            class="rule-type-card" 
            :class="{ active: ruleConfig.ruleCategory === 'SINGLE' }"
            @click="selectRuleType('SINGLE')"
          >
            <el-icon class="type-icon"><Monitor /></el-icon>
            <h3>单体征规则</h3>
            <p>基于单个生理指标的阈值告警</p>
            <div class="example">例：心率 > 120 连续3次</div>
            <div class="features">
              <span class="feature-tag">✓ 配置简单</span>
              <span class="feature-tag">✓ 性能高效</span>
              <span class="feature-tag">✓ 广泛适用</span>
            </div>
          </div>
          
          <div 
            class="rule-type-card" 
            :class="{ active: ruleConfig.ruleCategory === 'COMPOSITE' }"
            @click="selectRuleType('COMPOSITE')"
          >
            <el-icon class="type-icon"><Connection /></el-icon>
            <h3>复合规则</h3>
            <p>多个生理指标的组合条件</p>
            <div class="example">例：心率 > 120 且 血氧 < 90</div>
            <div class="features">
              <span class="feature-tag">✓ 综合分析</span>
              <span class="feature-tag">✓ 精准判断</span>
              <span class="feature-tag">✓ 减少误报</span>
            </div>
          </div>
          
          <div 
            class="rule-type-card" 
            :class="{ active: ruleConfig.ruleCategory === 'COMPLEX' }"
            @click="selectRuleType('COMPLEX')"
            style="opacity: 0.6; cursor: not-allowed;"
          >
            <el-icon class="type-icon"><Setting /></el-icon>
            <h3>复杂规则</h3>
            <p>高级逻辑表达式和自定义公式</p>
            <div class="example">例：自定义算法判断</div>
            <div class="features">
              <span class="feature-tag disabled">⏳ 敬请期待</span>
            </div>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 单体征条件配置 -->
    <div v-show="currentStep === 2 && ruleConfig.ruleCategory === 'SINGLE'" class="step-content">
      <el-card header="单体征条件配置">
        <el-form :model="ruleConfig" :rules="singleRules" ref="singleFormRef" label-width="120px">
          <el-form-item label="生理指标" prop="physicalSign" required>
            <el-select v-model="ruleConfig.physicalSign" placeholder="选择生理指标" @change="onPhysicalSignChange">
              <el-option 
                v-for="sign in physicalSigns" 
                :key="sign.value" 
                :label="sign.label" 
                :value="sign.value"
              >
                <span style="float: left">{{ sign.label }}</span>
                <span style="float: right; color: #8492a6; font-size: 13px">{{ sign.unit }}</span>
              </el-option>
            </el-select>
            <div class="form-tip" v-if="getSelectedSign()">
              正常范围参考: {{ getSelectedSign().normalRange }}
            </div>
          </el-form-item>
          
          <el-form-item label="正常范围" required>
            <div class="threshold-range">
              <el-input-number 
                v-model="ruleConfig.thresholdMin" 
                placeholder="最小值"
                :precision="getSelectedSign()?.precision || 1"
                :step="getSelectedSign()?.step || 1"
              />
              <span class="range-separator">至</span>
              <el-input-number 
                v-model="ruleConfig.thresholdMax" 
                placeholder="最大值"
                :precision="getSelectedSign()?.precision || 1"
                :step="getSelectedSign()?.step || 1"
              />
              <span class="unit">{{ getSelectedSignUnit() }}</span>
            </div>
            <div class="form-tip">
              超出此范围将触发告警
            </div>
          </el-form-item>
          
          <el-form-item label="连续异常次数" prop="trendDuration" required>
            <el-input-number 
              v-model="ruleConfig.trendDuration" 
              :min="1" 
              :max="10"
            />
            <span class="help-text">连续超出阈值多少次后触发告警</span>
          </el-form-item>
          
          <el-form-item label="时间窗口" prop="timeWindowSeconds">
            <el-input-number 
              v-model="ruleConfig.timeWindowSeconds" 
              :min="60" 
              :max="3600"
            />
            <span class="help-text">秒，在此时间窗口内统计异常次数</span>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
    
    <!-- 复合条件配置 -->
    <div v-show="currentStep === 2 && ruleConfig.ruleCategory === 'COMPOSITE'" class="step-content">
      <el-card header="复合条件配置">
        <div class="composite-conditions">
          <div 
            v-for="(condition, index) in compositeConditions" 
            :key="index" 
            class="condition-item"
          >
            <div class="condition-header">
              <span>条件 {{ index + 1 }}</span>
              <el-button 
                v-if="compositeConditions.length > 1"
                @click="removeCondition(index)" 
                type="danger" 
                icon="Delete"
                size="small"
                circle
              />
            </div>
            
            <div class="condition-row">
              <el-select v-model="condition.physicalSign" placeholder="生理指标">
                <el-option 
                  v-for="sign in physicalSigns" 
                  :key="sign.value"
                  :label="sign.label" 
                  :value="sign.value" 
                />
              </el-select>
              
              <el-select v-model="condition.operator" placeholder="运算符">
                <el-option label="大于 >" value=">" />
                <el-option label="小于 <" value="<" />
                <el-option label="大于等于 >=" value=">=" />
                <el-option label="小于等于 <=" value="<=" />
                <el-option label="等于 =" value="=" />
                <el-option label="不等于 !=" value="!=" />
              </el-select>
              
              <el-input-number 
                v-model="condition.threshold" 
                placeholder="阈值"
                :precision="getPhysicalSignPrecision(condition.physicalSign)"
              />
              
              <el-input-number 
                v-model="condition.durationSeconds" 
                placeholder="持续时间(秒)" 
                :min="0" 
              />
            </div>
            
            <!-- 逻辑连接符 -->
            <div 
              v-if="index < compositeConditions.length - 1" 
              class="logic-connector"
            >
              <el-radio-group v-model="logicalOperator">
                <el-radio-button label="AND">并且</el-radio-button>
                <el-radio-button label="OR">或者</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          
          <el-button 
            @click="addCondition" 
            type="primary" 
            icon="Plus"
            :disabled="compositeConditions.length >= 5"
          >
            添加条件 ({{ compositeConditions.length }}/5)
          </el-button>
        </div>
      </el-card>
    </div>
    
    <!-- 通知设置 -->
    <div v-show="currentStep === 3" class="step-content">
      <el-card header="通知设置">
        <el-form :model="ruleConfig" :rules="notificationRules" ref="notificationFormRef" label-width="120px">
          <el-form-item label="严重程度" prop="severityLevel" required>
            <el-select v-model="ruleConfig.severityLevel">
              <el-option value="info">
                <el-tag type="info">信息 (Info)</el-tag>
                <span style="margin-left: 10px;">一般性信息提醒</span>
              </el-option>
              <el-option value="minor">
                <el-tag type="">一般 (Minor)</el-tag>
                <span style="margin-left: 10px;">轻微异常，需要关注</span>
              </el-option>
              <el-option value="major">
                <el-tag type="warning">重要 (Major)</el-tag>
                <span style="margin-left: 10px;">重要异常，需要处理</span>
              </el-option>
              <el-option value="critical">
                <el-tag type="danger">紧急 (Critical)</el-tag>
                <span style="margin-left: 10px;">紧急情况，立即处理</span>
              </el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item label="通知渠道" prop="enabledChannels" required>
            <el-checkbox-group v-model="ruleConfig.enabledChannels">
              <el-checkbox label="message">
                <el-icon><Message /></el-icon>
                内部消息
              </el-checkbox>
              <el-checkbox label="wechat">
                <el-icon><ChatDotRound /></el-icon>
                微信通知
              </el-checkbox>
              <el-checkbox label="sms">
                <el-icon><Phone /></el-icon>
                短信通知
              </el-checkbox>
              <el-checkbox label="email">
                <el-icon><Message /></el-icon>
                邮件通知
              </el-checkbox>
            </el-checkbox-group>
            <div class="form-tip">
              Critical级别将自动启用WebSocket实时推送
            </div>
          </el-form-item>
          
          <el-form-item label="告警消息模板">
            <el-input 
              type="textarea" 
              v-model="ruleConfig.alertMessage" 
              placeholder="可使用变量: {device_sn}, {value}, {threshold}, {physical_sign}"
              :rows="3"
              maxlength="500"
              show-word-limit
            />
            <div class="template-variables">
              <span class="variable-tag" @click="insertVariable('{device_sn}')">{device_sn}</span>
              <span class="variable-tag" @click="insertVariable('{value}')">{value}</span>
              <span class="variable-tag" @click="insertVariable('{threshold}')">{threshold}</span>
              <span class="variable-tag" @click="insertVariable('{physical_sign}')">{physical_sign}</span>
            </div>
          </el-form-item>
          
          <el-form-item label="冷却期" prop="cooldownSeconds">
            <el-input-number 
              v-model="ruleConfig.cooldownSeconds" 
              :min="0" 
              :max="86400"
            />
            <span class="help-text">秒，避免重复告警的冷却时间</span>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
    
    <!-- 生效时间 -->
    <div v-show="currentStep === 4" class="step-content">
      <el-card header="生效时间设置">
        <el-form :model="ruleConfig" label-width="120px">
          <el-form-item label="全天生效">
            <el-switch v-model="allDayActive" @change="onAllDayChange" />
            <span class="help-text">关闭后可设置具体的生效时间段</span>
          </el-form-item>
          
          <el-form-item label="生效时间段" v-if="!allDayActive">
            <el-time-picker 
              v-model="effectiveTimeRange" 
              is-range 
              range-separator="至" 
              format="HH:mm" 
              placeholder="选择时间范围"
            />
          </el-form-item>
          
          <el-form-item label="生效星期">
            <el-checkbox-group v-model="ruleConfig.effectiveDays">
              <el-checkbox label="1">周一</el-checkbox>
              <el-checkbox label="2">周二</el-checkbox>
              <el-checkbox label="3">周三</el-checkbox>
              <el-checkbox label="4">周四</el-checkbox>
              <el-checkbox label="5">周五</el-checkbox>
              <el-checkbox label="6">周六</el-checkbox>
              <el-checkbox label="7">周日</el-checkbox>
            </el-checkbox-group>
            <div class="quick-actions">
              <el-button size="small" @click="selectWorkdays">工作日</el-button>
              <el-button size="small" @click="selectWeekends">周末</el-button>
              <el-button size="small" @click="selectAllDays">全选</el-button>
            </div>
          </el-form-item>
          
          <el-form-item label="立即生效">
            <el-switch v-model="ruleConfig.isActive" />
            <span class="help-text">关闭后规则将保存但不会生效</span>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
    
    <!-- 预览确认 -->
    <div v-show="currentStep === 5" class="step-content">
      <el-card header="规则预览">
        <div class="rule-preview">
          <div class="preview-section">
            <h4>📝 基础信息</h4>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="规则名称">{{ ruleConfig.ruleName }}</el-descriptions-item>
              <el-descriptions-item label="规则类型">{{ getRuleTypeText() }}</el-descriptions-item>
              <el-descriptions-item label="优先级">{{ getPriorityText() }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="ruleConfig.isActive ? 'success' : 'info'">
                  {{ ruleConfig.isActive ? '启用' : '禁用' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
          
          <div class="preview-section">
            <h4>🎯 触发条件</h4>
            <div class="condition-preview">{{ generateConditionText() }}</div>
          </div>
          
          <div class="preview-section">
            <h4>📢 通知配置</h4>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="严重程度">
                <el-tag :type="getSeverityTagType()">{{ getSeverityText() }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="通知渠道">
                <el-tag 
                  v-for="channel in ruleConfig.enabledChannels" 
                  :key="channel" 
                  size="small"
                  style="margin-right: 4px;"
                >
                  {{ getChannelText(channel) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="告警消息" :span="2">
                {{ ruleConfig.alertMessage || '使用默认模板' }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
          
          <div class="preview-section">
            <h4>⏰ 生效时间</h4>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="时间段">{{ formatEffectiveTime() }}</el-descriptions-item>
              <el-descriptions-item label="生效日期">{{ formatEffectiveDays() }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 操作按钮 -->
    <div class="wizard-actions">
      <el-button @click="previousStep" :disabled="currentStep === 0">
        <el-icon><ArrowLeft /></el-icon>
        上一步
      </el-button>
      
      <el-button @click="nextStep" type="primary" :disabled="!canNextStep" v-if="currentStep < 5">
        下一步
        <el-icon><ArrowRight /></el-icon>
      </el-button>
      
      <el-button @click="saveRule" type="success" v-if="currentStep === 5" :loading="saving">
        <el-icon><Check /></el-icon>
        保存规则
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Monitor, Connection, Setting, Plus, Delete, Message, ChatDotRound, 
  Phone, ArrowLeft, ArrowRight, Check
} from '@element-plus/icons-vue'
import { saveAlertRule } from '@/service/api/health/alert-rules'

// Props
interface Props {
  visible?: boolean
  editRule?: any
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  editRule: null
})

// Emits
interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'success'): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const currentStep = ref(0)
const saving = ref(false)
const inputVisible = ref(false)
const inputValue = ref('')
const allDayActive = ref(true)
const effectiveTimeRange = ref<[Date, Date] | null>(null)

// 表单引用
const basicFormRef = ref()
const singleFormRef = ref()
const notificationFormRef = ref()
const InputRef = ref()

// 规则配置
const ruleConfig = reactive({
  ruleName: '',
  ruleDescription: '',
  ruleCategory: 'SINGLE',
  physicalSign: '',
  thresholdMin: null,
  thresholdMax: null,
  trendDuration: 1,
  timeWindowSeconds: 300,
  priorityLevel: 3,
  severityLevel: 'minor',
  alertMessage: '',
  enabledChannels: ['message'],
  cooldownSeconds: 600,
  effectiveTimeStart: null,
  effectiveTimeEnd: null,
  effectiveDays: ['1','2','3','4','5','6','7'],
  ruleTags: [] as string[],
  isActive: true
})

// 复合条件
const compositeConditions = ref([
  { physicalSign: '', operator: '>', threshold: 0, durationSeconds: 60 }
])
const logicalOperator = ref('AND')

// 生理指标选项
const physicalSigns = ref([
  { 
    label: '心率', 
    value: 'heart_rate', 
    unit: 'bpm', 
    normalRange: '60-100',
    precision: 0,
    step: 1
  },
  { 
    label: '血氧', 
    value: 'blood_oxygen', 
    unit: '%', 
    normalRange: '95-100',
    precision: 1,
    step: 0.1
  },
  { 
    label: '体温', 
    value: 'temperature', 
    unit: '℃', 
    normalRange: '36.0-37.5',
    precision: 1,
    step: 0.1
  },
  { 
    label: '收缩压', 
    value: 'pressure_high', 
    unit: 'mmHg', 
    normalRange: '90-140',
    precision: 0,
    step: 1
  },
  { 
    label: '舒张压', 
    value: 'pressure_low', 
    unit: 'mmHg', 
    normalRange: '60-90',
    precision: 0,
    step: 1
  },
  { 
    label: '步数', 
    value: 'step', 
    unit: '步', 
    normalRange: '3000-10000',
    precision: 0,
    step: 100
  },
  { 
    label: '卡路里', 
    value: 'calorie', 
    unit: 'kcal', 
    normalRange: '1200-2500',
    precision: 0,
    step: 10
  },
  { 
    label: '距离', 
    value: 'distance', 
    unit: 'km', 
    normalRange: '2-8',
    precision: 2,
    step: 0.1
  },
  { 
    label: '压力指数', 
    value: 'stress', 
    unit: '分', 
    normalRange: '0-100',
    precision: 0,
    step: 1
  }
])

// 表单验证规则
const basicRules = {
  ruleName: [
    { required: true, message: '请输入规则名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  priorityLevel: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ]
}

const singleRules = {
  physicalSign: [
    { required: true, message: '请选择生理指标', trigger: 'change' }
  ],
  trendDuration: [
    { required: true, message: '请设置连续异常次数', trigger: 'change' }
  ]
}

const notificationRules = {
  severityLevel: [
    { required: true, message: '请选择严重程度', trigger: 'change' }
  ],
  enabledChannels: [
    { 
      required: true, 
      message: '请至少选择一个通知渠道', 
      trigger: 'change',
      validator: (rule: any, value: any, callback: any) => {
        if (!value || value.length === 0) {
          callback(new Error('请至少选择一个通知渠道'))
        } else {
          callback()
        }
      }
    }
  ]
}

// 计算属性
const canNextStep = computed(() => {
  switch (currentStep.value) {
    case 0: 
      return ruleConfig.ruleName.trim() !== '' && ruleConfig.priorityLevel
    case 1: 
      return ruleConfig.ruleCategory !== ''
    case 2: 
      if (ruleConfig.ruleCategory === 'SINGLE') {
        return ruleConfig.physicalSign !== '' && ruleConfig.thresholdMin !== null && ruleConfig.thresholdMax !== null
      } else if (ruleConfig.ruleCategory === 'COMPOSITE') {
        return compositeConditions.value.every(c => 
          c.physicalSign && c.operator && c.threshold !== null)
      }
      return true
    case 3: 
      return ruleConfig.severityLevel && ruleConfig.enabledChannels.length > 0
    case 4: 
      return true
    default: 
      return true
  }
})

// 方法
const selectRuleType = (type: string) => {
  if (type === 'COMPLEX') {
    ElMessage.warning('复杂规则功能开发中，敬请期待')
    return
  }
  ruleConfig.ruleCategory = type
}

const addCondition = () => {
  if (compositeConditions.value.length >= 5) {
    ElMessage.warning('最多只能添加5个条件')
    return
  }
  compositeConditions.value.push({
    physicalSign: '',
    operator: '>',
    threshold: 0,
    durationSeconds: 60
  })
}

const removeCondition = (index: number) => {
  if (compositeConditions.value.length > 1) {
    compositeConditions.value.splice(index, 1)
  }
}

const showInput = () => {
  inputVisible.value = true
  nextTick(() => {
    InputRef.value!.input!.focus()
  })
}

const handleInputConfirm = () => {
  if (inputValue.value && !ruleConfig.ruleTags.includes(inputValue.value)) {
    ruleConfig.ruleTags.push(inputValue.value)
  }
  inputVisible.value = false
  inputValue.value = ''
}

const removeTag = (tag: string) => {
  const index = ruleConfig.ruleTags.indexOf(tag)
  if (index > -1) {
    ruleConfig.ruleTags.splice(index, 1)
  }
}

const onPhysicalSignChange = () => {
  // 根据选择的指标设置建议的阈值
  const sign = getSelectedSign()
  if (sign) {
    const range = sign.normalRange.split('-')
    if (range.length === 2) {
      ruleConfig.thresholdMin = parseFloat(range[0])
      ruleConfig.thresholdMax = parseFloat(range[1])
    }
  }
}

const onAllDayChange = (value: boolean) => {
  if (value) {
    ruleConfig.effectiveTimeStart = null
    ruleConfig.effectiveTimeEnd = null
    effectiveTimeRange.value = null
  }
}

const selectWorkdays = () => {
  ruleConfig.effectiveDays = ['1', '2', '3', '4', '5']
}

const selectWeekends = () => {
  ruleConfig.effectiveDays = ['6', '7']
}

const selectAllDays = () => {
  ruleConfig.effectiveDays = ['1', '2', '3', '4', '5', '6', '7']
}

const insertVariable = (variable: string) => {
  const textarea = document.querySelector('textarea[placeholder*="可使用变量"]') as HTMLTextAreaElement
  if (textarea) {
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const text = ruleConfig.alertMessage
    ruleConfig.alertMessage = text.slice(0, start) + variable + text.slice(end)
    
    nextTick(() => {
      textarea.focus()
      textarea.setSelectionRange(start + variable.length, start + variable.length)
    })
  }
}

const nextStep = async () => {
  // 表单验证
  let formValid = true
  
  if (currentStep.value === 0 && basicFormRef.value) {
    formValid = await basicFormRef.value.validate().catch(() => false)
  } else if (currentStep.value === 2 && ruleConfig.ruleCategory === 'SINGLE' && singleFormRef.value) {
    formValid = await singleFormRef.value.validate().catch(() => false)
  } else if (currentStep.value === 3 && notificationFormRef.value) {
    formValid = await notificationFormRef.value.validate().catch(() => false)
  }
  
  if (!formValid) return
  
  if (canNextStep.value && currentStep.value < 5) {
    currentStep.value++
  }
}

const previousStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const saveRule = async () => {
  saving.value = true
  try {
    // 处理生效时间
    if (effectiveTimeRange.value) {
      ruleConfig.effectiveTimeStart = effectiveTimeRange.value[0]
      ruleConfig.effectiveTimeEnd = effectiveTimeRange.value[1]
    }
    
    // 构建保存数据
    const saveData = {
      ...ruleConfig,
      conditionExpression: ruleConfig.ruleCategory === 'COMPOSITE' ? {
        conditions: compositeConditions.value,
        logicalOperator: logicalOperator.value
      } : null
    }
    
    // 调用API保存
    await saveAlertRule(saveData)
    
    ElMessage.success('告警规则保存成功')
    emit('success')
    emit('update:visible', false)
    
  } catch (error: any) {
    ElMessage.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 格式化方法
const getRuleTypeText = () => {
  const types: Record<string, string> = {
    'SINGLE': '单体征规则',
    'COMPOSITE': '复合规则', 
    'COMPLEX': '复杂规则'
  }
  return types[ruleConfig.ruleCategory] || ''
}

const getPriorityText = () => {
  const priorities: Record<number, string> = { 
    1: '最高', 2: '高', 3: '中', 4: '低', 5: '最低' 
  }
  return priorities[ruleConfig.priorityLevel] || ''
}

const getSeverityText = () => {
  const severities: Record<string, string> = {
    'info': '信息',
    'minor': '一般',
    'major': '重要',
    'critical': '紧急'
  }
  return severities[ruleConfig.severityLevel] || ''
}

const getSeverityTagType = () => {
  const types: Record<string, string> = {
    'info': 'info',
    'minor': '',
    'major': 'warning',
    'critical': 'danger'
  }
  return types[ruleConfig.severityLevel] || ''
}

const getChannelText = (channel: string) => {
  const channels: Record<string, string> = {
    'message': '内部消息',
    'wechat': '微信',
    'sms': '短信',
    'email': '邮件'
  }
  return channels[channel] || channel
}

const generateConditionText = () => {
  if (ruleConfig.ruleCategory === 'SINGLE') {
    const sign = physicalSigns.value.find(s => s.value === ruleConfig.physicalSign)
    return `${sign?.label || ''} 在 ${ruleConfig.thresholdMin} - ${ruleConfig.thresholdMax} ${sign?.unit || ''} 范围外连续 ${ruleConfig.trendDuration} 次`
  } else if (ruleConfig.ruleCategory === 'COMPOSITE') {
    return compositeConditions.value.map(c => {
      const sign = physicalSigns.value.find(s => s.value === c.physicalSign)
      return `${sign?.label || ''} ${c.operator} ${c.threshold} ${sign?.unit || ''}`
    }).join(` ${logicalOperator.value === 'AND' ? '且' : '或'} `)
  }
  return ''
}

const getSelectedSign = () => {
  return physicalSigns.value.find(s => s.value === ruleConfig.physicalSign)
}

const getSelectedSignUnit = () => {
  const sign = getSelectedSign()
  return sign?.unit || ''
}

const getPhysicalSignPrecision = (physicalSign: string) => {
  const sign = physicalSigns.value.find(s => s.value === physicalSign)
  return sign?.precision || 1
}

const formatEffectiveTime = () => {
  if (allDayActive.value) {
    return '全天'
  }
  if (effectiveTimeRange.value) {
    const start = effectiveTimeRange.value[0]
    const end = effectiveTimeRange.value[1]
    return `${start.getHours().toString().padStart(2, '0')}:${start.getMinutes().toString().padStart(2, '0')} - ${end.getHours().toString().padStart(2, '0')}:${end.getMinutes().toString().padStart(2, '0')}`
  }
  return '全天'
}

const formatEffectiveDays = () => {
  const dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return ruleConfig.effectiveDays.map(d => dayNames[parseInt(d) - 1]).join(', ')
}

// 初始化
onMounted(() => {
  if (props.editRule) {
    // TODO: 加载编辑数据
    Object.assign(ruleConfig, props.editRule)
  }
})
</script>

<style scoped>
.alert-rule-wizard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.step-content {
  margin: 30px 0;
  min-height: 400px;
}

.rule-type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.rule-type-card {
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 30px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.rule-type-card:hover:not([style*="cursor: not-allowed"]) {
  border-color: #409eff;
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.2);
  transform: translateY(-2px);
}

.rule-type-card.active {
  border-color: #409eff;
  background: linear-gradient(135deg, #f0f9ff 0%, #e7f3ff 100%);
}

.type-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 15px;
}

.rule-type-card h3 {
  margin: 15px 0 10px;
  color: #303133;
  font-weight: 600;
}

.rule-type-card p {
  color: #606266;
  margin-bottom: 15px;
  font-size: 14px;
}

.example {
  background: linear-gradient(45deg, #f5f7fa, #e8f4f8);
  padding: 10px;
  border-radius: 8px;
  font-size: 12px;
  color: #666;
  margin-bottom: 15px;
  border-left: 3px solid #409eff;
}

.features {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
}

.feature-tag {
  background: #409eff;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
}

.feature-tag.disabled {
  background: #c0c4cc;
}

.threshold-range {
  display: flex;
  align-items: center;
  gap: 12px;
}

.range-separator {
  color: #606266;
  font-weight: 500;
}

.unit {
  color: #909399;
  font-size: 12px;
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.help-text {
  color: #909399;
  font-size: 12px;
  margin-left: 10px;
}

.condition-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  background: #fafbfc;
}

.condition-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  font-weight: 600;
  color: #303133;
}

.condition-row {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr 1fr;
  gap: 15px;
  align-items: center;
}

.logic-connector {
  text-align: center;
  margin: 15px 0;
  position: relative;
}

.logic-connector::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: #e4e7ed;
  z-index: 0;
}

.logic-connector .el-radio-group {
  background: white;
  padding: 0 20px;
  position: relative;
  z-index: 1;
}

.template-variables {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.variable-tag {
  background: #f0f2f5;
  color: #606266;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  border: 1px solid #d9d9d9;
  transition: all 0.3s;
}

.variable-tag:hover {
  background: #409eff;
  color: white;
}

.quick-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
}

.rule-preview {
  background: #fafbfc;
  border-radius: 8px;
  padding: 20px;
}

.preview-section {
  margin-bottom: 25px;
}

.preview-section h4 {
  color: #303133;
  margin-bottom: 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.condition-preview {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 15px;
  font-family: 'Monaco', 'Menlo', monospace;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.wizard-actions {
  text-align: center;
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.wizard-actions .el-button {
  margin: 0 10px;
  min-width: 120px;
}

@media (max-width: 768px) {
  .rule-type-grid {
    grid-template-columns: 1fr;
  }
  
  .condition-row {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .threshold-range {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
}
</style>