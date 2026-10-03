Title: Optimizing Model Parameters
URL: https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html
Topic: SGD, loss, and weight updates
Source-Type: official documentation (PyTorch)
Text:
Optimization changes model parameters to reduce error. In PyTorch's training loop, zero_grad clears accumulated gradients, backward computes gradients of loss, and optimizer.step updates parameters. The SGD optimizer receives a learning-rate setting. A saved validation-loss curve records outcomes after those updates; it does not reveal every internal step.
