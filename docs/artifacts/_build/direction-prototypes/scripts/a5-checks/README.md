# A5 prototype checks (copied 2026-10-21)

Scratch check scripts the A5 implementer ran (click-through, 390/430/500 px overflow, pending-line timings, AA contrast
in both themes, no red outside the safety card, wireframe shots). They were written in the job temp folder
`/Users/innocentnortey/.claude/jobs/0d72ed71/tmp` and still name it for their temp Chrome profile and output paths;
change those paths before rerunning. Cap every headless run (`perl -e 'alarm 60; exec @ARGV' …`) and never touch a
running browser. Results are in the plan's appended *Deviations* and the dev log.
