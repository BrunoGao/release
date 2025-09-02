package com.ljwx.admin;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * LjwxBoot Application 项目启动
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.admin.LjwxBootAdminApplication
 * @CreateTime 2023/7/6 - 11:11
 */

@EnableScheduling
@MapperScan({"com.ljwx.modules.**.repository.mapper", "com.ljwx.modules.health.mapper"})
@SpringBootApplication(scanBasePackages = "com.ljwx.**")
public class LjwxBootAdminApplication {

    public static void main(String[] args) {
        SpringApplication.run(LjwxBootAdminApplication.class, args);
    }

}
