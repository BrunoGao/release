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

import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.health.domain.dto.alert.info.TAlertInfoAddDTO;
import com.ljwx.modules.health.domain.dto.alert.info.TAlertInfoDeleteDTO;
import com.ljwx.modules.health.domain.dto.alert.info.TAlertInfoSearchDTO;
import com.ljwx.modules.health.domain.dto.alert.info.TAlertInfoUpdateDTO;
import com.ljwx.modules.health.domain.vo.TAlertInfoVO;

/**
 *  门面接口层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.ITAlertInfoFacade
 * @CreateTime 2024-10-27 - 20:37:23
 */

public interface ITAlertInfoFacade {

    /**
     *  - 分页查询
     *
     * @param pageQuery        分页对象
     * @param tAlertInfoSearchDTO 查询对象
     * @return {@link RPage} 查询结果
     * @author payne.zhuang
     * @CreateTime 2024-10-27 - 20:37:23
     */
    RPage<TAlertInfoVO> listTAlertInfoPage(PageQuery pageQuery, TAlertInfoSearchDTO tAlertInfoSearchDTO);

    /**
     * 根据 ID 获取详情信息
     *
     * @param id ID
     * @return {@link TAlertInfoVO}  VO 对象
     * @author payne.zhuang
     * @CreateTime 2024-10-27 - 20:37:23
     */
    TAlertInfoVO get(Long id);

    /**
     * 新增
     *
     * @param tAlertInfoAddDTO 新增 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2024-10-27 - 20:37:23
     */
    boolean add(TAlertInfoAddDTO tAlertInfoAddDTO);

    /**
     * 编辑更新信息
     *
     * @param tAlertInfoUpdateDTO 编辑更新 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2024-10-27 - 20:37:23
     */
    boolean update(TAlertInfoUpdateDTO tAlertInfoUpdateDTO);

    /**
     * 批量删除信息
     *
     * @param tAlertInfoDeleteDTO 删除 DTO 对象
     * @return @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2024-10-27 - 20:37:23
     */
    boolean batchDelete(TAlertInfoDeleteDTO tAlertInfoDeleteDTO);

}