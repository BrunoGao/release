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

package com.ljwx.modules.system.domain.bo;

import com.ljwx.modules.system.domain.entity.SysPosition;
import lombok.Data;

import java.io.Serial;
import java.util.List;

/**
 * 岗位管理 BO 业务处理对象
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.domain.bo.SysPositionBO
 * @CreateTime 2024-06-27 - 21:26:12
 */

@Data
public class SysPositionBO extends SysPosition {

    @Serial
    private static final long serialVersionUID = 4678000186142372913L;

    /**
     * Ids
     */
    private List<Long> ids;

    /**
     * 组织ID
     */
    private Long orgId;

    /**
     * 组织ID列表 (用于权限过滤)
     */
    private List<Long> orgIds;

    /**
     * 租户ID (0表示全局岗位，所有租户可见)
     */
    private Long customerId;

    /**
     * 租户ID列表 (用于多租户过滤)
     */
    private List<Long> customerIds;

}