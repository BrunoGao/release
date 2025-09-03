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

package com.ljwx.modules.health.domain.bo;

import lombok.Data;
import com.ljwx.modules.health.domain.entity.TDeviceInfo;
import java.util.List;

/**
 *  BO 业务处理对象
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.domain.bo.TDeviceInfoBO
 * @CreateTime 2024-12-14 - 21:31:16
 */

@Data
public class TDeviceInfoBO extends TDeviceInfo {

    /**
     * Ids
     */
    private List<Long> ids;

    private Long customerId;

    private String status;

    private String model;

    private String serialNumber;

    private String chargingStatus;

    private String wearableStatus;

    /**
     * 用户ID字符串(查询条件用)
     */
    private String userIdStr;

    /**
     * 组织ID
     */
    private Long orgId;

}