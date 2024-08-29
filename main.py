import logging

import gymnasium as gym

from src.agent import DQNAgent
from src.utils.plot_result import plot_durations
from src.environment import NsOranEnv

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ts-xapp.log'),
        logging.StreamHandler()
    ]
)

def main():
    env = NsOranEnv(ue_id=2)
    agent = DQNAgent(env=env)
    agent.learn()
    plot_durations(
        episode_durations=agent.episode_durations,
        complete=False,
    )


if __name__ == "__main__":
    main()