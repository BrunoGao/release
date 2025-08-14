/*
 * All Rights Reserved: Copyright [2024] [Zhuang Pan (brunoGao@gmail.com)]
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

package com.ljwx.modules.health.service;

import lombok.Data;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Device User Mapping Service 服务接口层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @CreateTime 2024-03-20 - 10:00:00
 */
public interface IDeviceUserMappingService {

    /**
     * 根据用户ID和部门ID获取设备序列号列表
     * @param userId 用户ID
     * @param departmentId 部门ID
     * @return 设备序列号列表
     */
    List<String> getDeviceSnList(String userId, String departmentId);

    /**
     * 批量获取设备关联的用户和部门信息
     * @param deviceSns 设备序列号集合
     * @return 设备序列号到用户信息的映射
     */
    Map<String, UserInfo> getDeviceUserInfo(Set<String> deviceSns);

    /**
     * 根据部门ID获取所有关联的设备序列号
     * @param departmentId 部门ID
     * @return 设备序列号列表
     */
    List<String> getDeviceSnListByDepartmentId(String departmentId);

    Map<String, UserInfo> getUserInfoMap(List<String> deviceSnList);

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    class UserInfo {
        private String userId;
        private String userName;
        private String departmentId;
        private String departmentName;
    }
} 