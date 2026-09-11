# Ganymede — Interview Capture Template

**Status:** Draft
**Date:** September 2026
**Purpose:** Capture a single discovery interview in a form that feeds directly into the four discovery-outputs.md sections (workflow map, economic baseline, risk baseline, buying map). Use one copy per interview; file the filled copy in `docs/discovery/`.

**Rule:** Do not demo first. Ask them to walk through a recent matter task. The interview script is in `docs/discovery/interview-script.md`. This template is the capture layer on top of that script.

---

## Interview header

```markdown
# Interview Capture — <firm identifier or subject>

**Date:** —
**Interviewer:** Daniel Kliewer
**Interviewee(s):** — (names, roles, and whether they are the sponsor / approver / end user / IT / risk)
**Duration:** —
**Mode:** in person / video / phone
**Notes on setting:** —
**Warm-up or intro used:** (if a warm intro was used, note it; otherwise note that this was a cold outreach reply)
```

---

## Opening (do not skip)

Record whether the interviewee was told, before any questions, that:

- This is research, not a pitch.
- The goal is to understand one recent matter task: what the documents were, what the job was, where the time went, and what review points existed.
- If a question does not fit their practice, the honest answer is more useful than a polite one.

**Opening delivered?** yes / no / partially.
**Interviewee's initial reaction:** —.

---

## The matter walk-through

**Matter chosen by interviewee:** — (what matter they walked through; if they declined to name one, note why).

### 1. Show me the last chronology or internal memo you built.

**Answer:** —

**Matter type:** —
**Document set (types and rough scale):** —
**Who built it:** —

### 2. Where did you spend the most time?

**Answer:** —

**Specific time sinks named (searching filenames, reading to find a date, reconciling versions, verifying a claim before drafting, other):** —

### 3. Which documents were involved?

**Documents named (PDF, scanned PDF, Word, email, notes, other):** —
**Rough page count:** —
**Naming / organization:** —
**Inconsistencies in naming or organization:** —

### 4. How were the files organized?

**Answer:** —

### 5. Who touched this matter?

**Roles named and what each did:** —

### 6. What was the review chain?

**Who reviewed the chronology or memo before it was used or sent:** —
**What they checked for:** —
**What caused rework (if any):** —

### 7. What would make you distrust an answer immediately?

**Answer:** —

**Specific distrust triggers named (wrong date, source you can't find, claim not in the record, other):** —

### 8. Which data can never leave your control?

**Answer:** —

**Absolute boundary named:** —

### 9. Who approves a new tool and what evidence do they require?

**Approver roles named:** —
**Evidence each requires (security review, data flow, citations, audit trail, references, pilot terms, other):** —

### 10. If you could only solve one expensive job with a tool like this, what would it be?

**Answer:** —

**The one job they named:** —

---

## Current AI behavior (if it came up)

### 11. Have you used any AI tool on client or matter documents?

**Answer:** —

**Tool used (if any):** —
**Conditions under which it was used:** —

### 12. What did you check before using it?

**Answer:** —

**If they did not check anything:** note that explicitly.

### 13. What would have to be true for you to use an AI tool on a real matter file?

**Answer:** —

**Specific conditions named:** —

---

## Buying path

### 14. Who would need to sign off on a tool like this?

**Roles named (not just the person):** —
**Current approval process (if described):** —

### 15. What evidence would they want before approving?

**Evidence named (security review, data flow, citations, audit trail, references, pilot terms, other):** —

### 16. Is there a budget owner or procurement path?

**Answer:** —

**Budget owner named (if any):** —
**Procurement path described (if any):** —
**If no budget owner or procurement path:** note as a possible disqualifier.

---

## Closing

### 17. What would make you walk away from a tool like this after one use?

**Answer:** —

### 18. Is there a matter you could share for a pilot that has no client-confidentiality barrier?

**Answer:** —

**Synthetic / public / expressly authorized corpus available?** yes / no / maybe / not addressed.

### 19. Would you be willing to review a prototype or a citation sample before committing?

**Answer:** —

**Yes / no / "show me the workflow first" / other:** —

---

## Evidence scoring (from the interview script's buyer evidence ladder)

For this interview, score the evidence on the three-tier ladder. Move the prospect up only when the evidence changes.

| Tier | Definition | This interview |
|------|------------|----------------|
| Weak | "Interesting," newsletter signup, social reaction, feature suggestion. | |
| Useful | Introduces IT, offers a corpus, schedules reviewers, shares current cost. | |
| Strong | Reviews terms, names budget, signs pilot, or pays. | |

**Highest tier reached this interview:** weak / useful / strong.

**Evidence supporting that tier (quote or summarize):** —

---

## Discovery-outputs mapping

This section is the bridge to `docs/discovery/discovery-outputs.md`. After the interview, transfer these answers into the four output documents. Do not leave the capture template as the only record.

### To Workflow Map

- **Trigger:** — (what starts the work)
- **Inputs:** — (documents and files involved)
- **Actors and roles:** — (who does what)
- **Work, in sequence:** — (steps, in order)
- **Review:** — (who reviews, what they check, what causes rework)
- **Output:** — (what is produced and where it goes)
- **Pain points (observer notes):** — (where time went, where friction occurred, where distrust would arise)

### To Economic Baseline

- **People:** — (roles and counts)
- **Time, observed:** — (how long the job took, by activity)
- **Frequency:** — (how often this job occurs)
- **Delay sources:** — (what made it slower than it should be)
- **Write-offs or rework:** — (hours written off, errors that caused rework)
- **Current tool path:** — (what they use now, in sequence)
- **Before baseline (for later comparison):** — (one-paragraph description of current state, in their words if possible)

### To Risk Baseline

- **Where matter data lives:** — (locations, systems, devices)
- **Who can access what:** — (boundaries, or absence of them)
- **Vendor exposure:** — (third-party tools receiving matter data, terms if known)
- **Retention and deletion:** — (how long, who can delete, whether deletion is real)
- **AI usage today:** — (any generative AI use on matter content, conditions, what was checked)
- **Confidentiality boundary (firm's absolute line):** — (what can never leave their control)

### To Buying Map

- **Sponsor:** — (name or role, what they own, what would make them proceed)
- **Approver(s):** — (roles, what evidence each requires)
- **IT / security reviewer:** — (role, what they will ask, what stack or posture they need)
- **End users:** — (roles, what they would use it for, what would make them trust it)
- **Budget owner / procurement path:** — (who controls budget, how purchases happen)
- **Proof required at each stage:** — (discovery → demo → technical review → pilot → annual close)
- **Disqualifiers observed:** — (any that apply)

---

## Safe corpus check

- **Is a safe corpus plausible for this firm?** yes / no / maybe / not addressed.
- **If yes, what kind?** synthetic / public / expressly authorized / not specified.
- **If expressly authorized is plausible, what is needed to get there?** (written permission, handling terms, who signs, timeline)
- **If no safe corpus is plausible, why?** —

---

## Champion check

- **Is there a champion?** yes / no / unclear.
- **If yes, who, and what makes them a champion?** (they introduced the idea of a pilot, offered a corpus, scheduled reviewers, or otherwise moved past polite interest)
- **If no, what would it take to create one?** —

---

## Disqualifiers observed

From the interview script's disqualifier list. Check any that apply.

- [ ] The only interest is "AI is exciting."
- [ ] No one will supply a safe corpus or review outputs.
- [ ] The desired use case requires licensed legal content on day one.
- [ ] The buyer expects autonomous legal advice or guaranteed accuracy.
- [ ] Every prospect demands a different first integration.
- [ ] No budget owner or procurement path.

**If any are checked, record the detail and the decision (move on; do not try to overcome with persuasion).** —

---

## Disposition

- **Next step:** — (send follow-up, schedule technical review, request corpus access, move on, other)
- **Prospect stage after this interview:** qualified contact / live conversation / commitment advance / moved on.
- **Stage-change evidence (if any):** — (what changed the stage, if it changed)

---

## After the interview

1. Transfer the four discovery-outputs sections into their respective documents in `docs/discovery/`.
2. Update the prospect stage in `docs/sales/prospect-tracking.md` and the Week scorecard if the stage changed.
3. If a live conversation or commitment advance occurred, record the evidence in the scorecard's demand section.
4. File this capture template in `docs/discovery/<interview-date>-<firm-identifier>-capture.md`.

---

*This template is the capture layer for discovery interviews. It maps directly to the four discovery-outputs.md sections and to the buyer evidence ladder. It is not a survey; it is a structured record of a real conversation.*
