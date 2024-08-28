import time
import logging
from abc import abstractmethod, ABC

from ricsdl.syncstorage import SyncStorage
from ricsdl.exceptions import RejectedByBackend, NotConnected, BackendError 

from src.utils.config import get_config


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
        

class MockSDLManager(SDLManagerABC):
    def __init__(self, namespace: str = "ns-o-ran"):
        self.namespace = namespace

    def find_keys(self, prefix: str) -> list[str]:
        ...

    def find_get_keys(self, prefix: str) -> dict[str, bytes]:
        ...
    
    def remove(self, key: str | set[str]):
        ...


class RealSDLManager(SDLManagerABC):
    def __init__(self, namespace: str = "ns-o-ran"):
        self.namespace = namespace
        self.sdl = _try_func_return(SyncStorage)

    def find_keys(self, prefix: str) -> list[str]:
        ret_keys = self._try_func_return(lambda: self.sdl.find_keys(self.namespace, prefix))
        return ret_keys

    def find_get_keys(self, prefix: str) -> dict[str, bytes]:
        ret_key_values = self._try_func_return(lambda: self.sdl.find_and_get(self.namespace, prefix))
        return ret_key_values
    
    def remove(self, key: str | set[str]) -> None:
        self._try_func_return(lambda: self.sdl.remove(self.namespace, key))


def get_sdl_manager() -> RealSDLManager | MockSDLManager:
    config = get_config()
    if config.SDL.MODE == "TEST": 
        return MockSDLManager()
    return RealSDLManager()
