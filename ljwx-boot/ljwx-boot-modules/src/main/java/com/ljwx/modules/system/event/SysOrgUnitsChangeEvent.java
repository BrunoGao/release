package com.ljwx.modules.system.event;

import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import lombok.Getter;
import lombok.Setter;
import org.springframework.context.ApplicationEvent;

@Getter
@Setter
public class SysOrgUnitsChangeEvent extends ApplicationEvent {
    private final SysOrgUnits orgUnit;
    private final String operationType; // CREATE, UPDATE, DELETE
    
    public SysOrgUnitsChangeEvent(Object source, SysOrgUnits orgUnit, String operationType) {
        super(source);
        this.orgUnit = orgUnit;
        this.operationType = operationType;
    }
} 