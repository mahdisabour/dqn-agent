import random
import time


def generate_mock_data():
    ue_id = random.choice(range(2)) + 1
    timestamp = int(time.time())
    def _create_data_helper(_range: int = 20):
        entry = f"{timestamp}," + ",".join([str(random.randint(1, 10)) for _ in range(_range)])
        return entry.encode()

    return {
        f"du-cell-2,{timestamp},{ue_id}": _create_data_helper(),
        f"cu-up-cell-2,{timestamp},{ue_id}": _create_data_helper(),
        f"cu-cp-cell-2,{timestamp},{ue_id}": _create_data_helper(),
    }

