# A/B Test Strategy: Database Connection Flow Optimization

## 1. Test Context & Objective
**Objective:** Increase the conversion rate of users successfully registering their database in the SentinelDB dashboard (`register-db.tsx`).
**Current State:** SentinelDB V3 MVP has just launched. We do not currently have baseline metrics, so our first goal is establishing a baseline, then running our first optimization test. 
**Target Metric:** Connection Rate (Users who submit valid credentials / Total Users who land on the dashboard).

---

## 2. Hypothesis Generation (ICE Prioritization)
Since we aren't sure what the primary friction point is (Trust vs. Complexity vs. Credential Access), we should test the strongest potential blockers first.

### Hypothesis 1: Trust & Security Framing (Recommended First Test)
**Hypothesis:** Because SentinelDB requires read-only access to production databases, we believe that *adding explicit security guarantees (e.g., "Read-only access only", "SOC2 Compliant", "Data is never stored") next to the credential inputs* will increase connection conversion by 15% for new tenants. We'll know this is true when the submit rate of the connection form increases compared to the control.

### Hypothesis 2: Guided Setup vs. Blank Form
**Hypothesis:** Because database hosts and ports can be confusing to locate, we believe *providing a platform-specific toggle (AWS RDS, Supabase, Neon, Custom) that pre-fills standard ports and username formats* will reduce cognitive load and increase connection conversion by 10%. 

**ICE Scores:**
1. **Trust & Security:** Impact (8) + Confidence (7) + Ease (9) = **8.0**
2. **Guided Setup:** Impact (7) + Confidence (6) + Ease (5) = **6.0**

*Decision: We will run Hypothesis 1 first because it requires only copy/layout changes (high Ease) and addresses the most common B2B SaaS blocker (high Impact).*

---

## 3. Test Design: Trust & Security Framing

### Variants
*   **Variant A (Control):** The current `register-db.tsx` form. Standard title ("Connect your Database"), subtitle ("We need read-only access to monitor incidents."), and standard input fields.
*   **Variant B (Security-Enhanced):** 
    *   Change Title to: "Securely Connect your Database"
    *   Change Subtitle to: "SentinelDB uses an encrypted, read-only connection. We never execute DML/DDL or store your raw table data."
    *   Add a visual "Lock" icon badge next to the Password field.
    *   Add a link: "Read our Security Architecture & Guardrails".

### Metrics
*   **Primary Metric:** Form Submission Success Rate.
*   **Secondary Metrics:** Time spent on page, Form abandonment rate (started typing but didn't submit).
*   **Guardrail Metric:** API Error rate (ensuring changes don't confuse users into entering wrong credentials).

---

## 4. Execution & Sample Size Plan

### Baseline Phase (Weeks 1-2)
Since we have no baseline, we must run the Control variant for 1-2 weeks to establish our current Connection Rate (e.g., 20%) and our Weekly Active Traffic.

### Test Phase (Weeks 3-6)
Assuming a baseline of 20% conversion, to detect a 15% relative lift (from 20% to 23% conversion) with 95% statistical significance:
*   **Required Sample Size:** ~3,800 visitors per variant.
*   **Total Traffic Needed:** ~7,600 visitors.
*   **Traffic Allocation:** 50/50 split via PostHog or Optimizely feature flags.

### Pre-Launch Checklist
- [ ] Install A/B testing SDK (e.g., PostHog) in the Next.js `layout.tsx`.
- [ ] Implement Variant B UI components behind a feature flag in `register-db.tsx`.
- [ ] Define the `database_connected_success` event in the analytics platform.
- [ ] QA both variants to ensure the FastAPI `/api/v1/tenant/instances` endpoint fires correctly for both.