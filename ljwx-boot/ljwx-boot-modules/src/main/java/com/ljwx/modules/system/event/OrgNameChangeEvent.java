package com.ljwx.modules.system.event;

import lombok.Getter;
import org.springframework.context.ApplicationEvent;

/**
 * 组织名称变更事件
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @CreateTime 2025-01-26
 */
@Getter
public class OrgNameChangeEvent extends ApplicationEvent {
    
    private final Long orgId;
    private final String newOrgName;
    private final String oldOrgName;
    
    public OrgNameChangeEvent(Object source, Long orgId, String newOrgName, String oldOrgName) {
        super(source);
        this.orgId = orgId;
        this.newOrgName = newOrgName;
        this.oldOrgName = oldOrgName;
    }
}