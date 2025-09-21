#!/usr/bin/env node

/**
 * Drawer 组件批量美化脚本
 * 
 * 用法: node scripts/enhance-drawers.js
 * 
 * 功能:
 * 1. 扫描所有 *-operate-drawer.vue 文件
 * 2. 自动应用美化方案
 * 3. 生成备份文件
 * 4. 输出美化报告
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// 配置
const CONFIG = {
  // 源文件目录
  sourceDir: 'src/views',
  // 备份目录
  backupDir: 'backup/drawers',
  // 样式文件导入语句
  styleImport: "@import '@/styles/drawer.scss';",
  // 是否生成备份
  createBackup: true,
  // 是否强制覆盖
  forceOverwrite: false
};

// 颜色配置映射
const COLOR_THEMES = {
  'user': {
    name: '用户管理',
    bannerBg: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
    iconBg: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
    iconShadow: 'rgba(14, 165, 233, 0.3)',
    titleColor: '#0c4a6e',
    descColor: '#0369a1',
    borderColor: '#e0f2fe'
  },
  'scheduler': {
    name: '调度任务',
    bannerBg: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
    iconBg: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    iconShadow: 'rgba(245, 158, 11, 0.3)',
    titleColor: '#92400e',
    descColor: '#a16207',
    borderColor: '#fde68a'
  },
  'device': {
    name: '设备管理',
    bannerBg: 'linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%)',
    iconBg: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
    iconShadow: 'rgba(139, 92, 246, 0.3)',
    titleColor: '#581c87',
    descColor: '#6b21a8',
    borderColor: '#e9d5ff'
  },
  'alert': {
    name: '告警配置',
    bannerBg: 'linear-gradient(135deg, #fef2f2 0%, #fecaca 100%)',
    iconBg: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
    iconShadow: 'rgba(239, 68, 68, 0.3)',
    titleColor: '#7f1d1d',
    descColor: '#991b1b',
    borderColor: '#fecaca'
  },
  'health': {
    name: '健康数据',
    bannerBg: 'linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)',
    iconBg: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    iconShadow: 'rgba(16, 185, 129, 0.3)',
    titleColor: '#064e3b',
    descColor: '#065f46',
    borderColor: '#d1fae5'
  }
};

// 组件图标映射
const COMPONENT_ICONS = {
  'user': 'i-material-symbols:person',
  'scheduler': 'i-material-symbols:schedule',
  'device': 'i-material-symbols:devices',
  'alert': 'i-material-symbols:warning',
  'health': 'i-material-symbols:health-and-safety',
  'menu': 'i-material-symbols:menu',
  'role': 'i-material-symbols:admin-panel-settings',
  'org': 'i-material-symbols:corporate-fare',
  'dict': 'i-material-symbols:book',
  'notice': 'i-material-symbols:notifications',
  'position': 'i-material-symbols:work',
  'customer': 'i-material-symbols:business',
  'interface': 'i-material-symbols:api',
  'geofence': 'i-material-symbols:fence',
  'message': 'i-material-symbols:message'
};

/**
 * 获取组件主题
 */
function getComponentTheme(filePath) {
  const fileName = path.basename(filePath);
  
  // 根据文件名判断组件类型
  for (const [key, theme] of Object.entries(COLOR_THEMES)) {
    if (fileName.includes(key)) {
      return { type: key, ...theme };
    }
  }
  
  // 默认主题
  return { 
    type: 'default', 
    ...COLOR_THEMES.user,
    name: '通用组件'
  };
}

/**
 * 获取组件图标
 */
function getComponentIcon(filePath, operationType = 'add') {
  const fileName = path.basename(filePath);
  
  for (const [key, icon] of Object.entries(COMPONENT_ICONS)) {
    if (fileName.includes(key)) {
      return operationType === 'add' ? `${icon}-add` : `${icon}-edit`;
    }
  }
  
  return operationType === 'add' ? 'i-material-symbols:add' : 'i-material-symbols:edit';
}

/**
 * 生成操作横幅代码
 */
function generateOperationBanner(theme, componentName) {
  const addIcon = getComponentIcon('', 'add');
  const editIcon = getComponentIcon('', 'edit');
  
  return `
      <!-- 操作提示横幅 -->
      <div class="operation-banner">
        <div class="banner-icon">
          <i class="${addIcon}" v-if="isAdd"></i>
          <i class="${editIcon}" v-else></i>
        </div>
        <div class="banner-content">
          <h3 class="banner-title">{{ isAdd ? '新增${componentName}' : '编辑${componentName}' }}</h3>
          <p class="banner-desc">{{ isAdd ? '请填写完整的${componentName}信息，标有 * 的为必填项' : '修改${componentName}信息，部分字段不可编辑' }}</p>
        </div>
      </div>
`;
}

/**
 * 生成表单分组代码
 */
function generateFormSection(title, icon, content) {
  return `
        <!-- ${title} -->
        <div class="form-section">
          <div class="section-title">
            <i class="${icon}"></i>
            ${title}
          </div>
          ${content}
        </div>`;
}

/**
 * 生成增强的底部按钮
 */
function generateFooter() {
  return `
      <template #footer>
        <div class="drawer-footer">
          <NButton @click="closeDrawer" class="cancel-btn">
            <template #icon>
              <i class="i-material-symbols:close"></i>
            </template>
            {{ $t('common.cancel') }}
          </NButton>
          <NButton type="primary" @click="handleSubmit" class="submit-btn" :loading="submitting">
            <template #icon>
              <i class="i-material-symbols:check" v-if="!submitting"></i>
            </template>
            {{ isAdd ? $t('common.add') : $t('common.update') }}
          </NButton>
        </div>
      </template>`;
}

/**
 * 生成主题样式
 */
function generateThemeStyles(theme) {
  return `
/* 操作提示横幅 - ${theme.name} */
.operation-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  margin: -24px -24px 24px -24px;
  background: ${theme.bannerBg};
  border-bottom: 1px solid ${theme.borderColor};
}

.banner-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: ${theme.iconBg};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  box-shadow: 0 4px 12px ${theme.iconShadow};
}

.banner-content {
  flex: 1;
}

.banner-title {
  font-size: 18px;
  font-weight: 700;
  color: ${theme.titleColor};
  margin: 0 0 4px 0;
}

.banner-desc {
  font-size: 14px;
  color: ${theme.descColor};
  margin: 0;
  line-height: 1.4;
}

/* 底部按钮样式 */
.drawer-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  width: 100%;
}

.cancel-btn {
  min-width: 100px;
}

.submit-btn {
  min-width: 120px;
}`;
}

/**
 * 处理单个drawer文件
 */
function enhanceDrawerFile(filePath) {
  console.log(`处理文件: ${filePath}`);
  
  try {
    // 读取文件内容
    const content = fs.readFileSync(filePath, 'utf8');
    
    // 如果已经美化过，跳过
    if (content.includes('enhanced-drawer') && !CONFIG.forceOverwrite) {
      console.log(`  ⏭️  已美化，跳过`);
      return { status: 'skipped', reason: 'already_enhanced' };
    }
    
    // 创建备份
    if (CONFIG.createBackup) {
      const backupPath = path.join(CONFIG.backupDir, path.relative(CONFIG.sourceDir, filePath));
      const backupDir = path.dirname(backupPath);
      if (!fs.existsSync(backupDir)) {
        fs.mkdirSync(backupDir, { recursive: true });
      }
      fs.writeFileSync(backupPath, content);
      console.log(`  📁 创建备份: ${backupPath}`);
    }
    
    // 获取组件主题
    const theme = getComponentTheme(filePath);
    const componentName = theme.name;
    
    let newContent = content;
    
    // 1. 添加 enhanced-drawer 类
    newContent = newContent.replace(
      /<NDrawer([^>]*?)>/g,
      (match, attrs) => {
        if (!attrs.includes('class=')) {
          return `<NDrawer${attrs} class="enhanced-drawer">`;
        } else {
          return match.replace(/class="([^"]*)"/, 'class="$1 enhanced-drawer"');
        }
      }
    );
    
    // 2. 增加drawer宽度
    newContent = newContent.replace(
      /:width="360"/g,
      ':width="420"'
    );
    
    // 3. 添加增强标题（在script部分）
    if (!newContent.includes('enhancedTitle')) {
      const titleAddition = `
const enhancedTitle = computed(() => {
  const icon = isAdd.value ? '✨' : '✏️';
  return \`\${icon} \${title.value}\`;
});`;
      
      newContent = newContent.replace(
        /(const isAdd = computed.*?;)/s,
        '$1\n' + titleAddition
      );
    }
    
    // 4. 添加submitting状态
    if (!newContent.includes('submitting')) {
      newContent = newContent.replace(
        /import.*from 'vue';/,
        match => match.replace('} from \'vue\';', ', ref } from \'vue\';')
      );
      
      newContent = newContent.replace(
        /(const.*?= computed.*?;)/s,
        '$1\nconst submitting = ref(false);'
      );
    }
    
    // 5. 增强handleSubmit函数
    newContent = newContent.replace(
      /async function handleSubmit\(\) \{[\s\S]*?\}/,
      `async function handleSubmit() {
  try {
    submitting.value = true;
    await validate();
    
    // request
    const func = isAdd.value ? fetchAdd : fetchUpdate;
    const { error, data } = await func(model);
    if (!error && data) {
      window.$message?.success(isAdd.value ? $t('common.addSuccess') : $t('common.updateSuccess'));
      closeDrawer();
      emit('submitted');
    }
  } catch (error) {
    console.error('Submit error:', error);
  } finally {
    submitting.value = false;
  }
}`
    );
    
    // 6. 添加操作横幅到模板
    const bannerCode = generateOperationBanner(theme, componentName);
    newContent = newContent.replace(
      /(<NDrawerContent[^>]*>)/,
      '$1' + bannerCode
    );
    
    // 7. 更新footer
    const footerCode = generateFooter();
    newContent = newContent.replace(
      /<template #footer>[\s\S]*?<\/template>/,
      footerCode
    );
    
    // 8. 添加或更新样式
    const themeStyles = generateThemeStyles(theme);
    const styleImport = `@import '${CONFIG.styleImport}';`;
    
    if (newContent.includes('<style scoped>')) {
      newContent = newContent.replace(
        /<style scoped>([\s\S]*?)<\/style>/,
        `<style scoped>\n${styleImport}\n\n${themeStyles}\n$1\n</style>`
      );
    } else {
      newContent = newContent.replace(
        /<\/template>$/,
        `</template>\n\n<style scoped>\n${styleImport}\n\n${themeStyles}\n</style>`
      );
    }
    
    // 写入文件
    fs.writeFileSync(filePath, newContent);
    console.log(`  ✅ 美化完成`);
    
    return { status: 'success', theme: theme.name };
    
  } catch (error) {
    console.error(`  ❌ 处理失败: ${error.message}`);
    return { status: 'error', error: error.message };
  }
}

/**
 * 主函数
 */
function main() {
  console.log('🎨 开始批量美化 Drawer 组件...\n');
  
  // 确保备份目录存在
  if (CONFIG.createBackup && !fs.existsSync(CONFIG.backupDir)) {
    fs.mkdirSync(CONFIG.backupDir, { recursive: true });
  }
  
  // 查找所有drawer文件
  const pattern = path.join(CONFIG.sourceDir, '**/*-operate-drawer.vue');
  const files = glob.sync(pattern);
  
  console.log(`📁 发现 ${files.length} 个 drawer 文件\n`);
  
  // 统计信息
  const stats = {
    total: files.length,
    success: 0,
    skipped: 0,
    error: 0,
    themes: {}
  };
  
  // 处理每个文件
  files.forEach((file, index) => {
    console.log(`[${index + 1}/${files.length}] ${file}`);
    const result = enhanceDrawerFile(file);
    
    stats[result.status]++;
    
    if (result.theme) {
      stats.themes[result.theme] = (stats.themes[result.theme] || 0) + 1;
    }
    
    console.log('');
  });
  
  // 输出统计结果
  console.log('📊 处理统计:');
  console.log(`  总计: ${stats.total}`);
  console.log(`  成功: ${stats.success}`);
  console.log(`  跳过: ${stats.skipped}`);
  console.log(`  失败: ${stats.error}`);
  
  if (Object.keys(stats.themes).length > 0) {
    console.log('\n🎨 主题分布:');
    for (const [theme, count] of Object.entries(stats.themes)) {
      console.log(`  ${theme}: ${count}`);
    }
  }
  
  console.log('\n✨ 美化完成！');
  
  if (CONFIG.createBackup) {
    console.log(`📁 备份文件保存在: ${CONFIG.backupDir}`);
  }
  
  console.log('\n📖 查看美化指南: docs/DRAWER_ENHANCEMENT_GUIDE.md');
}

// 运行主函数
if (require.main === module) {
  main();
}

module.exports = {
  enhanceDrawerFile,
  getComponentTheme,
  generateOperationBanner,
  generateFormSection,
  generateFooter,
  generateThemeStyles
};