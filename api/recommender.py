import json
import math
from functools import lru_cache
from pathlib import Path


MODEL_PATH = Path(__file__).resolve().parents[1] / "ml_models" / "merrec_item_pair_model.json"


@lru_cache
def load_recommender_model():
    with MODEL_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return data["parameters"]


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)

    z = math.exp(value)
    return z / (1.0 + z)


def calc_recommend_score(current_item, candidate_item) -> float:
    params = load_recommender_model()
    weights = params["weights"]

    same_c0 = 1.0 if current_item.c0_id == candidate_item.c0_id else 0.0
    same_c1 = 1.0 if current_item.c1_id == candidate_item.c1_id else 0.0
    price_diff = abs(math.log1p(current_item.price) - math.log1p(candidate_item.price))

    linear = (
        params["bias"]
        + weights["same_c0"] * same_c0
        + weights["same_c1"] * same_c1
        + weights["price_diff"] * price_diff
    )

    return sigmoid(linear)