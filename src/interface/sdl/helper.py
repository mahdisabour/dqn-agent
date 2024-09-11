import random
import time
from src.utils.config import get_config

def generate_mock_data():
    ue_num = get_config().ENV.NUM_UE
    timestamp = int(time.time())
    def _create_data_helper(_range: int, _ue_id: str):
        entry = f"{timestamp}," + f"{_ue_id}," + ",".join([str(random.choice([2, 3, 4, 5])) for _ in range(_range)])
        return entry.encode()
    result = {}
    for ue_id in range(1, ue_num+1):
        result.update({
            f"du-cell-2,{timestamp},{ue_id}": _create_data_helper(54, ue_id),
            f"cu-up-cell-2,{timestamp},{ue_id}": _create_data_helper(9, ue_id),
            f"cu-cp-cell-2,{timestamp},{ue_id}": _create_data_helper(31, ue_id),
        })
    return result

