import time
import logging
from abc import abstractmethod, ABC

from ricsdl.syncstorage import SyncStorage
from ricsdl.exceptions import RejectedByBackend, NotConnected, BackendError 

from src.utils.config import get_config
from src.utils.decorator import retry

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
    def find_keys(self, prefix: str) -> list[str]:
        ...

    @abstractmethod
    def find_get_keys(self, prefix: str) -> dict[str, bytes]:
        ...
    
    @abstractmethod
    def remove(self, key: str | set[str]):
        ...

    @abstractmethod
    def remove_all(self):
        ...
        

class MockSDLManager(SDLManagerABC):
    def __init__(self, namespace: str = "ns-o-ran"):
        self.namespace = namespace

    def find_keys(self, prefix: str) -> list[str]:
        ...

    def find_get_keys(self, prefix: str) -> dict[str, bytes]:
        ...
    
    def remove(self, key: str | set[str]):
        ...

    def get_next_obs(self) -> tuple[list[str]]:
        ...


class RealSDLManager(SDLManagerABC):
    def __init__(self, namespace: str = "ns-o-ran"):
        self.namespace = namespace
        self.SDL = _try_func_return(SyncStorage)
        self.last_ts = 0

    def find_get_keys(self, prefix: str) -> dict[str, bytes]:
        ret_key_values = self._try_func_return(lambda: self.SDL.find_and_get(self.namespace, prefix))
        return ret_key_values

    def remove_all(self):
        self._try_func_return(lambda: self.SDL.remove_all(self.namespace))

    @retry(max_retries=30, wait_time=1)
    def get_next_obs(self, ue_id: str):
        du_dict = self.find_get_keys("du-cell-*")
        cuup_dict = self.find_get_keys("cu-up-cell-*")
        cucp_dict = self.find_get_keys("cu-cp-cell-*")
        
        # Filter function to get specific ue and new data 
        def _filter_keys(key: str):
            return True if int(key.split(',')[1]) > self.last_ts and key.split(",")[-1] == ue_id  else False
        
        f_du_keys = list(filter(_filter_keys, du_dict.keys()))
        f_cuup_keys = list(filter(_filter_keys, cuup_dict.keys()))
        f_cucp_keys = list(filter(_filter_keys, cucp_dict.keys()))

        if not (f_du_keys or f_cucp_keys or f_cuup_keys):
            logger.info("Environment not ready")
            raise Exception("Environment not ready")

        last_du_key = max(f_du_keys, key=lambda key: int(key.split(",")[1]))
        last_cuup_key = max(f_cuup_keys, key=lambda key: int(key.split(",")[1]))
        last_cucp_key = max(f_cucp_keys, key=lambda key: int(key.split(",")[1]))

        self.last_ts = int(last_du_key.split(",")[1])

        # remove unused keys
        self.remove_all()

        return du_dict[last_du_key], cuup_dict[last_cuup_key], cucp_dict[last_cucp_key]
        

def get_sdl_manager() -> RealSDLManager | MockSDLManager:
    """
        Handle SDL running mode
    """
    config = get_config()
    if config.SDL.MODE == "TEST": 
        return MockSDLManager()
    return RealSDLManager()
