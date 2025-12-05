import os
import random
from collections import deque

# import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F  # noqa: N812
from loguru import logger


class DQN(nn.Module):
    """
    Deep Q-Network for approximating Q(s, a).
    Input: State Vector S_t (Knowledge + Behavior + Profile)
    Output: Q-values for each Concept (Action)
    """

    def __init__(self, input_dim: int, output_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, output_dim)
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        return self.fc3(x)  # Raw Q-values


class RLAgent:
    """
    Manages the DQN policy, exploration (epsilon-greedy), and experience replay.
    """

    def __init__(self, input_dim: int, output_dim: int, device="cpu", model_path="/data/rl_model.pth"):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.device = device
        self.model_path = model_path

        # Policy Network
        self.policy_net = DQN(input_dim, output_dim).to(device)
        self.target_net = DQN(input_dim, output_dim).to(device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = torch.optim.Adam(self.policy_net.parameters(), lr=1e-3)
        self.memory = deque(maxlen=10000)

        # Hyperparameters
        self.batch_size = 64
        self.gamma = 0.99
        self.epsilon = 0.1  # Exploration rate (can be decayed)

        # Load weights if exist
        self.load_checkpoint()

    def select_action(self, state_vector: list[float], valid_actions: list[int] = None) -> int:
        """
        Selects an action using Epsilon-Greedy policy.
        valid_actions: Optional mask to ensure we only recommend available concepts.
        """
        if random.random() < self.epsilon:
            if valid_actions:
                return random.choice(valid_actions)
            return random.randint(0, self.output_dim - 1)

        with torch.no_grad():
            state_tensor = torch.FloatTensor(state_vector).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_tensor)

            # Mask invalid actions (set Q to -inf)
            if valid_actions:
                mask = torch.full_like(q_values, float("-inf"))
                mask[0, valid_actions] = 0
                q_values = q_values + mask

            return q_values.argmax().item()

    def store_transition(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_step(self):
        """
        Standard DQN training step: Sample batch -> Calc Loss -> Backprop
        """
        if len(self.memory) < self.batch_size:
            return

        batch = random.sample(self.memory, self.batch_size)
        batch_state, batch_action, batch_reward, batch_next_state, batch_done = zip(*batch, strict=False)

        state = torch.FloatTensor(batch_state).to(self.device)
        action = torch.LongTensor(batch_action).unsqueeze(1).to(self.device)
        reward = torch.FloatTensor(batch_reward).unsqueeze(1).to(self.device)
        next_state = torch.FloatTensor(batch_next_state).to(self.device)
        done = torch.FloatTensor(batch_done).unsqueeze(1).to(self.device)

        # Q(s, a)
        curr_q = self.policy_net(state).gather(1, action)

        # max Q(s', a')
        next_q = self.target_net(next_state).max(1)[0].unsqueeze(1)
        expected_q = reward + (self.gamma * next_q * (1 - done))

        loss = F.mse_loss(curr_q, expected_q.detach())

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def save_checkpoint(self):
        """Saves model weights to disk."""
        try:
            torch.save(self.policy_net.state_dict(), self.model_path)
        except Exception as e:
            logger.error(f"Failed to save RL model: {e}")

    def load_checkpoint(self):
        """Loads model weights from disk."""
        if os.path.exists(self.model_path):
            try:
                self.policy_net.load_state_dict(torch.load(self.model_path, map_location=self.device))
                self.target_net.load_state_dict(self.policy_net.state_dict())
                logger.info(f"RL Model loaded from {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to load RL model: {e}")
        else:
            logger.info("No existing RL model found. Starting fresh.")
