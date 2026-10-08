import time
from dotenv import load_dotenv

load_dotenv()

from engine.config_loader import load_config
from engine.metrics import calculate_metric
from engine.interpreter_retail import interpret_retail_metric


config = load_config("config/retail.yaml")

questions = [
    ("Total sales", "sales"),
    ("Total profit", "profit"),
    ("Order count", "orders"),
    ("Units sold", "quantity"),
    ("Average shipping time", "avg_shipping_days"),
    ("Shipping cost", "shipping_cost"),
    ("Profit margin", "profit_margin"),
    ("Average order value", "average_order_value"),
]

print("InsightForge execution benchmark")
print("=" * 55)

total_ms = 0.0

for label, metric in questions:
    start = time.perf_counter()

    value = calculate_metric(metric, config)
    interpret_retail_metric(metric, value, config)

    elapsed_ms = (time.perf_counter() - start) * 1000
    total_ms += elapsed_ms

    print(f"{label:28} {elapsed_ms:10.2f} ms")

print("-" * 55)
print(f"{'TOTAL':28} {total_ms:10.2f} ms")
print(f"{'AVERAGE':28} {total_ms / len(questions):10.2f} ms")