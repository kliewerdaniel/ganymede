# Week 5 — Q&A workspace build

## Frontend structure

Building a single-page app in `web/` that talks to the FastAPI backend.

### Components:
1. **Matter home** — list of matters, document count, last activity
2. **Document inventory** — table of documents with metadata
3. **Question workspace** — ask a question, get streaming answer with citations
4. **Answer history** — past questions and answers
5. **Source inspector** — split view with answer on left, document on right
6. **Citation drawer** — click citation → opens PDF at page, highlights passage
7. **Citation feedback** — supporting / weak / wrong / inaccessible buttons

### Trust constraints:
- Matter authorization filters retrieval before prompt assembly
- Every citation carries document hash, page, offsets, retrieval scores
- No export without deliberate human action
- Prompt injection filtering on input
- Quoted-source boundaries in output

## API endpoints needed:
- `GET /api/v1/matters` — list matters
- `GET /api/v1/matters/{id}/documents` — document inventory
- `POST /api/v1/matters/{id}/ask` — ask a question (streaming)
- `GET /api/v1/matters/{id}/history` — answer history
- `POST /api/v1/citations/{id}/feedback` — citation feedback
