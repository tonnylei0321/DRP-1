package com.training.order.repository;

import com.training.order.model.Order;

import org.springframework.stereotype.Repository;

import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 订单数据仓库（内存实现）
 *
 * 使用 ConcurrentHashMap 存储，无需数据库。
 * 此类已完成，无需修改。
 */
@Repository
public class OrderRepository {

    private final Map<Long, Order> store = new ConcurrentHashMap<>();
    private final AtomicLong idGenerator = new AtomicLong(1);

    /**
     * 保存订单（新增或更新）
     */
    public Order save(Order order) {
        if (order.getId() == null) {
            order.setId(idGenerator.getAndIncrement());
        }
        store.put(order.getId(), order);
        return order;
    }

    /**
     * 根据 ID 查找订单
     */
    public Optional<Order> findById(Long id) {
        return Optional.ofNullable(store.get(id));
    }

    /**
     * 删除所有订单（测试用）
     */
    public void deleteAll() {
        store.clear();
        idGenerator.set(1);
    }
}
