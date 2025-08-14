/*
 * All Rights Reserved: Copyright [2024] [Zhuang Pan (paynezhuang@gmail.com)]
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
import com.ljwx.modules.health.domain.entity.THealthBaseline;
import java.util.List;

/**
 * 用户健康基线表：支持按日/周/月/年记录每个体征的基线统计值 BO 业务处理对象
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.domain.bo.THealthBaselineBO
 * @CreateTime 2025-05-04 - 14:13:02
 */

@Data
public class THealthBaselineBO extends THealthBaseline {

    /**
     * Ids
     */
    private List<Long> ids;

}