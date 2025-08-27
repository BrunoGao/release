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
import com.ljwx.modules.health.domain.entity.TAlertRules;
import java.util.List;

/**
 *  BO 业务处理对象
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.domain.bo.TAlertRulesBO
 * @CreateTime 2025-02-13 - 14:59:34
 */

@Data
public class TAlertRulesBO extends TAlertRules {

    /**
     * Ids
     */
    private List<Long> ids;

    private Long customerId;

}