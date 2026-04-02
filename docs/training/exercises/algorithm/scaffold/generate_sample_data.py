"""生成示例预测数据（运行一次即可）"""
import csv
import random

random.seed(42)
labels = ["cat", "dog", "bird"]

with open("data/sample_predictions.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["sample_id", "true_label", "predicted_label", "confidence"])
    for i in range(1, 101):
        true_label = random.choice(labels)
        # 80% 概率预测正确
        if random.random() < 0.8:
            pred_label = true_label
            confidence = round(random.uniform(0.7, 0.99), 2)
        else:
            pred_label = random.choice([l for l in labels if l != true_label])
            confidence = round(random.uniform(0.3, 0.65), 2)
        writer.writerow([i, true_label, pred_label, confidence])

print("示例数据已生成: data/sample_predictions.csv")
