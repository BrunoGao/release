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

import com.ljwx.modules.health.domain.dto.v1.alert.*;
import com.ljwx.modules.health.domain.vo.v1.alert.*;

import java.util.List;

/**
 * Bigscreen Alert Facade Interface - 大屏告警管理门面接口
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.facade.IBigscreenAlertFacade
 * @CreateTime 2025-01-01 - 10:00:00
 */
public interface IBigscreenAlertFacade {

    /**
     * 获取用户告警
     */
    List<UserAlertVO> getUserAlerts(UserAlertQueryDTO query);

    /**
     * 获取个人告警
     */
    List<PersonalAlertVO> getPersonalAlerts(PersonalAlertQueryDTO query);

    /**
     * 确认告警
     */
    boolean acknowledgeAlert(AlertAcknowledgeRequestDTO request);

    /**
     * 处理告警
     */
    boolean dealAlert(Long alertId);

    /**
     * 获取用户消息
     */
    List<UserMessageVO> getUserMessages(UserMessageQueryDTO query);
}