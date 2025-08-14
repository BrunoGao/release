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

package com.ljwx.modules.health.facade;

import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.health.domain.dto.device.message.detail.TDeviceMessageDetailAddDTO;
import com.ljwx.modules.health.domain.dto.device.message.detail.TDeviceMessageDetailDeleteDTO;
import com.ljwx.modules.health.domain.dto.device.message.detail.TDeviceMessageDetailSearchDTO;
import com.ljwx.modules.health.domain.dto.device.message.detail.TDeviceMessageDetailUpdateDTO;
import com.ljwx.modules.health.domain.vo.TDeviceMessageDetailVO;

/**
 *  门面接口层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.ITDeviceMessageDetailFacade
 * @CreateTime 2025-03-05 - 19:57:37
 */

public interface ITDeviceMessageDetailFacade {

    /**
     *  - 分页查询
     *
     * @param pageQuery        分页对象
     * @param tDeviceMessageDetailSearchDTO 查询对象
     * @return {@link RPage} 查询结果
     * @author payne.zhuang
     * @CreateTime 2025-03-05 - 19:57:37
     */
    RPage<TDeviceMessageDetailVO> listTDeviceMessageDetailPage(PageQuery pageQuery, TDeviceMessageDetailSearchDTO tDeviceMessageDetailSearchDTO);

    /**
     * 根据 ID 获取详情信息
     *
     * @param id ID
     * @return {@link TDeviceMessageDetailVO}  VO 对象
     * @author payne.zhuang
     * @CreateTime 2025-03-05 - 19:57:37
     */
    TDeviceMessageDetailVO get(Long id);

    /**
     * 新增
     *
     * @param tDeviceMessageDetailAddDTO 新增 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-03-05 - 19:57:37
     */
    boolean add(TDeviceMessageDetailAddDTO tDeviceMessageDetailAddDTO);

    /**
     * 编辑更新信息
     *
     * @param tDeviceMessageDetailUpdateDTO 编辑更新 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-03-05 - 19:57:37
     */
    boolean update(TDeviceMessageDetailUpdateDTO tDeviceMessageDetailUpdateDTO);

    /**
     * 批量删除信息
     *
     * @param tDeviceMessageDetailDeleteDTO 删除 DTO 对象
     * @return @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-03-05 - 19:57:37
     */
    boolean batchDelete(TDeviceMessageDetailDeleteDTO tDeviceMessageDetailDeleteDTO);

}