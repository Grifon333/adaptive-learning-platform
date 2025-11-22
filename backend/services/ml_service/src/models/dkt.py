import torch
import torch.nn as nn

class DKT(nn.Module):
    def __init__(self, input_dim, hidden_dim, layer_dim, output_dim):
        super(DKT, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.layer_dim = layer_dim
        self.output_dim = output_dim

        # Embeddings: вхід це комбінація (ConceptID + Correctness)
        # Якщо концепцій 100, то вхідних значень 200 (0-99 - помилки, 100-199 - успіх)
        self.embedding = nn.Embedding(input_dim * 2, hidden_dim)

        self.lstm = nn.LSTM(hidden_dim, hidden_dim, layer_dim, batch_first=True)

        self.fc = nn.Linear(hidden_dim, output_dim)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # x shape: (batch_size, sequence_length)
        embed = self.embedding(x)

        # LSTM output shape: (batch_size, seq_len, hidden_dim)
        out, _ = self.lstm(embed)

        # Prediction shape: (batch_size, seq_len, output_dim)
        res = self.sigmoid(self.fc(out))
        return res

# Функція-фабрика для ініціалізації моделі
def get_model(config):
    model = DKT(config.INPUT_DIM, config.HIDDEN_DIM, config.LAYER_DIM, config.OUTPUT_DIM)
    model.eval() # Встановлюємо режим inference (без навчання)
    return model
