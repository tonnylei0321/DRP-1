package com.training.order.model;

/**
 * 订单状态枚举
 *
 * 基础状态值已定义，转换规则待实现。
 *
 * TODO（中途变更时）：新增 REFUNDING、REFUNDED 状态及对应转换规则
 */
public enum OrderStatus {

    CREATED,
    PAID,
    SHIPPED,
    DELIVERED,
    CANCELLED;

    /**
     * 判断是否可以转换到目标状态
     *
     * TODO: 实现状态转换规则
     *
     * 合法转换：
     * - CREATED → PAID, CANCELLED
     * - PAID → SHIPPED, CANCELLED
     * - SHIPPED → DELIVERED
     * - DELIVERED → （无合法转换）
     * - CANCELLED → （无合法转换）
     *
     * 提示：可以用 switch 表达式或 Map<OrderStatus, Set<OrderStatus>>
     */
    public boolean canTransitionTo(OrderStatus target) {
        // TODO: 实现转换规则，当前默认返回 false
        return false;
    }
}
