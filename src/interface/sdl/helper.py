import random
import time


def generate_mock_data():
    timestamp = int(time.time())
    def _create_data_helper(_range: int, _ue_id: str):
        entry = f"{timestamp}," + f"{_ue_id}," + ",".join([str(random.choice([2, 3, 4, 5])) for _ in range(_range)])
        return entry.encode()
    result = {}
    for ue_id in range(1, 13):
        result.update({
            f"du-cell-2,{timestamp},{ue_id}": _create_data_helper(54, ue_id),
            f"cu-up-cell-2,{timestamp},{ue_id}": _create_data_helper(9, ue_id),
            f"cu-cp-cell-2,{timestamp},{ue_id}": _create_data_helper(31, ue_id),
        })
    return result

