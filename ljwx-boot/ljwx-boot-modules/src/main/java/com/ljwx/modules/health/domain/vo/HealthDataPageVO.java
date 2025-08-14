package com.ljwx.modules.health.domain.vo;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.metadata.OrderItem;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.ljwx.modules.customer.domain.entity.THealthDataConfig;
import lombok.Data;

import java.util.List;

@Data // #lombok注解
public class HealthDataPageVO<T> { // #分页VO，带columns
    private List<T> records; // #数据
    private long total, size, current; // #分页
    private List<?> columns; // #动态列
 
    public HealthDataPageVO(List<T> records, long total, long size, long current, List<?> columns) { // #极简构造
        this.records = records;
        this.total = total;
        this.size = size;
        this.current = current;
        this.columns = columns;

    }
}