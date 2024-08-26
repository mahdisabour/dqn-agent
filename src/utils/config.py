import json
from dataclasses import dataclass

@dataclass
class EnvironmentConfig:
    NUM_BS: int
    NUM_UE: int
    INTERVAL: int

@dataclass
class SDLConfig:
    NAMESPACE: str

@dataclass
class RCConfig:
    RC_XAPP_IP: str
    RC_XAPP_PORT: str

@dataclass
class DTConfig:
    ENABLE: str
    NUM_DT: int

@dataclass
class Config:
    environment: EnvironmentConfig
    sdl: SDLConfig
    RC: RCConfig
    DT: DTConfig


def get_config(path: str) -> Config:
    with open(path, "r") as file:
        config_dict = json.load(file)
    return Config(
        environment=EnvironmentConfig(**config_dict['ENV']),
        sdl=SDLConfig(**config_dict['SDL']),
        RC=RCConfig(**config_dict['RC']),
        DT=DTConfig(**config_dict['DT'])
    )