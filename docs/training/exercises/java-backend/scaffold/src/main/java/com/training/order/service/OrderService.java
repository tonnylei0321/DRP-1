package com.training.order.service;

import org.springframework.stereotype.Service;

/**
 * 订单服务层
 *
 * TODO: 实现以下方法：
 * - createOrder(customerName, amount) → 创建订单
 * - payOrder(orderId) → 支付订单（CREATED → PAID）
 * - shipOrder(orderId) → 发货（PAID → SHIPPED）
 * - deliverOrder(orderId) → 确认收货（SHIPPED → DELIVERED）
 * - cancelOrder(orderId) → 取消订单（仅 CREATED/PAID）
 *
 * 注意：
 * - 非法状态转换应抛出 IllegalStateException
 * - 订单不存在应抛出合适的异常
 * - 每次状态变更需记录操作日志
 */
@Service
public class OrderService {

    // TODO: 注入 OrderRepository

    // TODO: 实现业务方法
}
