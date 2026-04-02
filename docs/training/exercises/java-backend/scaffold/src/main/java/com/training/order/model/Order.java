package com.training.order.model;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 订单实体
 *
 * status 字段已使用 OrderStatus 枚举类型。
 */
public class Order {

    private Long id;
    private String customerName;
    private Double amount;
    private OrderStatus status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private List<String> operationLogs = new ArrayList<>();

    public Order() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    public Order(Long id, String customerName, Double amount) {
        this();
        this.id = id;
        this.customerName = customerName;
        this.amount = amount;
        this.status = OrderStatus.CREATED;
    }

    // --- Getter / Setter ---

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getCustomerName() { return customerName; }
    public void setCustomerName(String customerName) { this.customerName = customerName; }

    public Double getAmount() { return amount; }
    public void setAmount(Double amount) { this.amount = amount; }

    public OrderStatus getStatus() { return status; }
    public void setStatus(OrderStatus status) {
        this.status = status;
        this.updatedAt = LocalDateTime.now();
    }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }

    public List<String> getOperationLogs() { return operationLogs; }

    /**
     * 添加操作日志
     */
    public void addLog(String log) {
        this.operationLogs.add(
            LocalDateTime.now() + " - " + log
        );
    }
}
