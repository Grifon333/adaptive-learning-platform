import torch.nn as nn


class DKT(nn.Module):
    def __init__(self, input_dim, hidden_dim, layer_dim, output_dim):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.layer_dim = layer_dim
        self.output_dim = output_dim

        # Embeddings: the input is a combination (ConceptID + Correctness)
        # If there are 100 concepts, there are 200 input values (0-99 - errors, 100-199 - success)
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


# Factory function for model initialization
def get_model(config):
    model = DKT(config.INPUT_DIM, config.HIDDEN_DIM, config.LAYER_DIM, config.OUTPUT_DIM)
    model.eval()  # Set inference mode (no training)
    return model
