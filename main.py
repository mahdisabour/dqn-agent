import multiprocessing
import logging
import sys 
import signal 

import gymnasium as gym

from src.agent import DQNAgent
from src.utils.plot_result import plot_durations
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


def terminate_processes(processes):
    for process in processes:
        process.terminate()


def main(ue_id: str):
    env = NsOranEnv(ue_id=ue_id)
    agent = DQNAgent(env=env)
    agent.learn()
    plot_durations(
        episode_durations=agent.episode_durations,
        complete=False,
    )


if __name__ == "__main__":
    processes = []
    def signal_handler(sig, frame):
        logger.info("\nCtrl+C received! Terminating processes...")
        terminate_processes(processes)
        logger.info("All processes terminated.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        for i in range(1, 13):
            process = multiprocessing.Process(target=main, args=(i,))
            processes.append(process)
            process.start()
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

    logger.info("Finished")
