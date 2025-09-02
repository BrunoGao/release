// 示例后端代码：租户角色管理服务
// 文件路径：src/main/java/com/example/service/TenantRoleService.java

package com.example.service;

import com.example.entity.SysRole;
import com.example.entity.SysPosition;
import com.example.entity.Customer;
import com.example.mapper.SysRoleMapper;
import com.example.mapper.SysPositionMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Date;

@Service
public class TenantRoleService {

    @Autowired
    private SysRoleMapper roleMapper;
    
    @Autowired
    private SysPositionMapper positionMapper;

    /**
     * 创建新租户时同步默认角色和岗位数据
     * 
     * @param customer 新创建的租户信息
     */
    @Transactional
    public void syncDefaultRolesForNewTenant(Customer customer) {
        Long customerId = customer.getId();
        
        // 1. 创建默认角色
        createDefaultRoles(customerId);
        
        // 2. 创建默认岗位
        createDefaultPositions(customerId);
    }
    
    /**
     * 为新租户创建默认角色
     */
    private void createDefaultRoles(Long customerId) {
        // 定义默认角色模板
        String[] defaultRoles = {
            "R_ADMIN:租户管理员:负责租户内部管理",
            "R_MANAGER:部门经理:负责部门管理",
            "R_USER:普通用户:系统基础用户"
        };
        
        for (String roleTemplate : defaultRoles) {
            String[] parts = roleTemplate.split(":");
            String roleCode = parts[0];
            String roleName = parts[1];
            String description = parts[2];
            
            SysRole role = new SysRole();
            role.setRoleCode(roleCode);
            role.setRoleName(roleName);
            role.setDescription(description);
            role.setCustomerId(customerId);  // 关联到具体租户
            role.setStatus(1); // 启用状态
            role.setSort(1);
            role.setIsAdmin(roleCode.equals("R_ADMIN") ? 1 : 0);
            role.setCreateTime(new Date());
            role.setUpdateTime(new Date());
            
            roleMapper.insert(role);
        }
    }
    
    /**
     * 为新租户创建默认岗位
     */
    private void createDefaultPositions(Long customerId) {
        // 定义默认岗位模板
        String[] defaultPositions = {
            "MANAGER:经理:MGR:负责部门管理工作:5.0",
            "SUPERVISOR:主管:SUP:负责团队督导工作:3.0",
            "STAFF:员工:STF:执行具体工作任务:1.0"
        };
        
        for (String posTemplate : defaultPositions) {
            String[] parts = posTemplate.split(":");
            String code = parts[0];
            String name = parts[1];
            String abbr = parts[2];
            String description = parts[3];
            Double weight = Double.parseDouble(parts[4]);
            
            SysPosition position = new SysPosition();
            position.setCode(code);
            position.setName(name);
            position.setAbbr(abbr);
            position.setDescription(description);
            position.setWeight(weight);
            position.setCustomerId(customerId); // 关联到具体租户
            position.setOrgId(customerId); // 默认关联到租户根组织
            position.setStatus(1); // 启用状态
            position.setSort(1);
            position.setCreateTime(new Date());
            position.setUpdateTime(new Date());
            
            positionMapper.insert(position);
        }
    }
    
    /**
     * 根据租户ID查询角色列表（支持多租户隔离）
     */
    public List<SysRole> getRolesByCustomerId(Long customerId, boolean isAdmin) {
        if (isAdmin) {
            // admin用户可以查看所有角色（包括全局角色和所有租户角色）
            return roleMapper.selectAllRoles();
        } else {
            // 普通用户只能查看自己租户的角色
            return roleMapper.selectByCustomerId(customerId);
        }
    }
    
    /**
     * 根据租户ID查询岗位列表（支持多租户隔离）
     */
    public List<SysPosition> getPositionsByCustomerId(Long customerId, boolean isAdmin) {
        if (isAdmin) {
            // admin用户可以查看所有岗位（包括全局岗位和所有租户岗位）
            return positionMapper.selectAllPositions();
        } else {
            // 普通用户只能查看自己租户的岗位
            return positionMapper.selectByCustomerId(customerId);
        }
    }
}