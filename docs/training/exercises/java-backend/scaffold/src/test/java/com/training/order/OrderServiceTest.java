package com.training.order;

import com.training.order.model.Order;
import com.training.order.model.OrderStatus;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 订单服务测试
 *
 * 第一个示例测试已写好（体验 RED 状态）。
 * TODO: 按以下场景补充更多测试，然后实现 OrderService 让测试通过（GREEN）。
 *
 * 建议测试场景：
 * 1. 创建订单 → 状态为 CREATED ✅（已有示例）
 * 2. CREATED → PAID（合法转换）
 * 3. CREATED → SHIPPED（非法转换，抛异常）
 * 4. PAID → CANCELLED（合法取消）
 * 5. SHIPPED → CANCELLED（非法取消，抛异常）
 * 6. 订单不存在（抛异常）
 * 7. 重复支付（409 场景）
 *
 * 先写测试，再实现代码！
 */
@DisplayName("订单服务测试")
class OrderServiceTest {

    // TODO: 注入或创建 OrderService 实例
    // private OrderService orderService;

    @Test
    @DisplayName("创建订单 → 状态应为 CREATED")
    void createOrder_shouldHaveCreatedStatus() {
        // 这是示例测试，当前会失败（RED）
        // 实现 OrderService.createOrder() 后应通过（GREEN）

        // TODO: 取消注释并实现 OrderService
        // Order order = orderService.createOrder("张三", 99.9);
        // assertNotNull(order.getId());
        // assertEquals(OrderStatus.CREATED, order.getStatus());
        // assertEquals("张三", order.getCustomerName());

        fail("TODO: 取消上方注释，实现 OrderService 后运行");
    }

    // TODO: 在这里补充更多测试场景
}
