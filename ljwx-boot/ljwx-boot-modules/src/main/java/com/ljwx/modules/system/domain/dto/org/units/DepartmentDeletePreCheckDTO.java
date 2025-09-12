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

package com.ljwx.modules.system.domain.dto.org.units;

import lombok.Builder;
import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 部门删除前置检查结果DTO
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.domain.dto.org.units.DepartmentDeletePreCheckDTO
 * @CreateTime 2025-09-12 - 16:35:30
 */
@Data
@Builder
public class DepartmentDeletePreCheckDTO {

    /**
     * 是否可以安全删除（没有用户和设备）
     */
    private Boolean canSafeDelete;

    /**
     * 需要删除的部门信息
     */
    private List<DepartmentInfo> departmentsToDelete;

    /**
     * 需要删除的用户信息
     */
    private List<UserInfo> usersToDelete;

    /**
     * 需要释放的设备信息
     */
    private List<DeviceInfo> devicesToRelease;

    /**
     * 汇总信息
     */
    private SummaryInfo summary;

    @Data
    @Builder
    public static class DepartmentInfo {
        private Long orgId;
        private String orgName;
        private Integer level;
        private Integer userCount;
        private Integer deviceCount;
    }

    @Data
    @Builder
    public static class UserInfo {
        private Long userId;
        private String userName;
        private String realName;
        private String orgName;
        private String deviceSn;
        private Boolean hasDevice;
    }

    @Data
    @Builder
    public static class DeviceInfo {
        private String deviceSn;
        private String deviceType;
        private Long boundUserId;
        private String boundUserName;
        private String orgName;
    }

    @Data
    @Builder
    public static class SummaryInfo {
        private Integer totalDepartments;
        private Integer totalUsers;
        private Integer totalDevices;
        private Integer usersWithDevices;
        private String warningMessage;
    }
}