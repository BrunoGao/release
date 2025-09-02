package com.ljwx.modules.system.listener;

import com.ljwx.modules.customer.domain.entity.TCustomerConfig;
import com.ljwx.modules.customer.domain.entity.THealthDataConfig;
import com.ljwx.modules.customer.domain.entity.TInterface;
import com.ljwx.modules.customer.service.ITCustomerConfigService;
import com.ljwx.modules.customer.service.ITHealthDataConfigService;
import com.ljwx.modules.customer.service.ITInterfaceService;
import com.ljwx.modules.health.domain.entity.TAlertRules;
import com.ljwx.modules.health.service.ITAlertRulesService;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.domain.entity.SysRole;
import com.ljwx.modules.system.domain.entity.SysPosition;
import com.ljwx.modules.system.service.ISysRoleService;
import com.ljwx.modules.system.service.ISysPositionService;
import com.ljwx.modules.system.event.SysOrgUnitsChangeEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;


import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@Component
@Slf4j
public class OrgUnitsChangeListener {
    
    @Autowired
    private ITCustomerConfigService customerConfigService;
    
    @Autowired
    private ITInterfaceService interfaceService;
    
    @Autowired
    private ITHealthDataConfigService healthDataConfigService;
    
    @Autowired
    private ITAlertRulesService alertRulesService;
    
    @Autowired
    private ISysRoleService roleService;
    
    @Autowired
    private ISysPositionService positionService;
    
    @Transactional(rollbackFor = Exception.class)
    @EventListener(SysOrgUnitsChangeEvent.class)
    public void handleOrgUnitsChange(SysOrgUnitsChangeEvent event) {
        SysOrgUnits orgUnit = event.getOrgUnit();
        log.warn("OrgUnitsChangeListener event triggered, orgId={}, isDeleted={}, parentId={}, hash={}", 
            orgUnit.getId(), orgUnit.getIsDeleted(), orgUnit.getParentId(), System.identityHashCode(this));
        if (orgUnit.getParentId() == 0 && orgUnit.getIsDeleted() == 0) {
            cloneCustomerConfig(orgUnit);
            cloneInterface(orgUnit);
            cloneHealthDataConfig(orgUnit);
            cloneAlertRules(orgUnit);
            cloneRoles(orgUnit);
            clonePositions(orgUnit);
            log.info("Cloned config, roles and positions for new orgId={}", orgUnit.getId());
        }
        if (orgUnit.getParentId() == 0 && orgUnit.getIsDeleted() == 1) {
            customerConfigService.lambdaUpdate().eq(TCustomerConfig::getId, orgUnit.getId()).set(TCustomerConfig::getIsDeleted, 1).update();
            interfaceService.lambdaUpdate().eq(TInterface::getCustomerId, orgUnit.getId()).set(TInterface::getDeleted, 1).update();
            healthDataConfigService.lambdaUpdate().eq(THealthDataConfig::getCustomerId, orgUnit.getId()).set(THealthDataConfig::getIsDeleted, 1).update();
            alertRulesService.lambdaUpdate().eq(TAlertRules::getCustomerId, orgUnit.getId()).set(TAlertRules::getDeleted, 1).update();
            roleService.lambdaUpdate().eq(SysRole::getCustomerId, orgUnit.getId()).set(SysRole::getDeleted, 1).update();
            positionService.lambdaUpdate().eq(SysPosition::getCustomerId, orgUnit.getId()).set(SysPosition::getDeleted, 1).update();
            log.info("Deleted org and related config, roles, positions for orgId={}", orgUnit.getId());
        }
    }
    
    private void cloneCustomerConfig(SysOrgUnits o) { // 复制客户配置
        // 检查是否已存在配置，避免循环创建
        TCustomerConfig existingConfig = customerConfigService.getById(o.getId());
        if (existingConfig != null) {
            log.info("CustomerConfig already exists for orgId={}, skipping clone", o.getId());
            return;
        }
        
        customerConfigService.list(new QueryWrapper<TCustomerConfig>().eq("id", 1)).forEach(c -> {
            TCustomerConfig n = new TCustomerConfig();
            n.setId(o.getId()); n.setCustomerName(o.getName());
            n.setLicenseKey(c.getLicenseKey()); n.setCreateTime(c.getCreateTime()); n.setUpdateTime(c.getUpdateTime());
            n.setIsSupportLicense(c.getIsSupportLicense()); n.setUploadMethod(c.getUploadMethod());
            n.setIsDeleted(0);
            n.setEnableResume(c.getEnableResume());
            n.setUploadRetryCount(c.getUploadRetryCount());
            n.setCacheMaxCount(c.getCacheMaxCount());
            n.setUploadRetryInterval(c.getUploadRetryInterval());
            n.setCustomerId(o.getId()); // 设置customer_id
            customerConfigService.saveOrUpdate(n);
        });
    }
    
    private void cloneInterface(SysOrgUnits o) { // 复制接口配置
        log.warn("cloneInterface called for orgId={}", o.getId());
        interfaceService.remove(new QueryWrapper<TInterface>().eq("customer_id", o.getId())); // 先清理
        List<TInterface> exists = interfaceService.list(new QueryWrapper<TInterface>().eq("customer_id", o.getId()));
        Set<String> existNames = exists.stream().map(TInterface::getName).collect(Collectors.toSet());
        interfaceService.list(new QueryWrapper<TInterface>().eq("customer_id", 1).eq("is_deleted", 0)).stream()
            .filter(i -> !existNames.contains(i.getName()))
            .forEach(i -> {
                log.warn("Inserting interface name={} for orgId={}", i.getName(), o.getId());
                log.warn("i.getApiAuth()={}", i.getApiAuth());
                log.warn("i.getApiId()={}", i.getApiId());
                System.out.println("i.getApiAuth()={}" + i.getApiAuth());
                System.out.println("i.getApiId()={}" + i.getApiId());
                TInterface n = new TInterface();
                n.setName(i.getName()); n.setUrl(i.getUrl()); n.setCallInterval(i.getCallInterval());
                n.setMethod(i.getMethod()); n.setDescription(i.getDescription()); n.setEnabled(i.getEnabled());
                n.setCustomerId(o.getId()); n.setDeleted(0); n.setCreateTime(i.getCreateTime()); n.setUpdateTime(i.getUpdateTime());
                n.setApiAuth(i.getApiAuth()); 
                n.setApiId(i.getApiId());
                interfaceService.saveOrUpdate(n);
            });
    }
    
    private void cloneHealthDataConfig(SysOrgUnits o) { // 复制健康数据配置
        log.warn("cloneHealthDataConfig called for orgId={}", o.getId());
        healthDataConfigService.remove(new QueryWrapper<THealthDataConfig>().eq("customer_id", o.getId())); // 先清理
        healthDataConfigService.list(new QueryWrapper<THealthDataConfig>().eq("customer_id", 1)).forEach(h -> {
            THealthDataConfig n = new THealthDataConfig();
            n.setCustomerId(o.getId()); n.setDataType(h.getDataType()); n.setFrequencyInterval(h.getFrequencyInterval());
            n.setIsRealtime(h.getIsRealtime()); n.setIsEnabled(h.getIsEnabled()); n.setIsDefault(h.getIsDefault());
            n.setWarningHigh(h.getWarningHigh()); n.setWarningLow(h.getWarningLow()); n.setWarningCnt(h.getWarningCnt());
            n.setIsDeleted(0); n.setCreateTime(h.getCreateTime()); n.setUpdateTime(h.getUpdateTime()); n.setWeight(h.getWeight());
            healthDataConfigService.saveOrUpdate(n);
        });
    }
    
    private void cloneAlertRules(SysOrgUnits o) {
        log.warn("cloneAlertRules called for orgId={}", o.getId());
        alertRulesService.remove(new QueryWrapper<TAlertRules>().eq("customer_id", o.getId()));
        alertRulesService.list(new QueryWrapper<TAlertRules>().eq("customer_id", 0).eq("is_deleted", 0)).forEach(a -> {
            TAlertRules n = new TAlertRules();
            n.setCustomerId(o.getId());
            n.setRuleType(a.getRuleType());
            n.setPhysicalSign(a.getPhysicalSign());
            n.setThresholdMin(a.getThresholdMin());
            n.setThresholdMax(a.getThresholdMax());
            n.setDeviationPercentage(a.getDeviationPercentage());
            n.setTrendDuration(a.getTrendDuration());
            n.setParameters(a.getParameters());
            n.setTriggerCondition(a.getTriggerCondition());
            n.setAlertMessage(a.getAlertMessage());
            n.setSeverityLevel(a.getSeverityLevel());
            n.setNotificationType(a.getNotificationType());
            n.setDeleted(0);
            n.setCreateTime(a.getCreateTime());
            n.setUpdateTime(a.getUpdateTime());
            alertRulesService.saveOrUpdate(n);
        });
    }
    
    private void cloneRoles(SysOrgUnits o) { // 复制角色
        log.warn("cloneRoles called for orgId={}", o.getId());
        // 先清理当前租户的角色（避免重复）
        roleService.lambdaUpdate().eq(SysRole::getCustomerId, o.getId()).set(SysRole::getDeleted, 1).update();
        
        // 获取所有全局角色（customer_id = 0）
        roleService.list(new QueryWrapper<SysRole>().eq("customer_id", 0).eq("is_deleted", 0)).forEach(r -> {
            SysRole n = new SysRole();
            n.setParentId(r.getParentId());
            n.setRoleName(r.getRoleName());
            n.setRoleCode(r.getRoleCode());
            n.setDescription(r.getDescription());
            n.setSort(r.getSort());
            n.setCreateUser(r.getCreateUser());
            n.setCreateUserId(r.getCreateUserId());
            n.setCreateTime(r.getCreateTime());
            n.setUpdateUser(r.getUpdateUser());
            n.setUpdateUserId(r.getUpdateUserId());
            n.setUpdateTime(r.getUpdateTime());
            n.setStatus(r.getStatus());
            n.setIsAdmin(r.getIsAdmin());
            n.setDeleted(0);
            n.setCustomerId(o.getId()); // 设置为当前租户ID
            roleService.save(n);
            log.info("Cloned role {} for tenant {}", r.getRoleName(), o.getId());
        });
    }
    
    private void clonePositions(SysOrgUnits o) { // 复制岗位
        log.warn("clonePositions called for orgId={}", o.getId());
        // 先清理当前租户的岗位（避免重复）
        positionService.lambdaUpdate().eq(SysPosition::getCustomerId, o.getId()).set(SysPosition::getDeleted, 1).update();
        
        // 获取所有全局岗位（customer_id = 0）
        positionService.list(new QueryWrapper<SysPosition>().eq("customer_id", 0).eq("is_deleted", 0)).forEach(p -> {
            SysPosition n = new SysPosition();
            n.setName(p.getName());
            n.setCode(p.getCode());
            n.setAbbr(p.getAbbr());
            n.setDescription(p.getDescription());
            n.setSort(p.getSort());
            n.setCreateUser(p.getCreateUser());
            n.setCreateUserId(p.getCreateUserId());
            n.setCreateTime(p.getCreateTime());
            n.setUpdateUser(p.getUpdateUser());
            n.setUpdateUserId(p.getUpdateUserId());
            n.setUpdateTime(p.getUpdateTime());
            n.setStatus(p.getStatus());
            n.setDeleted(0);
            n.setOrgId(o.getId()); // 设置组织ID为当前租户ID
            n.setWeight(p.getWeight());
            n.setCustomerId(o.getId()); // 设置为当前租户ID
            positionService.save(n);
            log.info("Cloned position {} for tenant {}", p.getName(), o.getId());
        });
    }

} 