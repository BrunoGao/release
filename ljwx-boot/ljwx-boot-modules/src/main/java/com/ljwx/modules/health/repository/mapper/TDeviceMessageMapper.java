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

import com.ljwx.modules.health.domain.entity.TDeviceMessage;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 *  Mapper 接口层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.repository.mapper.TDeviceMessageMapper
 * @CreateTime 2024-10-24 - 13:07:24
 */

public interface TDeviceMessageMapper extends BaseMapper<TDeviceMessage> {

    /**
     * 检查用户是否已确认消息
     * 基于真实数据库表结构：delivery_status = 'ACKNOWLEDGED'
     */
    @Select("SELECT COUNT(*) FROM t_device_message_detail " +
            "WHERE message_id = #{messageId} AND target_id = #{userId} " +
            "AND delivery_status = 'ACKNOWLEDGED' AND is_deleted = 0")
    Long checkUserAcknowledgement(@Param("messageId") Long messageId, @Param("userId") String userId);

    /**
     * 查询已确认消息的用户ID列表
     * delivery_status = 'ACKNOWLEDGED' 表示已确认
     */
    @Select("SELECT DISTINCT target_id FROM t_device_message_detail " +
            "WHERE message_id = #{messageId} AND delivery_status = 'ACKNOWLEDGED' " +
            "AND target_type = 'USER' AND is_deleted = 0")
    List<String> getAcknowledgedUserIds(@Param("messageId") Long messageId);

    /**
     * 检查t_device_message_detail表是否存在
     */
    @Select("SELECT COUNT(*) FROM information_schema.tables " +
            "WHERE table_schema = DATABASE() AND table_name = 't_device_message_detail'")
    Long checkDetailTableExists();

}