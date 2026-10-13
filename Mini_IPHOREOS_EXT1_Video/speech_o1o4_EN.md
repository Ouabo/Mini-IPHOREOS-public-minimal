# Speech script: O1_O4_Overview_EN.mp4

Full narration, timed to the five chapters in `tools/make_o1_o4_video.py` (title,
then one chapter per objective, then the closing card). The video itself is silent
and captioned; this script is for a narrator to read aloud alongside it, or to use
as the basis for a future voiceover track. Timings are approximate guides, not
word-exact marks; a narrator should pace against what is on screen, not the clock.

No double hyphens or em dashes are used anywhere below, to match the on-screen
captions' own style.

---

**[0:00, title card]**

This video asks a simple question. What can a small desktop robot simulation
already tell us about four much bigger goals from our research plan?

Those goals are labelled O1 through O4. They describe a future robot working in a
real warehouse, picking items off shelves and sorting parts, on real hardware. The
robot you are about to see is much smaller than that. It is a simulation of a robot
approaching a cardboard wall on a desktop. It is an early step toward those four
goals, not a claim that we have already reached them. Each of the next four
chapters takes one goal, shows what evidence we actually have for it today, and is
honest about what that evidence does not yet prove.

**[0:10, O1: Learn grounded concepts and events]**

The first goal asks whether a system can learn ideas from its own experience that
still hold up later, on data it was never trained on. Our robot does not just guess
a single number for how far it is from the wall. It reports a range it is confident
in, and that range gets tighter as it gathers more evidence.

We tested this honestly. Every result shown throughout this project was first
worked out on one set of random trials, then re-run, completely unchanged, on a
different set the robot had never seen before. The numbers held up almost exactly,
three point three decisions on the original trials, three point two on the new
ones. That kind of replication is exactly what this goal asks for.

What this does not prove is the harder claim the real goal is after, that the
robot understands objects and relationships well enough to generalise far beyond
this one small task. That is still ahead of us.

**[0:55, O2: Infer context and allocate computation]**

The second goal asks whether a system can figure out which situation it is in, and
spend its effort accordingly, without permanently throwing away the possibility
that it is wrong.

Watch the meter on the right. The robot is holding two guesses at once, is the
floor behaving normally, or is it the slower regime, and shifting its confidence
between them as readings come in. Importantly, the guess that is currently losing
is never deleted. It can still recover if the evidence changes. A separate
mechanism decides when there is enough accumulated evidence to act on a change,
rather than reacting to every single noisy reading. And the planner itself weighs
the cost of each action against how much it expects to learn.

What this does not prove is anything about real hardware, latency, memory, or
power use. Here we are only counting decisions and a simulated cost per action.

**[1:40, O3: Recompose knowledge for adaptive planning]**

The third goal asks the hardest question, can knowledge learned on one task
actually transfer to a different task, not just a repeat of the same one?

We built a second task with a different target distance, and gave each simulated
robot a hidden, persistent bias in its own speed, something calibration could never
see in advance. One robot, on the left, starts cold, with no prior experience. The
other, on the right, carries over what it learned on the first task.

On this run, the cold robot needed five decisions to recognise the change in
speed after the switch. The one that carried knowledge over needed four. Averaged
across a hundred different simulated robots, that gap holds up, five point two
decisions against three point eight, and it is not a fluke, the carried-over
robot was faster in sixty one cases out of a hundred, slower in only seven. Overall
task completion time barely changed, and we show that honestly too, because the
benefit is specifically in how fast the robot recognises what changed, not in
finishing the whole task sooner.

**[2:30, O4: Establish bounded trustworthiness]**

The fourth goal asks whether a system's confidence can be trusted, whether it
respects hard safety limits on its own, and whether its decisions can be checked
afterward.

Here the robot receives a reading that is badly wrong, the kind of glitch a real
sensor occasionally produces. Watch the right-hand panel flash. The robot catches
it immediately and refuses to trust it, because the reading is far outside what its
own uncertainty says is plausible. Separately, the planner will not even consider
an action that risks overshooting the target, no matter how good that action might
otherwise look. And everything the robot decides, and why, is written to a log that
can be checked after the fact.

Here is the one place we have to be completely direct. None of this has been
tested on real hardware. No physical robot has been built. This evidence covers
the software mechanisms for trustworthiness, not the real-world claim.

**[3:15, closing card]**

So, in plain terms, four small results for four big goals. Calibrated, confirmed
predictions, for goal one. Efficient, recoverable decision making, for goal two. A
real, measured case of learning transferring to a new goal, for goal three. And
calibrated confidence with enforced safety limits and a full decision record, for
goal four. None of this is the full warehouse robot our research plan describes.
Two real tasks, real hardware, and physical testing are still ahead of us. But for
a small desktop simulation, this is genuine, honestly reported evidence that the
approach is pointed in the right direction.
