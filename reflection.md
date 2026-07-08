# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial design has four classes which are the following and their responsibilities:
Scheduler: 
    Attributes: Holds a reference to the owner. 
    Methods: Collects tasks from all pets, sorts and filters them by priority and available time, checks the owner's preferences and time constraints, and generates a daily plan with a brief explanation of why each task was included or skipped.
Owner: 
    Attributes: Holds the owner's name, a list of their pets, and their scheduling preferences. 
    Methods: Adding or removing pets and retrieving a list of the pets. 
Pet: 
    Attributes: Holds the name of the individual pet and a list of tasks.
    Methods: Adding tasks and retrieving the list of tasks.
Task: 
    Attributes: Holds a description of the activity, a time, a duration, and a priority level. 
    Methods: Change to completed or incompleted. 

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

No changes

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

My scheduler considers three constraints: available time (a daily minute budget from Owner.preferences), task priority (high/medium/low), and task duration. generate_plan() sorts incomplete tasks by priority first, then by time, and greedily includes tasks until the time budget runs out. I prioritized time and priority as the two "hard" constraints because my README explicitly asks for a plan that fits available time and explains its reasoning — duration is really just the mechanism that makes the time constraint concrete.


**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

Scheduler.detect_conflicts() only checks for exact time matches — two tasks at 08:00 are flagged, but a task from 08:00–08:30 and another from 08:15–08:45 would not be, even though they actually overlap. I chose exact-match detection because it's simple, predictable, and covers the most common real-world case (someone accidentally double-booking the same time slot), while true overlap detection would require comparing time ranges and handling more edge cases (e.g. tasks that span midnight). For a scheduling app used by one household, I think this tradeoff is reasonable — it catches the obvious mistakes without adding a lot of complexity for a marginal gain in accuracy.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used my AI coding assistant throughout the project: to brainstorm the initial class list and generate a Mermaid.js UML diagram, to scaffold the pawpal_system.py skeleton with dataclasses, to flesh out the full method implementations, and to write the main.py demo and tests/test_pawpal.py suite. The most effective use was asking it to review my skeleton against my actual README before I wrote any logic — that review caught a real gap (Task needed duration/priority/pet_name that I hadn't included) before it became a bigger refactor.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

One moment I didn't just accept AI output as-is: when asked to simplify detect_conflicts() for readability, the AI suggested a more "Pythonic" version using defaultdict and a list comprehension. I decided to keep my original explicit-loop version instead, because it's easier to debug (I can put a breakpoint or print statement inside a loop, but not as cleanly inside a comprehension) and easier to read top to bottom — which matters more for a method that surfaces scheduling conflicts to a pet owner than saving a few lines of code.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested: task completion status changes, task addition to a pet (and automatic pet_name tagging), chronological sorting, filtering by pet name, recurring task generation (a completed daily task creates a task for the next day, while a one-off task does not recur), conflict detection (duplicate times flagged, distinct times not flagged, and conflicts across different pets), an edge case of a pet with zero tasks, and that generate_plan() respects both the time budget and priority ordering. These matter because they cover the "smart" behaviors my README explicitly asks for — sorting, filtering, conflicts, recurrence, and planning — not just basic getters/setters.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I'm fairly confident in the scheduler's correctness for the cases it's designed to handle — all 11 of my automated tests pass. If I had more time, I'd test tasks that cross midnight, a weekly task recurring correctly over multiple cycles, and overlapping-but-not-identical time ranges (since my current conflict detection only catches exact matches, as noted in 2b).

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with the recurring task logic and using a dictionary to map frequency strings to `timedelta` objects (`{"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}`) made the date math clean and correct without needing to manually handle month or year rollovers. Seeing `Scheduler.process_completion()` correctly create and attach a new task for the next day in the CLI demo felt like the moment the system actually became "smart" rather than just a data structure.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

If I had another iteration, I'd improve conflict detection to check for overlapping time ranges instead of only exact time matches. Right now, two tasks at 08:00–08:30 and 08:15–08:45 would slip through undetected even though they genuinely overlap. This would require storing an end time (or computing one from `time + duration`) and comparing ranges instead of single timestamps — a bigger change than it sounds, since it touches how conflicts are grouped and reported.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?


The biggest thing I learned is that AI-generated code is only as good as how carefully I check it against my actual requirements. Early on, I built a UML diagram and skeleton from a generic project description before I'd read my real README closely, and it was missing fields (`duration`, `priority`, `preferences`) that my actual assignment needed. Being the "lead architect" meant catching that gap myself by re-reading my own requirements, not just trusting that the first AI-generated draft was complete
