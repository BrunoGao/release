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

import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import lombok.Data;

import java.io.Serial;
import java.util.List;

/**
 * 组织/部门/子部门管理 BO 业务处理对象
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.domain.bo.SysOrgUnitsBO
 * @CreateTime 2024-07-16 - 16:35:30
 */

@Data
public class SysOrgUnitsBO extends SysOrgUnits {

    @Serial
    private static final long serialVersionUID = 8969706163115883132L;

    /**
     * Ids
     */
    private List<Long> ids;

    /**
     * 状态
     */
    private String status;

    /**
     * 父ID
     */
    private Long parentId;

    /**
     * ID
     */
    private Long id;

}