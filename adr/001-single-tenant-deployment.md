# Ganymede — ADR 001: Single-Tenant, Customer-Controlled Deployment

**Status:** Accepted
**Date:** September 2026
**Deciders:** Daniel Kliewer (founder)
**Review trigger:** Before any pilot with live data; before any change to the deployment model.

---

## Context

The product's trust story depends on matter data staying under customer control and not being sent to public model APIs. The buyer is a 10-50 attorney civil-litigation firm with no internal ML platform team. The deployment must be operable by a customer with a technical contact, or by a managed service provider, without requiring enterprise procurement leverage.

The question is: what deployment model makes the trust story legible, operable, and testable for the first pilot and the first annual customers.

---

## Decision

**Ganymede ships as a single-tenant, customer-controlled deployment.**

Each customer receives one isolated stack:
- One Next.js + FastAPI application instance.
- One PostgreSQL database (with pgvector and full-text search).
- One encrypted file volume.
- One local model runtime (Ollama initially, with an adapter boundary for vLLM or another runtime).
- One audit domain.

There is no shared application database or vector index between customers. There is no multi-tenant SaaS layer in the first release.

The default delivery mechanism is a Docker Compose release for a customer-controlled Linux server or private VPC. Managed dedicated hosting is a separately priced option, not the default.

Outbound network access is deny-by-default. No telemetry or inference traffic leaves the deployment unless the customer enables it.

---

## Consequences

**Enables:**
- A trust story that is verifiable: "runs in a customer-controlled environment" is an architecture statement, not a marketing claim.
- Matter isolation that can be proven at the data layer, not just by prompt instruction.
- A deployment model that small firms can operate with a technical contact, or buy as managed hosting.
- An audit trail that is scoped to one customer, one matter boundary at a time.

**Costs:**
- Each customer is a separate deployment. Installation, updates, backup, restore, and support must be repeatable or they become bespoke.
- The founder initially carries the deployment and support burden. This is acceptable in the proof phase; it must be automated or priced before it scales.
- Multi-tenant efficiency is not available. This is deliberate.

**Hardens:**
- The product cannot default to sending matter data to a public model endpoint.
- Cross-customer leakage is structurally impossible at the database and index level, not just at the prompt level.
- The customer's IT/security reviewer has a concrete, inspectable deployment to evaluate.

---

## Alternatives considered

### Multi-tenant SaaS

Rejected. A shared application database or vector index between customers would make the trust story harder to prove and harder to audit. It would also change the buyer profile: the target is a firm that wants control, not a firm that wants a SaaS subscription with a trust promise attached.

Reconsider only if a customer segment emerges that explicitly wants multi-tenant and is willing to pay for it under terms that preserve the trust boundaries.

### Managed hosting as the default

Rejected as the default. Managed dedicated hosting is a real option and is priced separately, but the default is a Docker Compose release the customer or MSP can install. Managed hosting is an expansion of the offer, not a replacement for the customer-controlled default.

### Cloud-hosted inference (public model API)

Rejected. Sending matter data to a public model API is the trust boundary the product is built to avoid. Local inference with an adapter boundary is the path. The adapter exists so the model runtime can change without rewriting the product, not so the product can default to a public endpoint.

---

## References

- [Product Contract](../specification/product-contract.md)
- [Trust Boundaries](trust-boundaries.md)
- [Business Plan — Revenue Model](commercial/plan.md)

---

*This ADR establishes the deployment model. It does not define the deployment mechanics; those are in the operations docs and the Docker Compose release, which will be written in Phase 5.*
