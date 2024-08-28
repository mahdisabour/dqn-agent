import gymnasium as gym

from src.utils.config import Config

class Environment(gym.Env):
    def __init__(self, config: Config):
        ...

    def reset(self):
        """
        Resets the environment to the initial state.
        Returns the initial observation.
        """
        pass

    def step(self, action):
        """
        Executes the given action in the environment.
        Returns:
            - next_state: The next observation after the action.
            - reward: The reward received for the action.
            - done: Boolean indicating if the episode is over.
            - info: Optional info for debugging.
        """
        pass

    def render(self):
        """
        Renders the environment (for visualization).
        """
        pass

    def action_space(self):
        """
        Returns the action space of the environment.
        """
        pass

    def observation_space(self):
        """
        Returns the observation space of the environment.
        """
        pass