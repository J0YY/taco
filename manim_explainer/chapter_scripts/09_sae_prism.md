# 09 SAE As A Prism

## Voiceover

Here is the sparse autoencoder as a prism.

The original residual stream has 256 mixed dimensions. The SAE expands that into
4,096 feature slots. On any step, only a small number are active.

Some active slots can be inspected as grasp primitives, task progress, language
target features, or episode-specific traces. The point is not that every label
is perfect. The point is that the model state becomes easier to audit.

## Visual Beats

- Dense residual stream enters the TopK SAE.
- Sparse feature bars fan out.
- Feature labels appear beside active bars.
- Bottom cards show reconstruction quality and feature counts.
