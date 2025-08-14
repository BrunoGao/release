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
import com.ljwx.modules.health.domain.dto.device.user.TDeviceUserAddDTO;
import com.ljwx.modules.health.domain.dto.device.user.TDeviceUserDeleteDTO;
import com.ljwx.modules.health.domain.dto.device.user.TDeviceUserSearchDTO;
import com.ljwx.modules.health.domain.dto.device.user.TDeviceUserUpdateDTO;
import com.ljwx.modules.health.domain.vo.TDeviceUserVO;

/**
 * 设备与用户关联表 门面接口层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.ITDeviceUserFacade
 * @CreateTime 2025-01-03 - 15:12:29
 */

public interface ITDeviceUserFacade {

    /**
     * 设备与用户关联表 - 分页查询
     *
     * @param pageQuery        分页对象
     * @param tDeviceUserSearchDTO 查询对象
     * @return {@link RPage} 查询结果
     * @author payne.zhuang
     * @CreateTime 2025-01-03 - 15:12:29
     */
    RPage<TDeviceUserVO> listTDeviceUserPage(PageQuery pageQuery, TDeviceUserSearchDTO tDeviceUserSearchDTO);

    /**
     * 根据 ID 获取详情信息
     *
     * @param id 设备与用户关联表ID
     * @return {@link TDeviceUserVO} 设备与用户关联表 VO 对象
     * @author payne.zhuang
     * @CreateTime 2025-01-03 - 15:12:29
     */
    TDeviceUserVO get(Long id);

    /**
     * 新增设备与用户关联表
     *
     * @param tDeviceUserAddDTO 新增设备与用户关联表 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-01-03 - 15:12:29
     */
    boolean add(TDeviceUserAddDTO tDeviceUserAddDTO);

    /**
     * 编辑更新设备与用户关联表信息
     *
     * @param tDeviceUserUpdateDTO 编辑更新 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-01-03 - 15:12:29
     */
    boolean update(TDeviceUserUpdateDTO tDeviceUserUpdateDTO);

    /**
     * 批量删除设备与用户关联表信息
     *
     * @param tDeviceUserDeleteDTO 删除 DTO 对象
     * @return @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-01-03 - 15:12:29
     */
    boolean batchDelete(TDeviceUserDeleteDTO tDeviceUserDeleteDTO);

}