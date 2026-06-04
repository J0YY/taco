# 06 TopK Sparsity

## Voiceover

TopK is the rule that makes the code sparse.

First the encoder produces many feature scores. Then TopK keeps only the K
largest scores and sets everything else to zero. In this simplified drawing,
K equals three. In the TACO Octo SAE summary, the typical active count is about
64 out of 4,096 slots on each step.

That sparsity is what makes the feature vector readable over time.

## Visual Beats

- Raw feature-score bars appear.
- TopK keeps the largest bars and suppresses the rest.
- The project-specific callout gives the 64-of-4096 scale.
