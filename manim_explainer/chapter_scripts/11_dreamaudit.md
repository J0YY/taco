# 11 DreamAudit Evidence Timing

## Voiceover

DreamAudit turns an internal hint into replayable evidence.

In the FR-004 exhibit, the SAE monitor first alerts at step 32. A later action
diagnostic fires closer to the failure. The physical failure arrives around step
80, giving the internal monitor a 48-step warning lead.

That lead time is what makes the failure mode operationally useful: the system
can intervene before the robot visibly commits to the bad behavior.

## Visual Beats

- Timeline runs from step 0 to failure.
- Internal SAE monitor crosses threshold early.
- Action diagnostic crosses later.
- Bracket labels the warning lead.
