# Frontend Dashboard for V3 SaaS (React/Next.js) Requirements

## Problem Frame
SentinelDB's V3 backend now supports true multi-tenancy, JWT-based authentication, and mocked billing integration. However, the system lacks a customer-facing interface. We need to build a production-grade SaaS frontend that allows users (Startup CTOs, small team leads, DBEs) to onboard, connect their databases, and view DB incident RCAs securely within their isolated tenant context. 

The dashboard must look and feel premium, utilizing advanced design system practices (e.g., bento grids, minimalism) guided by specialized frontend AI skills.

---

## Core Workflows

### F1. SaaS Onboarding & Authentication
- User signs up / logs in via Supabase Auth.
- User is prompted to select a subscription plan (simulated via Stripe Mock).
- User lands on an onboarding wizard to register their first database instance (Instance Registry integration).

### F2. Tenant Isolation & Navigation
- The active tenant context is maintained in the URL path (`/t/[tenantId]/...`).
- Server Components act as a Backend-for-Frontend (BFF), forwarding the JWT to the FastAPI backend while ensuring cross-tenant data leaks are impossible on the frontend.
- Users can switch tenants via a global navigation dropdown if they belong to multiple workspaces.

### F3. Incident Management & Reporting
- **Live Incident Feed:** A real-time or frequently polled list of active incidents.
- **Incident Report View:** A detailed, scannable view of the deterministic RCA, split into Root Cause, Why This Is Most Likely, Runbook Match, and Safe Next Actions.
- **Evidence Panel:** Expandable drawers or side-panels displaying raw metric values and charts (CPU, Connections, etc.).
- **Manual Trigger:** A form to select an instance, alert focus, and time window to force an analysis job.

---

## Requirements

**R1.** The application must be built using Next.js (App Router).
**R2.** Data fetching and mutations must primarily utilize React Server Components and Server Actions to hide API endpoints and tokens from the browser.
**R3.** The UI must implement a path-based tenant isolation strategy (`/t/[tenantId]`) to ensure all incident links are inherently tenant-aware and shareable.
**R4.** The frontend must integrate with the existing FastAPI backend (`AUTH_ENFORCED=true`) by attaching the Supabase JWT to all requests.
**R5.** A "Settings" area must exist for users to view their billing status (Active/Mocked) and manage their registered DB instances.
**R6.** The design execution must leverage advanced UI/UX skills (`impeccable`, `ui-ux-pro-max`) to deliver a high-quality, non-templated look and feel.

---

## Scope Boundaries

### Deferred to Follow-Up Work
- Real Stripe checkout integration (using mock status for now).
- Multi-user RBAC within a single tenant (assume one admin user per tenant for V3 MVP).
- Real-time WebSockets for incident updates (polling or manual refresh is acceptable for V3 MVP).

### Outside this product's identity
- Direct execution of SQL queries from the dashboard.
- Modifying database infrastructure or configurations from the UI.

---

## Key Technical Decisions
1. **Next.js App Router:** Chosen over React+Vite (from V1C plan) to provide a secure BFF layer, SSR for faster initial loads, and better SEO/Auth handling patterns.
2. **Path-Based Tenancy:** Picked over global state context to allow for robust deep-linking to specific incident reports, which is critical for incident response collaboration.
3. **Stripe Mocking:** We will mock the billing portal on the frontend to match the backend's current 'active' mock response, preventing blockers while testing the core UI.
