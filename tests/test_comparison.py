from dotenv import load_dotenv

load_dotenv()
from engine.comparison import compare_periods
from engine.config_loader import load_config


config = load_config("config/telecom.yaml")

result = compare_periods(
    aggregation="COUNT",
    column="*",
    view=config["database"]["view"],
)

print(result)