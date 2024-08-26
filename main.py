import gymnasium as gym

from src.agent import DQNAgent
from src.utils.plot_result import plot_durations


def main():
    env = gym.make("CartPole-v1")
    agent = DQNAgent(env=env)
    agent.learn()
    plot_durations(
        episode_durations=agent.episode_durations,
        complete=False,
    )


if __name__ == "__main__":
    main()