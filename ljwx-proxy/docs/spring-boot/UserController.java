package com.ljwx.api.v1.controller;

import com.ljwx.api.v1.dto.*;
import com.ljwx.api.v1.service.UserService;
import com.ljwx.common.response.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 用户管理API控制器 v1
 * 
 * @author LJWX Team
 * @version 1.0.0
 */
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Tag(name = "User API", description = "用户管理相关接口")
public class UserController {

    private final UserService userService;

    /**
     * 获取用户资料
     */
    @GetMapping("/profile")
    @Operation(summary = "获取用户资料", description = "获取用户的详细资料信息")
    public ApiResponse<UserProfileDTO> getUserProfile(
            @Parameter(description = "用户ID", required = true) @RequestParam String userId) {
        
        UserProfileDTO result = userService.getUserProfile(userId);
        return ApiResponse.success(result);
    }

    /**
     * 获取组织下的用户列表
     */
    @GetMapping
    @Operation(summary = "获取用户列表", description = "获取指定组织下的用户列表")
    public ApiResponse<List<UserDTO>> getUsers(
            @Parameter(description = "组织ID", required = true) @RequestParam String orgId) {
        
        List<UserDTO> result = userService.getUsersByOrgId(orgId);
        return ApiResponse.success(result);
    }
}