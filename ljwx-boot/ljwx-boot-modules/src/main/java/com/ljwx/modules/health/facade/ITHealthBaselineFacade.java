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

package com.ljwx.modules.health.facade;

import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.health.domain.dto.health.baseline.THealthBaselineAddDTO;
import com.ljwx.modules.health.domain.dto.health.baseline.THealthBaselineDeleteDTO;
import com.ljwx.modules.health.domain.dto.health.baseline.THealthBaselineSearchDTO;
import com.ljwx.modules.health.domain.dto.health.baseline.THealthBaselineUpdateDTO;
import com.ljwx.modules.health.domain.vo.THealthBaselineVO;

/**
 * 用户健康基线表：支持按日/周/月/年记录每个体征的基线统计值 门面接口层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.ITHealthBaselineFacade
 * @CreateTime 2025-05-04 - 14:13:02
 */

public interface ITHealthBaselineFacade {

    /**
     * 用户健康基线表：支持按日/周/月/年记录每个体征的基线统计值 - 分页查询
     *
     * @param pageQuery        分页对象
     * @param tHealthBaselineSearchDTO 查询对象
     * @return {@link RPage} 查询结果
     * @author payne.zhuang
     * @CreateTime 2025-05-04 - 14:13:02
     */
    RPage<THealthBaselineVO> listTHealthBaselinePage(PageQuery pageQuery, THealthBaselineSearchDTO tHealthBaselineSearchDTO);

    /**
     * 根据 ID 获取详情信息
     *
     * @param id 用户健康基线表：支持按日/周/月/年记录每个体征的基线统计值ID
     * @return {@link THealthBaselineVO} 用户健康基线表：支持按日/周/月/年记录每个体征的基线统计值 VO 对象
     * @author payne.zhuang
     * @CreateTime 2025-05-04 - 14:13:02
     */
    THealthBaselineVO get(Long id);

    /**
     * 新增用户健康基线表：支持按日/周/月/年记录每个体征的基线统计值
     *
     * @param tHealthBaselineAddDTO 新增用户健康基线表：支持按日/周/月/年记录每个体征的基线统计值 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-05-04 - 14:13:02
     */
    boolean add(THealthBaselineAddDTO tHealthBaselineAddDTO);

    /**
     * 编辑更新用户健康基线表：支持按日/周/月/年记录每个体征的基线统计值信息
     *
     * @param tHealthBaselineUpdateDTO 编辑更新 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-05-04 - 14:13:02
     */
    boolean update(THealthBaselineUpdateDTO tHealthBaselineUpdateDTO);

    /**
     * 批量删除用户健康基线表：支持按日/周/月/年记录每个体征的基线统计值信息
     *
     * @param tHealthBaselineDeleteDTO 删除 DTO 对象
     * @return @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-05-04 - 14:13:02
     */
    boolean batchDelete(THealthBaselineDeleteDTO tHealthBaselineDeleteDTO);

}