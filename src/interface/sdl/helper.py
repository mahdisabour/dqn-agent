import random
import time


def generate_mock_data():
    ue_id = random.choice(range(12)) + 1
    timestamp = int(time.time())
    def _create_data_helper(_range: int):
        entry = f"{timestamp}," + f"{ue_id}," + ",".join([str(random.choice([2, 3, 4, 5])) for _ in range(_range)])
        return entry.encode()

    return {
        f"du-cell-2,{timestamp},{ue_id}": _create_data_helper(54),
        f"cu-up-cell-2,{timestamp},{ue_id}": _create_data_helper(9),
        f"cu-cp-cell-2,{timestamp},{ue_id}": _create_data_helper(31),
    }

