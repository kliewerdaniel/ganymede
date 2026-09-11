# Ganymede — Discovery Outputs

**Phase:** Discovery (Weeks 1-2)
**Purpose:** Characterize the job, the buyer, the risk, and the corpus before writing code.

Every discovery session produces four documents. They are not templates to fill in abstractly — they are observations about a real workflow.

---

## 1. Workflow map

**Trigger** — What starts the work? A new matter opening, a deposition date, a discovery deadline, a client request?

**Inputs** — What documents, files, notes, and prior work products go into this task?

**Actors** — Who touches it? Attorneys, paralegals, associates, support staff. What each one does.

**Work** — What happens, in sequence. Collecting files. Searching. Reading to find dates or contradictions. Building the chronology. Drafting the memo. Verifying claims against sources. Reviewing before use.

**Review** — Who reviews the output, what they check for, what causes rework.

**Output** — What is produced and where it goes: internal memo, chronology, deposition prep, client update, court filing (if any).

**Template:**

```markdown
# Workflow Map — <matter type or job>

## Trigger
<what starts this>

## Inputs
<documents and files involved>

## Actors and roles
<who does what>

## Work, in sequence
1. <step>
2. <step>
...

## Review
<who reviews, what they check, what causes rework>

## Output
<what is produced and where it goes>

## Pain points (observer notes)
<where time went, where friction occurred, where distrust would arise>
```

---

## 2. Economic baseline

This is the before picture. It must be specific enough that you could measure a change against it.

**People involved** — Roles and how many of each.

**Hours** — How long the job took, rough breakdown by activity.

**Frequency** — How often this job occurs. Per matter? Per month? Per year?

**Delay** — What makes it take longer than it should. Waiting on someone, searching, re-reading, verifying.

**Write-offs** — Hours written off or unbilled because of rework, error, or delay.

**Template:**

```markdown
# Economic Baseline — <matter type or job>

## People
<roles and counts>

## Time, observed
<how long the job took, by activity>

## Frequency
<how often this job occurs>

## Delay sources
<what made it slower than it should be>

## Write-offs or rework
<hours written off, errors that caused rework>

## Current tool path
<what they use now, in sequence>

## Before baseline (for later comparison)
<a one-paragraph description of the current state, in their words if possible>
```

---

## 3. Risk baseline

Where does confidential data currently travel? This is the before picture for the trust story.

**Data locations** — Where matter files live now. Network drives, practice-management systems, email, local machines, consumer AI tools (if any).

**Access boundaries** — Who can see what. Are there boundaries, or does everyone with matter access see everything?

**Vendor exposure** — Any third-party tools that receive matter data. Under what terms.

**Retention and deletion** — How long files are kept, who can delete them, whether deletion is real.

**AI usage today** — Have anyone uploaded matter content to a generative AI tool? Which one, under what conditions, and what did they check first?

**Template:**

```markdown
# Risk Baseline — <matter type or job>

## Where matter data lives
<locations, systems, devices>

## Who can access what
<boundaries, or absence of them>

## Vendor exposure
<third-party tools receiving matter data, terms if known>

## Retention and deletion
<how long, who can delete, whether deletion is real>

## AI usage today
<any generative AI use on matter content, conditions, what was checked>

## Confidentiality boundary (firm's absolute line)
<what can never leave their control>
```

---

## 4. Buying map

Who is in the buying committee, what they care about, and what proof they need.

**Roles:**
- Managing partner / sponsor — owns the problem, decides whether to proceed.
- Litigation partner — can trust and verify it.
- Associate / paralegal — uses it, feels whether it reduces rework.
- IT / MSP — can operate it, approves deployment.
- Risk / counsel — where does data travel, what are the terms.

**Template:**

```markdown
# Buying Map — <firm>

## Sponsor
<name or role, what they own, what would make them proceed>

## Approver(s)
<roles, what evidence each requires>

## IT / security reviewer
<role, what they will ask, what stack or posture they need>

## End users
<roles, what they would use it for, what would make them trust it>

## Budget owner / procurement path
<who controls budget, how purchases happen>

## Proof required at each stage
<discovery → demo → technical review → pilot → annual close>

## Disqualifiers observed
<any that apply>
```

---

## Discovery exit criteria

Discovery is complete when:

- One practice workflow, one buyer, one champion, one costly job are identified.
- Signed-off spec and corpus exist (or a clear path to them).
- No unresolved critical data-flow question remains.
- A design-partner letter or written pilot-review commitment is secured (or a clear reason it is not).

If these are not met, do not proceed to implementation. Narrow the workflow or change the market.

---

## File naming

`docs/discovery/<interview-date-or-topic>-<firm-identifier-or-subject>.md`

Examples:
- `docs/discovery/2026-09-15-texas-civil-litigation-firm-a-workflow.md`
- `docs/discovery/economic-baseline-document-heavy-matters.md`
- `docs/discovery/risk-baseline-confidential-data-flow.md`
- `docs/discovery/buying-map-small-firm-litigation.md`
