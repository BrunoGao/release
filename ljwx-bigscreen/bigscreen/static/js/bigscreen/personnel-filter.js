// 人员筛选功能 - 部门和用户数据处理
// 存储部门数据的映射关系
window.departmentMap = new Map();

// 初始化人员筛选功能
function initPersonnelFilter() {
    const customerId = window.CUSTOMER_ID || '1';
    console.log('🏢 初始化人员筛选功能，客户ID:', customerId);
    
    // 获取部门数据并填充地图上的选择框
    loadDepartmentsToMapFilter(customerId);
    
    // 绑定地图筛选面板的事件
    bindMapFilterEvents();
}

// 加载部门数据到地图筛选面板
async function loadDepartmentsToMapFilter(customerId) {
    try {
        console.log('📊 正在获取部门数据...');
        const response = await fetch(`/get_departments?orgId=${customerId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.data) {
            console.log('✅ 部门数据获取成功:', data.data);
            populateMapDepartmentSelect(data.data);
        } else {
            console.warn('⚠️ 部门数据格式异常:', data);
            showMockDepartmentsInMap();
        }
    } catch (error) {
        console.error('❌ 获取部门数据失败:', error);
        showMockDepartmentsInMap();
    }
}

// 填充地图筛选面板的部门选择框
function populateMapDepartmentSelect(departments) {
    const deptSelect = document.getElementById('deptSelect');
    if (!deptSelect) {
        console.warn('⚠️ 未找到地图部门选择框元素');
        return;
    }
    
    // 清空现有选项
    deptSelect.innerHTML = '<option value="">选择部门</option>';
    
    // 递归添加部门选项并保存映射关系
    function addDepartmentOptions(depts, level = 0) {
        depts.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept.id;
            const indent = '　'.repeat(level);
            option.textContent = indent + dept.name;
            deptSelect.appendChild(option);
            
            // 保存部门ID和名称的映射
            window.departmentMap.set(dept.id.toString(), dept.name);
            
            if (dept.children && dept.children.length > 0) {
                addDepartmentOptions(dept.children, level + 1);
            }
        });
    }
    
    addDepartmentOptions(departments);
    console.log('✅ 地图部门选择框填充完成，共', window.departmentMap.size, '个部门');
}

// 在地图中显示模拟部门数据
function showMockDepartmentsInMap() {
    console.log('🔄 在地图中使用模拟部门数据');
    const mockDepartments = [
        { id: 1, name: '技术部', children: [] },
        { id: 2, name: '市场部', children: [] },
        { id: 3, name: '财务部', children: [] },
        { id: 4, name: '人事部', children: [] }
    ];
    populateMapDepartmentSelect(mockDepartments);
}

// 绑定地图筛选面板事件
function bindMapFilterEvents() {
    const deptSelect = document.getElementById('deptSelect');
    const userSelect = document.getElementById('userSelect');
    
    if (!deptSelect || !userSelect) {
        console.warn('⚠️ 未找到地图筛选选择框元素');
        return;
    }
    
    deptSelect.addEventListener('change', function() {
        const selectedDeptId = this.value;
        const selectedDeptName = selectedDeptId ? window.departmentMap.get(selectedDeptId.toString()) : '';
        
        console.log('🏢 地图部门选择变化:', selectedDeptId, selectedDeptName);
        
        // 重置用户选择框
        userSelect.innerHTML = '<option value="">选择用户</option>';
        
        if (selectedDeptId) {
            loadUsersToMapFilter(selectedDeptId, userSelect);
        }
        
        // 触发地图更新
        updateMapFilter(selectedDeptId, selectedDeptName);
    });
    
    // 用户选择变化事件
    userSelect.addEventListener('change', function() {
        const selectedDeptId = deptSelect.value;
        const selectedDeptName = selectedDeptId ? window.departmentMap.get(selectedDeptId.toString()) : '';
        const selectedUserId = this.value;
        const selectedOption = this.options[this.selectedIndex];
        const selectedUserName = selectedOption.dataset.userName || '';
        
        console.log('👤 地图用户选择变化:', selectedUserId, selectedUserName);
        
        // 触发地图更新
        updateMapFilter(selectedDeptId, selectedDeptName, selectedUserId, selectedUserName);
    });
}

// 加载用户数据到地图筛选面板
async function loadUsersToMapFilter(deptId, userSelect) {
    try {
        console.log('👥 正在获取用户数据，部门ID:', deptId);
        const response = await fetch(`/fetch_users?orgId=${deptId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const users = await response.json();
        
        if (Array.isArray(users) && users.length > 0) {
            console.log('✅ 用户数据获取成功:', users);
            populateMapUserSelect(users, userSelect);
        } else {
            console.warn('⚠️ 用户数据为空或格式异常:', users);
            showMockUsersInMap(userSelect);
        }
    } catch (error) {
        console.error('❌ 获取用户数据失败:', error);
        showMockUsersInMap(userSelect);
    }
}

// 填充地图用户选择框
function populateMapUserSelect(users, userSelect) {
    users.forEach(user => {
        const option = document.createElement('option');
        option.value = user.id;
        option.textContent = user.user_name;
        option.dataset.userName = user.user_name;
        userSelect.appendChild(option);
    });
    
    // 添加"全部用户"选项
    const allOption = document.createElement('option');
    allOption.value = 'all';
    allOption.textContent = '全部用户';
    userSelect.appendChild(allOption);
    
    console.log('✅ 地图用户选择框填充完成，共', users.length, '个用户');
}

// 在地图中显示模拟用户数据
function showMockUsersInMap(userSelect) {
    console.log('🔄 在地图中使用模拟用户数据');
    const mockUsers = [
        { id: 1, user_name: '张三' },
        { id: 2, user_name: '李四' },
        { id: 3, user_name: '王五' }
    ];
    populateMapUserSelect(mockUsers, userSelect);
}

// 更新地图筛选
function updateMapFilter(deptId, deptName, userId, userName) {
    console.log('🗺️ 更新地图筛选:', { deptId, deptName, userId, userName });
    
    // 更新全局筛选变量
    if (typeof window.currentDept !== 'undefined') {
        window.currentDept = deptId || '';
        if (typeof currentDept !== 'undefined') {
            currentDept = deptId || '';
        }
    }
    
    if (typeof window.currentUser !== 'undefined') {
        window.currentUser = userId || '';
        if (typeof currentUser !== 'undefined') {
            currentUser = userId || '';
        }
    }
    
    console.log('🔄 已更新筛选条件:', { currentDept: currentDept || window.currentDept, currentUser: currentUser || window.currentUser });
    
    // 触发地图数据重新加载
    if (window.loadDashboardData) {
        console.log('🔄 触发数据刷新以应用筛选');
        window.loadDashboardData();
    }
}

// 切换筛选面板显示状态 #修复为原版逻辑
function toggleFilterPanel() {
    const p = document.getElementById('filterPanel');
    const t = document.getElementById('filterToggle');
    
    if (!p) {
        console.warn('⚠️ 未找到筛选面板');
        return;
    }
    
    console.log('🎛️ 切换筛选面板状态');
    
    // 使用原版的expanded类名逻辑
    if (p.classList.contains('expanded')) {
        p.classList.remove('expanded');
        if (t) t.textContent = '🔍';
        console.log('📴 筛选面板已关闭');
    } else {
        p.classList.add('expanded');
        if (t) t.textContent = '✕';
        console.log('📋 筛选面板已打开');
    }
}

// 导出到全局作用域
window.initPersonnelFilter = initPersonnelFilter;
window.toggleFilterPanel = toggleFilterPanel;
window.updateMapFilter = updateMapFilter;

console.log('✅ personnel-filter.js 加载完成'); 