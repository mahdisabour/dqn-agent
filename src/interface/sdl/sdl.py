import time
import random
import logging
from abc import abstractmethod, ABC

from ricsdl.syncstorage import SyncStorage
from ricsdl.exceptions import RejectedByBackend, NotConnected, BackendError 

from src.utils.config import get_config
from src.utils.decorator import retry
from src.interface.sdl.helper import generate_mock_data


logger = logging.getLogger(__name__)


def _try_func_return(func):
    """
    Generic wrapper function to call SDL API function and handle exceptions if they are raised.
    """
    try:
        return func()
    except RejectedByBackend as exp:
        logger.info(f'SDL function {func.__name__} failed: {str(exp)}')
        # Permanent failure, just forward the exception
        raise
    except (NotConnected, BackendError) as exp:
        logger.error(f'SDL function {func.__name__} failed for a temporal error: {str(exp)}')
        # Here we could have a retry logic


class SDLManagerABC(ABC):
    @abstractmethod
    def __init__(self, namespace: str = "ns-o-ran"):
        self.namespace = namespace

    @abstractmethod
    def find_get_keys(self, prefix: str) -> dict[str, bytes]:
        ...
    
    @abstractmethod
    def remove_all(self):
        ...
        

class MockSDLManager(SDLManagerABC):
    def __init__(self, namespace: str = "ns-o-ran"):
        self.namespace = namespace
        self.sdl = {}

    def find_get_keys(self, prefix: str) -> dict[str, bytes]:
        thr = 0.5
        if random.random() > thr:
            self.sdl.update(generate_mock_data())
        return {k: v for k, v in self.sdl.items() if k.startswith(prefix)}

    def remove_all(self):
        self.sdl = {}


class RealSDLManager(SDLManagerABC):
    def __init__(self, namespace: str = "ns-o-ran"):
        self.namespace = namespace
        self.SDL = _try_func_return(SyncStorage)

    def find_get_keys(self, prefix: str) -> dict[str, bytes]:
        ret_key_values = self._try_func_return(lambda: self.SDL.find_and_get(self.namespace, prefix))
        return ret_key_values

    def remove_all(self):
        self._try_func_return(lambda: self.SDL.remove_all(self.namespace))


def get_sdl_manager() -> RealSDLManager | MockSDLManager:
    """
        Handle SDL running mode
    """
    config = get_config()
    if config.SDL.MODE == "TEST": 
        return MockSDLManager()
    return RealSDLManager()


@retry(max_retries=30, wait_time=1)
def get_next_obs(
        sdl_manager: RealSDLManager | MockSDLManager, ue_id: str
    ) -> tuple[tuple, int]:
    """
        Handling get last observation in sdl
    """
    du_dict = sdl_manager.find_get_keys("du-cell-*")
    cuup_dict = sdl_manager.find_get_keys("cu-up-cell-*")
    cucp_dict = sdl_manager.find_get_keys("cu-cp-cell-*")
    
    # Filter function to get specific ue
    def _filter_keys(key: str):
        return True if key.split(",")[-1] == ue_id  else False
    
    f_du_keys = list(filter(_filter_keys, du_dict.keys()))
    f_cuup_keys = list(filter(_filter_keys, cuup_dict.keys()))
    f_cucp_keys = list(filter(_filter_keys, cucp_dict.keys()))

    if not (f_du_keys and f_cucp_keys and f_cuup_keys):
        logger.warn("Environment not ready")
        raise Exception("Environment not ready")

    last_du_key = max(f_du_keys, key=lambda key: int(key.split(",")[1]))
    last_cuup_key = max(f_cuup_keys, key=lambda key: int(key.split(",")[1]))
    last_cucp_key = max(f_cucp_keys, key=lambda key: int(key.split(",")[1]))

    # remove all keys
    sdl_manager.remove_all()

    return (
        du_dict[last_du_key], 
        cuup_dict[last_cuup_key], 
        cucp_dict[last_cucp_key]
    )
