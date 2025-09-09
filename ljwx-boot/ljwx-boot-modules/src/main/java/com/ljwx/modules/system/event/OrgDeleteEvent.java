package com.ljwx.modules.system.event;

import lombok.Getter;
import org.springframework.context.ApplicationEvent;

/**
 * 组织删除事件
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @CreateTime 2025-01-26
 */
@Getter
public class OrgDeleteEvent extends ApplicationEvent {
    
    private final Long orgId;
    private final String orgName;
    
    public OrgDeleteEvent(Object source, Long orgId, String orgName) {
        super(source);
        this.orgId = orgId;
        this.orgName = orgName;
    }
}