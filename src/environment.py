from abc import ABC, abstractmethod

class Environment(ABC):
    @abstractmethod
    def reset(self):
        """
        Resets the environment to the initial state.
        Returns the initial observation.
        """
        pass

    @abstractmethod
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

    @abstractmethod
    def render(self):
        """
        Renders the environment (for visualization).
        """
        pass

    @abstractmethod
    def action_space(self):
        """
        Returns the action space of the environment.
        """
        pass

    @abstractmethod
    def observation_space(self):
        """
        Returns the observation space of the environment.
        """
        pass