package com.ljwx.api.v1.controller;

import com.ljwx.api.v1.dto.*;
import com.ljwx.api.v1.service.OrganizationService;
import com.ljwx.common.response.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 组织管理API控制器 v1
 * 
 * @author LJWX Team
 * @version 1.0.0
 */
@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
@Tag(name = "Organization API", description = "组织管理相关接口")
public class OrganizationController {

    private final OrganizationService organizationService;

    /**
     * 获取组织统计信息
     */
    @GetMapping("/organizations/statistics")
    @Operation(summary = "获取组织统计信息", description = "获取客户总体统计信息")
    public ApiResponse<OrganizationStatisticsDTO> getOrganizationStatistics(
            @Parameter(description = "客户ID", required = true) @RequestParam("customer_id") String customerId) {
        
        OrganizationStatisticsDTO result = organizationService.getOrganizationStatistics(customerId);
        return ApiResponse.success(result);
    }

    /**
     * 获取部门信息
     */
    @GetMapping("/departments")
    @Operation(summary = "获取部门列表", description = "获取指定组织下的部门列表")
    public ApiResponse<List<DepartmentDTO>> getDepartments(
            @Parameter(description = "组织ID", required = true) @RequestParam String orgId) {
        
        List<DepartmentDTO> result = organizationService.getDepartments(orgId);
        return ApiResponse.success(result);
    }
}