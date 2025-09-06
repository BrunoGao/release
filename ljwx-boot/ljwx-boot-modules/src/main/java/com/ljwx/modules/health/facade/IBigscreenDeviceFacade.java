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

package com.ljwx.modules.health.facade;

import com.ljwx.modules.health.domain.dto.v1.device.*;
import com.ljwx.modules.health.domain.vo.v1.device.*;

import java.util.List;

/**
 * Bigscreen Device Facade Interface - 大屏设备管理门面接口
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.facade.IBigscreenDeviceFacade
 * @CreateTime 2025-01-01 - 10:00:00
 */
public interface IBigscreenDeviceFacade {

    /**
     * 获取设备用户信息
     */
    DeviceUserInfoVO getDeviceUserInfo(String deviceSn);

    /**
     * 获取设备状态信息
     */
    DeviceStatusVO getDeviceStatus(String deviceSn);

    /**
     * 获取设备用户组织信息
     */
    DeviceUserOrganizationVO getDeviceUserOrganization(String deviceSn);

    /**
     * 获取用户资料
     */
    UserProfileVO getUserProfile(String userId);

    /**
     * 获取用户列表
     */
    List<UserVO> getUsers(UserQueryDTO query);
}