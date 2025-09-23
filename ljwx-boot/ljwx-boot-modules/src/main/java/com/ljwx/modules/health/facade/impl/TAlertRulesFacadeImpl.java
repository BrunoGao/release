/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ljwx.modules.health.facade.impl;

import com.alibaba.fastjson.JSON;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.infrastructure.util.RedisUtil;
import com.ljwx.modules.health.domain.bo.TAlertRulesBO;
import com.ljwx.modules.health.domain.dto.alert.rules.TAlertRulesAddDTO;
import com.ljwx.modules.health.domain.dto.alert.rules.TAlertRulesDeleteDTO;
import com.ljwx.modules.health.domain.dto.alert.rules.TAlertRulesSearchDTO;
import com.ljwx.modules.health.domain.dto.alert.rules.TAlertRulesUpdateDTO;
import com.ljwx.modules.health.domain.entity.TAlertRules;
import com.ljwx.modules.health.domain.vo.TAlertRulesVO;
import com.ljwx.modules.health.facade.ITAlertRulesFacade;
import com.ljwx.modules.health.service.ITAlertRulesService;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.time.LocalTime;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;

/**
 *  门面接口实现层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.impl.TAlertRulesFacadeImpl
 * @CreateTime 2024-10-27 - 13:03:58
 */

@Service
@RequiredArgsConstructor
public class TAlertRulesFacadeImpl implements ITAlertRulesFacade {

    @NonNull
    private ITAlertRulesService tAlertRulesService;
    
    @NonNull 
    private com.ljwx.modules.health.service.AlertRulesCacheManager alertRulesCacheManager;

    @Override
    public RPage<TAlertRulesVO> listTAlertRulesPage(PageQuery pageQuery, TAlertRulesSearchDTO tAlertRulesSearchDTO) {
        TAlertRulesBO tAlertRulesBO = CglibUtil.convertObj(tAlertRulesSearchDTO, TAlertRulesBO::new);
        IPage<TAlertRules> tAlertRulesIPage = tAlertRulesService.listTAlertRulesPage(pageQuery, tAlertRulesBO);
        return RPage.build(tAlertRulesIPage, TAlertRulesVO::new);
    }

    @Override
    public TAlertRulesVO get(Long id) {
        TAlertRules byId = tAlertRulesService.getById(id);
        return CglibUtil.convertObj(byId, TAlertRulesVO::new);
    }

    @Override
    @Transactional
    public boolean add(TAlertRulesAddDTO tAlertRulesAddDTO) {
        // 预处理和验证
        preprocessAlertRule(tAlertRulesAddDTO);
        
        // 检查重复规则
        if (isDuplicateRule(tAlertRulesAddDTO)) {
            throw new RuntimeException("告警规则配置冲突：相同客户下已存在相同规则类型、监控指标和严重级别的规则，请修改后重试");
        }
        
        TAlertRulesBO tAlertRulesBO = CglibUtil.convertObj(tAlertRulesAddDTO, TAlertRulesBO::new);
        boolean result = tAlertRulesService.save(tAlertRulesBO);
        if (result) {
            updateAlertRulesCache(tAlertRulesBO.getCustomerId());
        }
        return result;
    }

    @Override
    @Transactional
    public boolean update(TAlertRulesUpdateDTO tAlertRulesUpdateDTO) {
        // 预处理和验证 - 与AddDTO类似的处理逻辑
        preprocessAlertRuleForUpdate(tAlertRulesUpdateDTO);
        
        TAlertRulesBO tAlertRulesBO = CglibUtil.convertObj(tAlertRulesUpdateDTO, TAlertRulesBO::new);
        boolean result = tAlertRulesService.updateById(tAlertRulesBO);
        if (result) {
            updateAlertRulesCache(tAlertRulesBO.getCustomerId());
        }
        return result;
    }

    @Override
    @Transactional
    public boolean batchDelete(TAlertRulesDeleteDTO tAlertRulesDeleteDTO) {
        TAlertRulesBO tAlertRulesBO = CglibUtil.convertObj(tAlertRulesDeleteDTO, TAlertRulesBO::new);
        // 获取要删除记录的customerId，用于更新缓存
        List<TAlertRules> toDelete = tAlertRulesService.listByIds(tAlertRulesBO.getIds());
        boolean result = tAlertRulesService.removeBatchByIds(tAlertRulesBO.getIds(), true);
        if (result && !toDelete.isEmpty()) {
            Long customerId = toDelete.get(0).getCustomerId();
            updateAlertRulesCache(customerId);
        }
        return result;
    }
    
    /**
     * 更新告警规则缓存 - 使用AlertRulesCacheManager
     * @param customerId 客户ID
     */
    private void updateAlertRulesCache(Long customerId) {
        if (customerId == null) {
            return;
        }
        
        try {
            // 使用AlertRulesCacheManager进行异步缓存更新
            alertRulesCacheManager.updateAlertRulesCacheAsync(customerId);
            
            // 发布规则变更事件
            alertRulesCacheManager.publishRuleChangeEvent(customerId, "update");
            
            System.out.println("✅ 触发告警规则缓存更新: customerId=" + customerId + " (通过AlertRulesCacheManager)");
            
        } catch (Exception e) {
            System.err.println("❌ 触发告警规则缓存更新失败: customerId=" + customerId + ", error=" + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * 预处理告警规则数据 - 用于更新
     */
    private void preprocessAlertRuleForUpdate(TAlertRulesUpdateDTO dto) {
        // 如果是复合规则，设置正确的ruleType
        if ("COMPOSITE".equals(dto.getRuleCategory())) {
            dto.setRuleType("composite");
            // 对于复合规则，physicalSign应该为空或者为"composite"
            if (dto.getPhysicalSign() == null || dto.getPhysicalSign().trim().isEmpty()) {
                dto.setPhysicalSign("composite");
            }
        }
        
        // 处理严重级别字段的映射
        if (dto.getLevel() != null && dto.getSeverityLevel() == null) {
            // 将前端的level字段映射到severityLevel
            switch (dto.getLevel().toUpperCase()) {
                case "LOW": case "MINOR":
                    dto.setSeverityLevel("minor");
                    break;
                case "MEDIUM": case "MODERATE":
                    dto.setSeverityLevel("moderate");
                    break;
                case "HIGH": case "MAJOR":
                    dto.setSeverityLevel("major");
                    break;
                case "CRITICAL": case "SEVERE":
                    dto.setSeverityLevel("critical");
                    break;
                default:
                    dto.setSeverityLevel("moderate");
            }
        }
        
        // 设置默认值
        if (dto.getIsEnabled() == null) {
            dto.setIsEnabled(true);
        }
        
        // 为复合规则生成唯一的物理指标标识
        if ("COMPOSITE".equals(dto.getRuleCategory()) && dto.getConditions() != null) {
            // 基于条件内容生成唯一标识，避免重复
            String conditionHash = String.valueOf(dto.getConditions().hashCode());
            dto.setPhysicalSign("composite_" + Math.abs(conditionHash.hashCode() % 10000));
        }
        
        // 处理时间字段转换 - 从ISO datetime字符串提取时间部分
        if (dto.getEffectiveTimeStart() != null) {
            dto.setEffectiveTimeStart(extractTimeFromDateTimeString(dto.getEffectiveTimeStart()));
        }
        if (dto.getEffectiveTimeEnd() != null) {
            dto.setEffectiveTimeEnd(extractTimeFromDateTimeString(dto.getEffectiveTimeEnd()));
        }
    }
    
    /**
     * 预处理告警规则数据 - 用于新增
     */
    private void preprocessAlertRule(TAlertRulesAddDTO dto) {
        // 如果是复合规则，设置正确的ruleType
        if ("COMPOSITE".equals(dto.getRuleCategory())) {
            dto.setRuleType("composite");
            // 对于复合规则，physicalSign应该为空或者为"composite"
            if (dto.getPhysicalSign() == null || dto.getPhysicalSign().trim().isEmpty()) {
                dto.setPhysicalSign("composite");
            }
        }
        
        // 处理严重级别字段的映射
        if (dto.getLevel() != null && dto.getSeverityLevel() == null) {
            // 将前端的level字段映射到severityLevel
            switch (dto.getLevel().toUpperCase()) {
                case "LOW": case "MINOR":
                    dto.setSeverityLevel("minor");
                    break;
                case "MEDIUM": case "MODERATE":
                    dto.setSeverityLevel("moderate");
                    break;
                case "HIGH": case "MAJOR":
                    dto.setSeverityLevel("major");
                    break;
                case "CRITICAL": case "SEVERE":
                    dto.setSeverityLevel("critical");
                    break;
                default:
                    dto.setSeverityLevel("moderate");
            }
        }
        
        // 设置默认值
        if (dto.getIsEnabled() == null) {
            dto.setIsEnabled(true);
        }
        
        // 为复合规则生成唯一的物理指标标识
        if ("COMPOSITE".equals(dto.getRuleCategory()) && dto.getConditions() != null) {
            // 基于条件内容生成唯一标识，避免重复
            String conditionHash = String.valueOf(dto.getConditions().hashCode());
            dto.setPhysicalSign("composite_" + Math.abs(conditionHash.hashCode() % 10000));
        }
        
        // 处理时间字段转换 - 从ISO datetime字符串提取时间部分
        if (dto.getEffectiveTimeStart() != null) {
            dto.setEffectiveTimeStart(extractTimeFromDateTimeString(dto.getEffectiveTimeStart()));
        }
        if (dto.getEffectiveTimeEnd() != null) {
            dto.setEffectiveTimeEnd(extractTimeFromDateTimeString(dto.getEffectiveTimeEnd()));
        }
    }
    
    /**
     * 检查是否存在重复的告警规则
     */
    private boolean isDuplicateRule(TAlertRulesAddDTO dto) {
        QueryWrapper<TAlertRules> wrapper = new QueryWrapper<>();
        wrapper.eq("customer_id", dto.getCustomerId())
               .eq("rule_type", dto.getRuleType() != null ? dto.getRuleType() : "metric")
               .eq("physical_sign", dto.getPhysicalSign() != null ? dto.getPhysicalSign() : "")
               .eq("severity_level", dto.getSeverityLevel() != null ? dto.getSeverityLevel() : "moderate");
        
        return tAlertRulesService.count(wrapper) > 0;
    }
    
    /**
     * 从datetime字符串中提取时间部分
     * 支持格式: "2025-09-12T01:00:00.000Z" -> "01:00:00"
     */
    private String extractTimeFromDateTimeString(String dateTimeString) {
        if (dateTimeString == null || dateTimeString.trim().isEmpty()) {
            return null;
        }
        
        try {
            // 如果已经是时间格式，直接返回
            if (dateTimeString.matches("^\\d{2}:\\d{2}:\\d{2}$")) {
                return dateTimeString;
            }
            
            // 处理ISO 8601格式的datetime字符串
            if (dateTimeString.contains("T")) {
                ZonedDateTime zonedDateTime = ZonedDateTime.parse(dateTimeString);
                LocalTime localTime = zonedDateTime.toLocalTime();
                return localTime.format(DateTimeFormatter.ofPattern("HH:mm:ss"));
            }
            
            // 如果包含空格，可能是 "yyyy-MM-dd HH:mm:ss" 格式
            if (dateTimeString.contains(" ")) {
                String[] parts = dateTimeString.split(" ");
                if (parts.length >= 2) {
                    return parts[1].substring(0, Math.min(parts[1].length(), 8)); // 截取时间部分
                }
            }
            
            return dateTimeString; // 其他情况直接返回原值
        } catch (Exception e) {
            System.err.println("解析时间字符串失败: " + dateTimeString + ", error: " + e.getMessage());
            return null;
        }
    }

}