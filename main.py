import multiprocessing
import logging
import sys 
import signal 

import gymnasium as gym

from src.agent import DQNAgent
from src.environment import NsOranEnv
from src.utils.config import get_config


logging.basicConfig(
    level=get_config().APP.LOGLEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ts-xapp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    ue_num = get_config().ENV.NUM_UE
    envs = [NsOranEnv(ue_id+1) for ue_id in range(ue_num)]
    agent = DQNAgent(envs=envs)
    agent.learn()


if __name__ == "__main__":
    main()