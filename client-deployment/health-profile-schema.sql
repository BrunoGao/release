-- 健康画像管理中心数据表设计
-- 1. 用户健康画像表
CREATE TABLE `t_health_profile` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint(20) NOT NULL COMMENT '用户ID',
  `customer_id` bigint(20) NOT NULL COMMENT '客户ID',
  `org_id` bigint(20) DEFAULT NULL COMMENT '部门ID',
  `health_score` decimal(5,2) DEFAULT NULL COMMENT '健康总评分(0-100)',
  `health_level` varchar(20) DEFAULT NULL COMMENT '健康等级(优秀/良好/一般/差)',
  `baseline_deviation_count` int(11) DEFAULT 0 COMMENT '基线偏离指标数量',
  `risk_indicators` json DEFAULT NULL COMMENT '风险指标列表',
  `profile_data` json DEFAULT NULL COMMENT '画像详细数据',
  `generated_time` datetime DEFAULT NULL COMMENT '画像生成时间',
  `data_range_start` datetime DEFAULT NULL COMMENT '数据统计开始时间',
  `data_range_end` datetime DEFAULT NULL COMMENT '数据统计结束时间',
  `status` tinyint(1) DEFAULT 1 COMMENT '状态(1:有效 0:无效)',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_customer` (`user_id`,`customer_id`),
  KEY `idx_customer_org` (`customer_id`,`org_id`),
  KEY `idx_health_level` (`health_level`),
  KEY `idx_generated_time` (`generated_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户健康画像表';

-- 2. 健康数据基线表  
CREATE TABLE `t_health_data_baseline` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint(20) NOT NULL COMMENT '用户ID',
  `customer_id` bigint(20) NOT NULL COMMENT '客户ID',
  `org_id` bigint(20) DEFAULT NULL COMMENT '部门ID',
  `baseline_type` varchar(20) NOT NULL COMMENT '基线类型(personal/department)',
  `indicator_type` varchar(50) NOT NULL COMMENT '指标类型(heartrate/temperature/etc)',
  `baseline_min` decimal(10,2) DEFAULT NULL COMMENT '基线最小值',
  `baseline_max` decimal(10,2) DEFAULT NULL COMMENT '基线最大值',
  `baseline_avg` decimal(10,2) DEFAULT NULL COMMENT '基线平均值',
  `std_deviation` decimal(10,2) DEFAULT NULL COMMENT '标准差',
  `sample_count` int(11) DEFAULT 0 COMMENT '样本数量',
  `confidence_level` decimal(5,2) DEFAULT NULL COMMENT '置信度',
  `calculation_period` int(11) DEFAULT 30 COMMENT '计算周期(天)',
  `last_calculated` datetime DEFAULT NULL COMMENT '最后计算时间',
  `status` tinyint(1) DEFAULT 1 COMMENT '状态(1:有效 0:无效)',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_baseline` (`user_id`,`customer_id`,`baseline_type`,`indicator_type`),
  KEY `idx_customer_org_type` (`customer_id`,`org_id`,`baseline_type`),
  KEY `idx_indicator` (`indicator_type`),
  KEY `idx_calculated_time` (`last_calculated`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康数据基线表';

-- 3. 健康数据评分表
CREATE TABLE `t_health_data_score` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint(20) NOT NULL COMMENT '用户ID',
  `customer_id` bigint(20) NOT NULL COMMENT '客户ID',
  `org_id` bigint(20) DEFAULT NULL COMMENT '部门ID',
  `score_type` varchar(20) NOT NULL COMMENT '评分类型(personal/department)',
  `indicator_type` varchar(50) NOT NULL COMMENT '指标类型',
  `indicator_score` decimal(5,2) DEFAULT NULL COMMENT '指标得分(0-100)',
  `indicator_weight` decimal(5,2) DEFAULT 1.0 COMMENT '指标权重',
  `weighted_score` decimal(5,2) DEFAULT NULL COMMENT '加权得分',
  `deviation_level` varchar(20) DEFAULT NULL COMMENT '偏离程度(normal/mild/moderate/severe)',
  `risk_level` varchar(20) DEFAULT NULL COMMENT '风险等级(low/medium/high/critical)',
  `score_detail` json DEFAULT NULL COMMENT '评分详细信息',
  `calculated_time` datetime DEFAULT NULL COMMENT '计算时间',
  `data_range_start` datetime DEFAULT NULL COMMENT '数据范围开始时间',
  `data_range_end` datetime DEFAULT NULL COMMENT '数据范围结束时间',
  `status` tinyint(1) DEFAULT 1 COMMENT '状态(1:有效 0:无效)',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_score` (`user_id`,`customer_id`,`score_type`,`indicator_type`),
  KEY `idx_customer_org_type` (`customer_id`,`org_id`,`score_type`),
  KEY `idx_risk_level` (`risk_level`),
  KEY `idx_calculated_time` (`calculated_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康数据评分表';

-- 4. 画像生成任务日志表
CREATE TABLE `t_health_profile_task_log` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `task_id` varchar(64) NOT NULL COMMENT '任务ID',
  `task_type` varchar(20) NOT NULL COMMENT '任务类型(scheduled/manual)',
  `customer_id` bigint(20) NOT NULL COMMENT '客户ID',
  `target_type` varchar(20) DEFAULT NULL COMMENT '目标类型(user/org/all)',
  `target_ids` json DEFAULT NULL COMMENT '目标ID列表',
  `total_users` int(11) DEFAULT 0 COMMENT '总用户数',
  `success_count` int(11) DEFAULT 0 COMMENT '成功数量',
  `failed_count` int(11) DEFAULT 0 COMMENT '失败数量',
  `failed_users` json DEFAULT NULL COMMENT '失败用户详情',
  `start_time` datetime DEFAULT NULL COMMENT '开始时间',
  `end_time` datetime DEFAULT NULL COMMENT '结束时间',
  `duration_ms` bigint(20) DEFAULT NULL COMMENT '执行耗时(毫秒)',
  `status` varchar(20) DEFAULT 'running' COMMENT '任务状态(running/success/failed)',
  `error_message` text COMMENT '错误信息',
  `operator_id` bigint(20) DEFAULT NULL COMMENT '操作人ID(手动任务)',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_task_id` (`task_id`),
  KEY `idx_customer_type` (`customer_id`,`task_type`),
  KEY `idx_status` (`status`),
  KEY `idx_start_time` (`start_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康画像任务日志表';

-- 插入测试数据示例
INSERT INTO `t_health_profile` (`user_id`, `customer_id`, `org_id`, `health_score`, `health_level`, `baseline_deviation_count`, `profile_data`, `generated_time`, `data_range_start`, `data_range_end`) VALUES
(1, 1, 1, 85.50, '良好', 1, '{"heartrate": {"score": 90, "status": "normal"}, "temperature": {"score": 80, "status": "mild_deviation"}}', NOW(), DATE_SUB(NOW(), INTERVAL 30 DAY), NOW()),
(2, 1, 1, 92.30, '优秀', 0, '{"heartrate": {"score": 95, "status": "normal"}, "temperature": {"score": 88, "status": "normal"}}', NOW(), DATE_SUB(NOW(), INTERVAL 30 DAY), NOW()); 
