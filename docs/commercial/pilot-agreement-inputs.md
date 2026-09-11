# Ganymede — Pilot Agreement Inputs

**Status:** Draft
**Date:** September 2026
**Review trigger:** Before any pilot agreement is sent. Must be reviewed by qualified counsel.

---

**Warning:** This is a checklist of inputs that must be reflected in the pilot agreement and related documents. It is not a contract. It does not constitute legal advice. Counsel must draft and review the actual agreement, terms, and any data-processing arrangements.

---

## Pilot parameters

- **Pilot duration:** 30 days.
- **Scope:** one matter, up to 10 named users.
- **Price:** $4,500 fixed, credited toward an annual agreement if converted.
- **Includes:** onboarding, deployment support, three guided tasks, weekly review, final scorecard.
- **Excludes:** customer hardware, cloud infrastructure, unusual document migration, bespoke integrations.

---

## Corpus and data

- Define the approved pilot corpus: synthetic, public-domain, or expressly authorized.
- If real matter documents are used: written permission and handling terms before ingestion. This must include what may be stored, who may access it, retention, and deletion terms.
- Define what data enters the deployment and under what terms.
- Define what data does not enter the deployment.
- Define retention during the pilot and deletion after the pilot ends.
- Define operator access: who can access matter content for support, under what conditions, and with what logging.

---

## Security and confidentiality

- Describe the deployment model: customer-controlled single-tenant environment.
- Describe data flow: what travels where, and what never leaves the deployment by default.
- Describe encryption: TLS, encrypted file volume, managed secrets.
- Describe backup: daily encrypted backup, tested restore.
- Describe egress: default-deny outbound network policy; no telemetry or inference traffic leaves unless the customer enables it.
- Describe incident handling: who is notified, under what process, and what happens to the deployment during an incident.

---

## Professional responsibility

- Acknowledge that the product is a tool, not a lawyer.
- Acknowledge that the product does not claim to practice law, produce legally accurate conclusions, or automatically satisfy professional duties.
- Acknowledge that the firm's lawyers remain responsible for evaluating their own professional duties, including those described in applicable guidance such as ABA Formal Opinion 512.
- The product should surface information that helps a lawyer evaluate those duties; it does not promise automatic compliance.

---

## Acceptance criteria

- Pre-pilot baseline recorded.
- Three guided tasks completed.
- Pilot scorecard completed: active users, meaningful tasks, output usefulness after edits, median reported time saved, citation support, unsupported-claim rate, matter isolation, audit completeness.
- Written continuation decision or a specific, categorized loss reason.

---

## Liability and limitations

- Define liability limits, disclaimers, and intellectual property ownership of outputs.
- Define what happens to matter data at the end of the pilot.
- Define what happens if the pilot is terminated early.

---

## Conversion terms

- Define the path from paid pilot to annual contract.
- Define the pilot credit mechanism.
- Define what must be true for conversion to be offered (repeated use, quality pass, commercial sponsor).

---

## Action

Before any pilot corpus is ingested, qualified legal counsel must establish confidentiality, data-processing, incident, retention/deletion, liability, and permitted-use terms. This checklist is a product and engineering input, not legal advice.

---

*This document must be reviewed by qualified counsel before any pilot agreement is sent.*
