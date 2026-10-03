Title: torch.nn.Dropout
URL: https://docs.pytorch.org/docs/stable/generated/torch.nn.Dropout
Topic: dropout regularization
Source-Type: official documentation (PyTorch)
Text:
During training, dropout randomly sets some input elements to zero with the configured probability. During evaluation, the dropout module acts as an identity operation. Therefore a saved dropout setting affects training behavior, while evaluation uses the model in its evaluation mode; comparing runs still requires checking all other recorded settings.
