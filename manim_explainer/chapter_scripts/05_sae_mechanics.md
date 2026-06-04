# 05 Sparse Autoencoder Mechanics

## Voiceover

A sparse autoencoder learns a new coordinate system for activations.

The encoder takes the original activation vector `h` and converts it into feature
scores `z`. Most entries in `z` are zero or inactive. Then the decoder tries to
reconstruct the original vector from only the active feature directions.

Training balances two goals: reconstruct `h` accurately, and keep the feature
code sparse enough that individual features can be inspected.

## Visual Beats

- Dense `h` flows into the encoder.
- Sparse feature vector `z` appears with only a few active bars.
- Decoder reconstructs `h_hat`.
- Bottom equation shows `h_hat` as a sum of active feature directions.
