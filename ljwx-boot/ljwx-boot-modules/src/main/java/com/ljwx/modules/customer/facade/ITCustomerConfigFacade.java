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
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigAddDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigDeleteDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigSearchDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigUpdateDTO;
import com.ljwx.modules.customer.domain.vo.TCustomerConfigVO;

/**
 *  门面接口层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.customer.facade.ITCustomerConfigFacade
 * @CreateTime 2024-12-29 - 15:33:30
 */

public interface ITCustomerConfigFacade {

    /**
     *  - 分页查询
     *
     * @param pageQuery        分页对象
     * @param tCustomerConfigSearchDTO 查询对象
     * @return {@link RPage} 查询结果
     * @author payne.zhuang
     * @CreateTime 2024-12-29 - 15:33:30
     */
    RPage<TCustomerConfigVO> listTCustomerConfigPage(PageQuery pageQuery, TCustomerConfigSearchDTO tCustomerConfigSearchDTO);

    /**
     * 根据 ID 获取详情信息
     *
     * @param id ID
     * @return {@link TCustomerConfigVO}  VO 对象
     * @author payne.zhuang
     * @CreateTime 2024-12-29 - 15:33:30
     */
    TCustomerConfigVO get(Long id);

    /**
     * 新增
     *
     * @param tCustomerConfigAddDTO 新增 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2024-12-29 - 15:33:30
     */
    boolean add(TCustomerConfigAddDTO tCustomerConfigAddDTO);

    /**
     * 编辑更新信息
     *
     * @param tCustomerConfigUpdateDTO 编辑更新 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2024-12-29 - 15:33:30
     */
    boolean update(TCustomerConfigUpdateDTO tCustomerConfigUpdateDTO);

    /**
     * 批量删除信息
     *
     * @param tCustomerConfigDeleteDTO 删除 DTO 对象
     * @return @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2024-12-29 - 15:33:30
     */
    boolean batchDelete(TCustomerConfigDeleteDTO tCustomerConfigDeleteDTO);

}