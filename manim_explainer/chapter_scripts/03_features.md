# 03 What A Feature Is

## Voiceover

A feature is not necessarily one neuron. A better first picture is a direction
in activation space.

Imagine the activation vector as a point. A feature direction asks: how much does
this point line up with a meaningful pattern? The feature activation, or feature
score, is the strength of that alignment.

So when we say "gripper closing near object" or "language target is orange", we
mean a human label for a direction that repeatedly lights up in similar model
states.

## Visual Beats

- A 2D activation-space slice appears.
- The model state `h` is a point.
- A feature direction `d` and projection define the score `z_i`.
- The definition box distinguishes feature, activation, and human label.
