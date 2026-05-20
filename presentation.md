# KabaarAgent: AI-Driven Appraisal & Trading Engine 🤖♻️
> **A Submission for Google Antigravity Hackathon 2026**
> *Developed by: Usman Mughal (usman.mughal@taleemabad.com)*

---

## Slide 1: Executive Summary
*   **The Problem**: Informal scrap collectors handle raw, transliterated, and highly unstructured transactions. They lack transparent pricing indexes, visual classification tools, and secure bookkeeping ledger records.
*   **The Solution**: **KabaarAgent** is a complete, full-stack visual appraisal and trading engine. It allows collectors to snap pictures or dictate notes, translates local languages, projects payouts across local yards, and signs logs cryptographically.

---

## Slide 2: System Architecture & Layout
```
     [Android Client]                  [FastAPI Gateway]
   +-------------------+              +------------------+
   |  Jetpack Compose  |    POST      |  uvicorn server  |
   |   Material 3 UI   | -----------> |   (Port 8080)    |
   +-------------------+  /pipeline   +------------------+
                                               |
                                     +---------+---------+
                                     |                   |
                                     v                   v
                               [Appraiser]          [Arbitrage]
                             (Gemini Flash)       (Haversine Proximity)
                                     |                   |
                                     +---------+---------+
                                               |
                                               v
                                         [Ops Ledger]
                                      (HMAC Cryptography)
```

---

## Slide 3: Component-Level Specifications

### 🤖 Appraiser Agent (Gemini 3.5 Flash)
*   **Visual Analysis**: Converts base64 image captures of scrap materials to identify category and quality grades.
*   **Multilingual NLP**: Translates transliterated Urdu/Hindi notes (e.g. *"5kg copper wires aur purani copper tonti, baqi loha hai"*) and scales weights dynamically.
*   **Zero-Network Fallback**: Automatically switches to local rule-based regex parsing when connection is unavailable.

### 📍 Arbitrage Proximity Projector
*   **Haversine Proximity**: Calculates physical distances to local Rawalpindi recycling yards.
*   **Optimal Yield**: Verifies material availability, matching requirements, minimum batch thresholds, and projects the highest payout.

### 🔒 Operations Ledger (Security & Log Dispatch)
*   **Cryptographic Verification**: Hashes transaction details with HMAC-SHA256.
*   **Auditable Record**: Writes to local databases and compiles diagnostic trace streams.

---

## Slide 4: Production & Deployment Details
*   **FastAPI Cloud Container**: Deployed to Railway with dynamic binding to cloud-assigned `$PORT` for reverse-proxy routing.
    *   **Live Endpoint**: `https://kabaar-agent-production.up.railway.app/`
*   **Android App Package**: Standalone debug APK pre-configured to communicate directly with the production API.
*   **Trace Records**: Complete workspace log file bundle stored at `antigravity_trace.zip`.

---

## Slide 5: Innovation & Impact
1.  **Aesthetic Developer Glassmorphism**: Provides real-time visibility into internal agent steps in the mobile client terminal console.
2.  **Low-Latency Resiliency**: Structural fallback engines ensure continuous trading in weak network zones.
3.  **Audit Trail**: Cryptographic signing prevents transaction tampering.
