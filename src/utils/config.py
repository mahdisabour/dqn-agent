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
    MODE: str


@dataclass
class RCConfig:
    RC_XAPP_IP: str
    RC_XAPP_PORT: str


@dataclass
class DTConfig:
    ENABLE: str
    NUM_DT: int


@dataclass
class AgentConfig:
    PLOT: bool


@dataclass
class APPConfig:
    LOGLEVEL: str


@dataclass
class Config:
    ENV: EnvironmentConfig
    SDL: SDLConfig
    RC: RCConfig
    DT: DTConfig
    AGENT: AgentConfig
    APP: APPConfig


def get_config(path: str = "./config.json") -> Config:
    with open(path, "r") as file:
        config_dict = json.load(file)
    return Config(
        ENV=EnvironmentConfig(**config_dict['ENV']),
        SDL=SDLConfig(**config_dict['SDL']),
        RC=RCConfig(**config_dict['RC']),
        DT=DTConfig(**config_dict['DT']),
        AGENT=AgentConfig(**config_dict['AGENT']),
        APP=APPConfig(**config_dict['APP'])
    )