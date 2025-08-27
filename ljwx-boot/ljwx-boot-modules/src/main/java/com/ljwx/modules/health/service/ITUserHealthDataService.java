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

package com.ljwx.modules.health.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.IService;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.ljwx.modules.health.domain.dto.user.health.data.TUserHealthDataSearchDTO;
import org.springframework.http.ResponseEntity;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import com.ljwx.modules.health.domain.vo.HealthDataPageVO;
/**
 *  Service 服务接口层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.ITUserHealthDataService
 * @CreateTime 2024-12-15 - 22:04:51
 */

public interface ITUserHealthDataService extends IService<TUserHealthData> {

    /**
     *  - 分页查询
     *
     * @param pageQuery 分页对象
     * @param tUserHealthDataBO BO 查询对象
     * @return {@link Map} 分页结果
     * @author payne.zhuang
     * @CreateTime 2024-12-15 - 22:04:51
     */
    HealthDataPageVO<Map<String,Object>> listTUserHealthDataPage(PageQuery pageQuery, TUserHealthDataSearchDTO tUserHealthDataSearchDTO);

    /**
     * 获取用户健康数据
     *
     * @param userId 用户ID
     * @param deviceSn 设备SN
     * @param startDate 开始日期
     * @param endDate 结束日期
     * @param timeType 时间类型
     * @return {@link List} 健康数据列表
     */
    ResponseEntity<Object> getUserHealthData(String departmentInfo, String userId, LocalDateTime startDate, LocalDateTime endDate, String timeType);
}
