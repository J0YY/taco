# 02 Activations, Weights, And Neurons

## Voiceover

Start with the ordinary neural-network picture. Pixels and a language instruction
flow into the model. Inside, each neuron computes a number: a weighted sum of
inputs, plus a bias, passed through a nonlinearity.

At one moment in a rollout, all of those internal numbers form an activation
vector. We call it `h`.

That vector is a snapshot of what the model is representing right now. If the
robot is about to fail, the interesting question is whether `h` already contains
a warning.

## Visual Beats

- Pixels and instruction enter a small neural network.
- A highlighted neuron and weight lines define "neuron", "weight", and
  "activation".
- The network output becomes an activation vector `h`.
