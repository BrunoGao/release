// 示例后端代码：组织架构变更监听器
// 文件路径：src/main/java/com/example/listener/OrgUnitsChangeListener.java

package com.example.listener;

import com.example.entity.OrgUnits;
import com.example.entity.Customer;
import com.example.service.TenantRoleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

/**
 * 组织架构变更监听器
 * 监听租户/部门的创建、更新、删除事件
 */
@Component
public class OrgUnitsChangeListener {

    @Autowired
    private TenantRoleService tenantRoleService;

    /**
     * 监听租户创建事件
     * 当创建新的顶级组织（租户）时触发
     */
    @EventListener
    public void handleTenantCreated(TenantCreatedEvent event) {
        Customer customer = event.getCustomer();
        
        try {
            // 为新租户同步默认角色和岗位数据
            tenantRoleService.syncDefaultRolesForNewTenant(customer);
            
            // 记录日志
            System.out.println("Successfully created default roles and positions for tenant: " + customer.getName());
            
        } catch (Exception e) {
            System.err.println("Failed to sync default data for tenant: " + customer.getName());
            e.printStackTrace();
            // 这里可以添加补偿机制或者告警通知
        }
    }

    /**
     * 监听部门创建事件
     */
    @EventListener
    public void handleDepartmentCreated(DepartmentCreatedEvent event) {
        OrgUnits department = event.getDepartment();
        
        // 部门创建时的处理逻辑
        // 例如：创建部门特定的默认岗位
        System.out.println("Department created: " + department.getName() + 
                          " under tenant: " + department.getCustomerId());
    }

    /**
     * 监听租户删除事件
     */
    @EventListener
    public void handleTenantDeleted(TenantDeletedEvent event) {
        Long customerId = event.getCustomerId();
        
        try {
            // 清理租户相关的角色和岗位数据
            cleanupTenantRolesAndPositions(customerId);
            
            System.out.println("Successfully cleaned up roles and positions for deleted tenant: " + customerId);
            
        } catch (Exception e) {
            System.err.println("Failed to cleanup data for deleted tenant: " + customerId);
            e.printStackTrace();
        }
    }

    /**
     * 清理被删除租户的角色和岗位数据
     */
    private void cleanupTenantRolesAndPositions(Long customerId) {
        // 这里实现清理逻辑
        // 注意：需要考虑数据的完整性约束
        // 可能需要先解除用户与角色、岗位的关联关系
    }
}

/**
 * 租户创建事件
 */
class TenantCreatedEvent {
    private final Customer customer;
    
    public TenantCreatedEvent(Customer customer) {
        this.customer = customer;
    }
    
    public Customer getCustomer() {
        return customer;
    }
}

/**
 * 部门创建事件
 */
class DepartmentCreatedEvent {
    private final OrgUnits department;
    
    public DepartmentCreatedEvent(OrgUnits department) {
        this.department = department;
    }
    
    public OrgUnits getDepartment() {
        return department;
    }
}

/**
 * 租户删除事件
 */
class TenantDeletedEvent {
    private final Long customerId;
    
    public TenantDeletedEvent(Long customerId) {
        this.customerId = customerId;
    }
    
    public Long getCustomerId() {
        return customerId;
    }
}