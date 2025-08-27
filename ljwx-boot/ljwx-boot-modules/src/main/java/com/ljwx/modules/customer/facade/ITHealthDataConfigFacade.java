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

package com.ljwx.modules.customer.facade;

import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.customer.domain.dto.health.data.config.THealthDataConfigAddDTO;
import com.ljwx.modules.customer.domain.dto.health.data.config.THealthDataConfigDeleteDTO;
import com.ljwx.modules.customer.domain.dto.health.data.config.THealthDataConfigSearchDTO;
import com.ljwx.modules.customer.domain.dto.health.data.config.THealthDataConfigUpdateDTO;
import com.ljwx.modules.customer.domain.vo.THealthDataConfigVO;

/**
 *  门面接口层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.customer.facade.ITHealthDataConfigFacade
 * @CreateTime 2024-12-29 - 15:02:31
 */

public interface ITHealthDataConfigFacade {

    /**
     *  - 分页查询
     *
     * @param pageQuery        分页对象
     * @param tHealthDataConfigSearchDTO 查询对象
     * @return {@link RPage} 查询结果
     * @author payne.zhuang
     * @CreateTime 2024-12-29 - 15:02:31
     */
    RPage<THealthDataConfigVO> listTHealthDataConfigPage(PageQuery pageQuery, THealthDataConfigSearchDTO tHealthDataConfigSearchDTO);

    /**
     * 根据 ID 获取详情信息
     *
     * @param id ID
     * @return {@link THealthDataConfigVO}  VO 对象
     * @author payne.zhuang
     * @CreateTime 2024-12-29 - 15:02:31
     */
    THealthDataConfigVO get(Long id);

    /**
     * 新增
     *
     * @param tHealthDataConfigAddDTO 新增 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2024-12-29 - 15:02:31
     */
    boolean add(THealthDataConfigAddDTO tHealthDataConfigAddDTO);

    /**
     * 编辑更新信息
     *
     * @param tHealthDataConfigUpdateDTO 编辑更新 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2024-12-29 - 15:02:31
     */
    boolean update(THealthDataConfigUpdateDTO tHealthDataConfigUpdateDTO);

    /**
     * 批量删除信息
     *
     * @param tHealthDataConfigDeleteDTO 删除 DTO 对象
     * @return @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2024-12-29 - 15:02:31
     */
    boolean batchDelete(THealthDataConfigDeleteDTO tHealthDataConfigDeleteDTO);

}