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

package com.ljwx.modules.health.repository.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.modules.health.domain.bo.TDeviceInfoBO;
import com.ljwx.modules.health.domain.entity.TDeviceInfo;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 *  Mapper 接口层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.repository.mapper.TDeviceInfoMapper
 * @CreateTime 2024-10-21 - 20:23:09
 */

public interface TDeviceInfoMapper extends BaseMapper<TDeviceInfo> {


    IPage<TDeviceInfo> listDeviceInfoWithUserName(IPage<TDeviceInfo> page, @Param("bo") TDeviceInfoBO tDeviceInfoBO);
}
