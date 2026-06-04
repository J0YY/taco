# 12 Readiness Tier From Model Internals

## Voiceover

Now TACO turns evidence into a certificate.

The certificate is not saying "the robot is safe in general." It says a specific
failure mode was identified, the internal signal appears early, and a required
runtime control can respond to it.

That is how the model internals change the readiness tier: they identify the
failure family and define the condition under which deployment can be certified.

## Visual Beats

- Evidence cards flow into a certificate panel.
- The panel names the readiness tier, failure mode, and required condition.
- The limitation card stays visible to avoid overclaiming.
