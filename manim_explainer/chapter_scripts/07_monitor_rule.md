# 07 Feature Monitor Rule

## Voiceover

Once we have feature scores, a monitor is just a rule over time.

On each timestep, read the sparse feature vector `z(t)`. If a risk feature rises
above a threshold, the robot can slow down, hand off, or abort before the visible
failure happens.

For certification, the important object is not a pretty feature plot. It is a
runtime rule with a threshold, a lead time, and a known false-alert profile.

## Visual Beats

- Safe rollout stays below threshold.
- Failure rollout crosses the threshold.
- Rule box spells out the monitor logic step by step.
