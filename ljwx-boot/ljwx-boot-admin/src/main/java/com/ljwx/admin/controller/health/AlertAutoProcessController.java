/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 */

package com.ljwx.admin.controller.health;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import cn.dev33.satoken.annotation.SaCheckPermission;
import com.ljwx.modules.health.domain.entity.TAlertRules;
import com.ljwx.modules.health.domain.dto.AlertRuleQueryDTO;
import com.ljwx.modules.health.domain.dto.AlertRuleUpdateDTO;
import com.ljwx.modules.health.domain.vo.AlertRuleStatsVO;
import com.ljwx.modules.health.service.ITAlertRulesService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import jakarta.servlet.http.HttpServletResponse;
import java.time.LocalDateTime;
import java.util.*;

/**
 * 告警自动处理规则管理控制器
 * 
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName AlertAutoProcessController
 * @CreateTime 2025-09-10
 */
@Tag(name = "告警自动处理规则管理", description = "告警自动处理规则的增删改查和统计功能")
@Slf4j
@RestController
@RequestMapping("/admin/health/alert-auto-process")
@RequiredArgsConstructor
public class AlertAutoProcessController {

    private final ITAlertRulesService alertRulesService;

    /**
     * 查询告警自动处理规则列表
     */
    @Operation(summary = "查询告警自动处理规则列表", description = "分页查询告警自动处理规则")
    @SaCheckPermission("alert:rules:query")
    @GetMapping("/list")
    public Result<RPage<TAlertRules>> list(AlertRuleQueryDTO queryDTO, PageQuery pageQuery) {
        try {
            LambdaQueryWrapper<TAlertRules> queryWrapper = new LambdaQueryWrapper<TAlertRules>()
                .like(queryDTO.getPhysicalSign() != null, TAlertRules::getPhysicalSign, queryDTO.getPhysicalSign())
                .eq(queryDTO.getRuleType() != null, TAlertRules::getRuleType, queryDTO.getRuleType())
                .eq(queryDTO.getSeverityLevel() != null, TAlertRules::getSeverityLevel, queryDTO.getSeverityLevel())
                .eq(queryDTO.getIsEnabled() != null, TAlertRules::getIsEnabled, queryDTO.getIsEnabled())
                .eq(queryDTO.getAutoProcessEnabled() != null, TAlertRules::getAutoProcessEnabled, queryDTO.getAutoProcessEnabled())
                .eq(queryDTO.getCustomerId() != null, TAlertRules::getCustomerId, queryDTO.getCustomerId())
                .orderByDesc(TAlertRules::getUpdateTime);

            IPage<TAlertRules> page = new Page<>(pageQuery.getPage(), pageQuery.getPageSize());
            IPage<TAlertRules> result = alertRulesService.page(page, queryWrapper);
            return Result.success("查询成功", RPage.build(result));
            
        } catch (Exception e) {
            log.error("查询告警规则列表失败", e);
            return Result.failure("查询失败: " + e.getMessage());
        }
    }

    /**
     * 获取告警自动处理规则详细信息
     */
    @Operation(summary = "获取告警自动处理规则详情")
    @SaCheckPermission("alert:rules:query")
    @GetMapping("/{id}")
    public Result<TAlertRules> getInfo(@Parameter(description = "规则ID") @PathVariable("id") Long id) {
        try {
            TAlertRules rule = alertRulesService.getById(id);
            if (rule == null) {
                return Result.failure("告警规则不存在");
            }
            return Result.success("操作成功", rule);
            
        } catch (Exception e) {
            log.error("获取告警规则详情失败: ruleId={}", id, e);
            return Result.failure("获取规则详情失败: " + e.getMessage());
        }
    }

    /**
     * 新增告警自动处理规则
     */
    @Operation(summary = "新增告警自动处理规则")
    @SaCheckPermission("alert:rules:add")
    @PostMapping
    public Result<Void> add(@Validated @RequestBody TAlertRules alertRule) {
        try {
            // 设置创建信息
            alertRule.setCreateTime(LocalDateTime.now());
            alertRule.setUpdateTime(LocalDateTime.now());
            
            // 默认值设置
            if (alertRule.getAutoProcessEnabled() == null) {
                alertRule.setAutoProcessEnabled(false);
            }
            if (alertRule.getAutoProcessDelaySeconds() == null) {
                alertRule.setAutoProcessDelaySeconds(0);
            }
            if (alertRule.getAutoResolveThresholdCount() == null) {
                alertRule.setAutoResolveThresholdCount(1);
            }
            if (alertRule.getSuppressDurationMinutes() == null) {
                alertRule.setSuppressDurationMinutes(60);
            }

            boolean saved = alertRulesService.save(alertRule);
            if (saved) {
                log.info("新增告警自动处理规则成功: ruleId={}, ruleType={}, action={}", 
                    alertRule.getId(), alertRule.getRuleType(), alertRule.getAutoProcessAction());
                return Result.success("新增成功");
            } else {
                return Result.failure("新增告警规则失败");
            }
            
        } catch (Exception e) {
            log.error("新增告警规则失败", e);
            return Result.failure("新增规则失败: " + e.getMessage());
        }
    }

    /**
     * 修改告警自动处理规则
     */
    @Operation(summary = "修改告警自动处理规则")
    @SaCheckPermission("alert:rules:edit")
    @PutMapping
    public Result<Void> edit(@Validated @RequestBody AlertRuleUpdateDTO updateDTO) {
        try {
            TAlertRules alertRule = alertRulesService.getById(updateDTO.getId());
            if (alertRule == null) {
                return Result.failure("告警规则不存在");
            }

            // 更新字段
            if (updateDTO.getPhysicalSign() != null) {
                alertRule.setPhysicalSign(updateDTO.getPhysicalSign());
            }
            if (updateDTO.getThresholdMin() != null) {
                alertRule.setThresholdMin(updateDTO.getThresholdMin());
            }
            if (updateDTO.getThresholdMax() != null) {
                alertRule.setThresholdMax(updateDTO.getThresholdMax());
            }
            if (updateDTO.getSeverityLevel() != null) {
                alertRule.setSeverityLevel(updateDTO.getSeverityLevel());
            }
            if (updateDTO.getAutoProcessEnabled() != null) {
                alertRule.setAutoProcessEnabled(updateDTO.getAutoProcessEnabled());
            }
            if (updateDTO.getAutoProcessAction() != null) {
                alertRule.setAutoProcessAction(updateDTO.getAutoProcessAction());
            }
            if (updateDTO.getAutoProcessDelaySeconds() != null) {
                alertRule.setAutoProcessDelaySeconds(updateDTO.getAutoProcessDelaySeconds());
            }
            if (updateDTO.getAutoResolveThresholdCount() != null) {
                alertRule.setAutoResolveThresholdCount(updateDTO.getAutoResolveThresholdCount());
            }
            if (updateDTO.getSuppressDurationMinutes() != null) {
                alertRule.setSuppressDurationMinutes(updateDTO.getSuppressDurationMinutes());
            }
            if (updateDTO.getIsEnabled() != null) {
                alertRule.setIsEnabled(updateDTO.getIsEnabled());
            }

            alertRule.setUpdateTime(LocalDateTime.now());

            boolean updated = alertRulesService.updateById(alertRule);
            if (updated) {
                log.info("修改告警自动处理规则成功: ruleId={}, autoEnabled={}, action={}", 
                    alertRule.getId(), alertRule.getAutoProcessEnabled(), alertRule.getAutoProcessAction());
                return Result.success("修改成功");
            } else {
                return Result.failure("修改告警规则失败");
            }
            
        } catch (Exception e) {
            log.error("修改告警规则失败: ruleId={}", updateDTO.getId(), e);
            return Result.failure("修改规则失败: " + e.getMessage());
        }
    }

    /**
     * 删除告警自动处理规则
     */
    @Operation(summary = "删除告警自动处理规则")
    @SaCheckPermission("alert:rules:remove")
    @DeleteMapping("/{ids}")
    public Result<Void> remove(@Parameter(description = "规则ID,多个用逗号分隔") @PathVariable Long[] ids) {
        try {
            boolean removed = alertRulesService.removeByIds(Arrays.asList(ids));
            if (removed) {
                log.info("删除告警自动处理规则成功: ruleIds={}", Arrays.toString(ids));
                return Result.success("删除成功");
            } else {
                return Result.failure("删除告警规则失败");
            }
            
        } catch (Exception e) {
            log.error("删除告警规则失败: ruleIds={}", Arrays.toString(ids), e);
            return Result.failure("删除规则失败: " + e.getMessage());
        }
    }

    /**
     * 批量启用/禁用自动处理
     */
    @Operation(summary = "批量启用/禁用自动处理")
    @SaCheckPermission("alert:rules:edit")
    @PutMapping("/toggle-auto-process")
    public Result<Void> toggleAutoProcess(@RequestBody Map<String, Object> params) {
        try {
            @SuppressWarnings("unchecked")
            List<Long> ids = (List<Long>) params.get("ids");
            Boolean enabled = (Boolean) params.get("enabled");
            
            if (ids == null || ids.isEmpty()) {
                return Result.failure("请选择要操作的规则");
            }

            LambdaQueryWrapper<TAlertRules> queryWrapper = new LambdaQueryWrapper<TAlertRules>()
                .in(TAlertRules::getId, ids);
            
            List<TAlertRules> rules = alertRulesService.list(queryWrapper);
            for (TAlertRules rule : rules) {
                rule.setAutoProcessEnabled(enabled);
                rule.setUpdateTime(LocalDateTime.now());
            }

            boolean updated = alertRulesService.updateBatchById(rules);
            if (updated) {
                log.info("批量{}自动处理成功: ruleIds={}", enabled ? "启用" : "禁用", ids);
                return Result.success("批量操作成功");
            } else {
                return Result.failure("操作失败");
            }
            
        } catch (Exception e) {
            log.error("批量操作自动处理失败", e);
            return Result.failure("操作失败: " + e.getMessage());
        }
    }

    /**
     * 获取自动处理规则统计
     */
    @Operation(summary = "获取自动处理规则统计")
    @SaCheckPermission("alert:rules:query")
    @GetMapping("/stats")
    public Result<AlertRuleStatsVO> getStats(@RequestParam(required = false) Long customerId) {
        try {
            LambdaQueryWrapper<TAlertRules> queryWrapper = new LambdaQueryWrapper<TAlertRules>()
                .eq(customerId != null, TAlertRules::getCustomerId, customerId);

            List<TAlertRules> allRules = alertRulesService.list(queryWrapper);
            
            AlertRuleStatsVO stats = AlertRuleStatsVO.builder()
                .totalRules((long) allRules.size())
                .enabledRules(allRules.stream().mapToLong(r -> r.getIsEnabled() ? 1 : 0).sum())
                .autoProcessEnabledRules(allRules.stream().mapToLong(r -> Boolean.TRUE.equals(r.getAutoProcessEnabled()) ? 1 : 0).sum())
                .build();

            // 按严重程度分组统计
            Map<String, Long> severityStats = new HashMap<>();
            allRules.stream()
                .filter(r -> Boolean.TRUE.equals(r.getAutoProcessEnabled()))
                .forEach(r -> {
                    String severity = r.getSeverityLevel() != null ? r.getSeverityLevel() : "unknown";
                    severityStats.put(severity, severityStats.getOrDefault(severity, 0L) + 1);
                });
            stats.setSeverityLevelStats(severityStats);
            
            // 按规则类型分组统计
            Map<String, Long> ruleTypeStats = new HashMap<>();
            allRules.stream()
                .filter(r -> Boolean.TRUE.equals(r.getAutoProcessEnabled()))
                .forEach(r -> {
                    String ruleType = r.getRuleType() != null ? r.getRuleType() : "unknown";
                    ruleTypeStats.put(ruleType, ruleTypeStats.getOrDefault(ruleType, 0L) + 1);
                });
            stats.setRuleTypeStats(ruleTypeStats);

            return Result.success("查询成功", stats);
            
        } catch (Exception e) {
            log.error("获取自动处理规则统计失败", e);
            return Result.failure("获取统计失败: " + e.getMessage());
        }
    }

    /**
     * 导出告警自动处理规则
     */
    @Operation(summary = "导出告警自动处理规则")
    @SaCheckPermission("alert:rules:export")
    @PostMapping("/export")
    public Result<Void> export(HttpServletResponse response, AlertRuleQueryDTO queryDTO) {
        try {
            LambdaQueryWrapper<TAlertRules> queryWrapper = new LambdaQueryWrapper<TAlertRules>()
                .like(queryDTO.getPhysicalSign() != null, TAlertRules::getPhysicalSign, queryDTO.getPhysicalSign())
                .eq(queryDTO.getRuleType() != null, TAlertRules::getRuleType, queryDTO.getRuleType())
                .eq(queryDTO.getSeverityLevel() != null, TAlertRules::getSeverityLevel, queryDTO.getSeverityLevel())
                .eq(queryDTO.getIsEnabled() != null, TAlertRules::getIsEnabled, queryDTO.getIsEnabled())
                .eq(queryDTO.getAutoProcessEnabled() != null, TAlertRules::getAutoProcessEnabled, queryDTO.getAutoProcessEnabled())
                .orderByDesc(TAlertRules::getUpdateTime);

            List<TAlertRules> list = alertRulesService.list(queryWrapper);
            // TODO: Implement Excel export functionality
            log.info("导出告警规则: {} 条记录", list.size());
            return Result.success("导出成功");
            
        } catch (Exception e) {
            log.error("导出告警规则失败", e);
            return Result.failure("导出失败: " + e.getMessage());
        }
    }

    /**
     * 获取自动处理动作选项
     */
    @Operation(summary = "获取自动处理动作选项")
    @GetMapping("/action-options")
    public Result<Map<String, String>> getActionOptions() {
        Map<String, String> options = new LinkedHashMap<>();
        options.put("AUTO_RESOLVE", "自动解决");
        options.put("AUTO_ACKNOWLEDGE", "自动确认");
        options.put("AUTO_ESCALATE", "自动升级");
        options.put("AUTO_SUPPRESS", "自动抑制");
        
        return Result.success("操作成功", options);
    }

    /**
     * 获取严重程度选项
     */
    @Operation(summary = "获取严重程度选项")
    @GetMapping("/severity-options")
    public Result<Map<String, String>> getSeverityOptions() {
        Map<String, String> options = new LinkedHashMap<>();
        options.put("critical", "Critical");
        options.put("major", "Major");
        options.put("minor", "Minor");
        options.put("info", "Info");
        
        return Result.success("操作成功", options);
    }
}