package ljwx.performance

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

/**
 * ljwx-boot系统Gatling性能测试
 * 验证组织架构闭包表优化效果和系统并发能力
 */
class LjwxBootPerformanceSimulation extends Simulation {

  // HTTP配置
  val httpProtocol = http
    .baseUrl("http://192.168.1.83:3333")
    .acceptHeader("application/json")
    .contentTypeHeader("application/json")
    .userAgentHeader("Gatling Performance Test")

  // 登录场景
  val loginScenario = scenario("用户登录性能测试")
    .exec(
      http("Admin登录")
        .post("/proxy-default/auth/user_name")
        .body(StringBody("""{"userName":"admin","password":"80a3d119ee1501354755dfc3c4638d74c67c801689efbed4f25f06cb4b1cd776"}"""))
        .check(status.is(200))
        .check(jsonPath("$.success").is("true"))
        .check(jsonPath("$.data.token").saveAs("authToken"))
    )
    .pause(1)

  // 组织查询场景（验证闭包表优化效果）
  val orgQueryScenario = scenario("组织架构查询性能测试")
    .exec(loginScenario)
    .pause(1)
    .repeat(50) {
      exec(
        http("查询组织列表")
          .get("/sys_org_units/page")
          .queryParam("page", "1")
          .queryParam("pageSize", "20")
          .queryParam("customerId", "0")
          .header("satoken", "${authToken}")
          .header("Authorization", "Bearer ${authToken}")
          .check(status.is(200))
          .check(responseTimeInMillis.lt(100)) // 验证<100ms响应时间
      )
      .pause(100.milliseconds)
    }

  // 用户查询场景（验证userId优化效果）  
  val userQueryScenario = scenario("用户查询性能测试")
    .exec(loginScenario)
    .pause(1)
    .repeat(30) {
      exec(
        http("查询用户列表")
          .get("/sys_user/page")
          .queryParam("page", "1")
          .queryParam("pageSize", "20")
          .queryParam("customerId", "0")
          .header("satoken", "${authToken}")
          .header("Authorization", "Bearer ${authToken}")
          .check(status.is(200))
          .check(responseTimeInMillis.lt(200)) // 验证<200ms响应时间
      )
      .pause(200.milliseconds)
    }

  // 告警处理场景
  val alertProcessingScenario = scenario("告警处理性能测试")
    .exec(loginScenario)
    .pause(1)
    .repeat(20) {
      exec(
        http("查询告警列表")
          .get("/t_alert_info/page")
          .queryParam("page", "1")
          .queryParam("pageSize", "10")
          .queryParam("customerId", "0")
          .header("satoken", "${authToken}")
          .header("Authorization", "Bearer ${authToken}")
          .check(status.is(200))
          .check(responseTimeInMillis.lt(500))
      )
      .pause(500.milliseconds)
    }

  // 综合业务场景
  val mixedWorkloadScenario = scenario("综合业务负载测试")
    .exec(loginScenario)
    .pause(1)
    .during(300.seconds) {
      randomSwitch(
        40.0 -> exec(
          http("首页数据查询")
            .get("/sys_user/page")
            .queryParam("page", "1")
            .queryParam("pageSize", "10")
            .queryParam("customerId", "0")
            .header("satoken", "${authToken}")
            .header("Authorization", "Bearer ${authToken}")
            .check(status.is(200))
        ),
        30.0 -> exec(
          http("组织管理查询")
            .get("/sys_org_units/page")
            .queryParam("page", "1")
            .queryParam("pageSize", "15")
            .queryParam("customerId", "0")
            .header("satoken", "${authToken}")
            .header("Authorization", "Bearer ${authToken}")
            .check(status.is(200))
        ),
        20.0 -> exec(
          http("设备状态查询")
            .get("/t_device_info/page")
            .queryParam("page", "1")
            .queryParam("pageSize", "20")
            .queryParam("customerId", "0")
            .header("satoken", "${authToken}")
            .header("Authorization", "Bearer ${authToken}")
            .check(status.is(200))
        ),
        10.0 -> exec(
          http("告警监控查询")
            .get("/t_alert_info/page")
            .queryParam("page", "1")
            .queryParam("pageSize", "5")
            .queryParam("customerId", "0")
            .header("satoken", "${authToken}")
            .header("Authorization", "Bearer ${authToken}")
            .check(status.is(200))
        )
      ).pause(1.seconds, 3.seconds)
    }

  // 执行配置
  setUp(
    // 基础负载测试
    loginScenario.inject(
      constantUsersPerSec(5) during(60.seconds)
    ),
    
    // 组织查询性能验证（验证闭包表优化）
    orgQueryScenario.inject(
      rampUsers(10) during(30.seconds)
    ),
    
    // 用户查询性能验证（验证userId优化）
    userQueryScenario.inject(
      rampUsers(15) during(45.seconds)
    ),
    
    // 告警处理压力测试
    alertProcessingScenario.inject(
      rampUsers(20) during(60.seconds)
    ),
    
    // 综合业务负载测试
    mixedWorkloadScenario.inject(
      rampUsers(50) during(120.seconds),
      constantUsersPerSec(30) during(300.seconds)
    )
  ).protocols(httpProtocol)
   .assertions(
     global.responseTime.max.lt(3000),
     global.responseTime.mean.lt(500),
     global.successfulRequests.percent.gt(95),
     forAll.responseTime.percentile3.lt(2000)
   )
}