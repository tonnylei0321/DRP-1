package com.training.order.controller;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 订单控制器
 *
 * TODO: 实现以下 REST 端点：
 * - POST   /api/orders              → 创建订单
 * - PUT    /api/orders/{id}/pay     → 支付
 * - PUT    /api/orders/{id}/ship    → 发货
 * - PUT    /api/orders/{id}/deliver → 确认收货
 * - PUT    /api/orders/{id}/cancel  → 取消
 *
 * 注意：
 * - 使用合适的 HTTP 状态码（200, 400, 404, 409）
 * - 返回统一的响应格式
 */
@RestController
@RequestMapping("/api/orders")
public class OrderController {

    // TODO: 注入 OrderService

    // TODO: 实现端点
}
