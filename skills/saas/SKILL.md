---
name: saas
description: SaaS product development patterns — multi-tenancy, subscription billing, onboarding flows, feature flags, and operational best practices for building Software-as-a-Service products.
license: MIT
metadata:
  author: Satcomx00-x00
  version: 1.0.0
---

# saas

SaaS product development patterns — multi-tenancy, subscription billing, onboarding flows, feature flags, and operational best practices for building Software-as-a-Service products.

## Instructions

Apply these practices when building SaaS applications:

### Multi-Tenancy

Choose the right isolation model for your use case:

| Model | Description | When to use |
|-------|-------------|-------------|
| Shared schema | All tenants share tables; rows tagged with `tenant_id` | Early stage, cost-sensitive |
| Schema-per-tenant | Separate DB schema per tenant | Medium isolation needs |
| DB-per-tenant | Separate database per tenant | High compliance / enterprise |

**Rules for shared-schema multi-tenancy:**
- Every query **must** filter by `tenant_id` — use middleware or a base repository class to enforce this
- Index `tenant_id` on every tenant-scoped table
- Never expose one tenant's data to another — write integration tests that assert cross-tenant isolation
- Use Row-Level Security (RLS) in PostgreSQL as an additional safety net

```sql
-- Enable RLS
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

### Subscription & Billing

- Delegate billing complexity to a provider (Stripe, Paddle, LemonSqueezy) — do not implement payment processing yourself
- Store only the external `customer_id` and `subscription_id` in your DB, not card data
- Listen to webhook events to keep subscription state in sync:
  - `customer.subscription.created` → activate plan
  - `customer.subscription.updated` → upgrade/downgrade
  - `customer.subscription.deleted` → cancel / grace period
  - `invoice.payment_failed` → notify user, restrict access after grace period
- Implement idempotency for webhook handlers (use the event `id` as an idempotency key)
- Store raw webhook payloads for auditability

### Feature Flags & Plan Gating

- Gate features by plan at the service layer, not the UI alone
- Use a central `can(tenant, feature)` helper that reads entitlements from the subscription record
- Decouple deployment from release with feature flags (LaunchDarkly, Unleash, or a simple DB-backed table)

```ts
// Centralised entitlement check
function can(tenant: Tenant, feature: Feature): boolean {
  return tenant.plan.features.includes(feature);
}

// Usage in a controller
if (!can(tenant, 'advanced_analytics')) {
  return res.status(403).json({ error: 'Upgrade your plan to access this feature' });
}
```

### Onboarding

- Minimise time-to-value: get the user to the "aha moment" as fast as possible
- Use a checklist-style onboarding flow with clear progress indicators
- Send a drip email sequence triggered by user actions (first login, first resource created, etc.)
- Pre-populate sample data for new tenants so the product doesn't feel empty on first use
- Collect the minimum required information upfront; defer everything else

### Observability & Operations

- Emit structured logs with `tenant_id`, `user_id`, and `request_id` on every log line
- Track per-tenant metrics: active users, API call volume, error rate, feature usage
- Alert on tenant-level anomalies (sudden spike or drop in activity)
- Build an internal admin panel for support: impersonate tenant, view audit log, manage subscriptions
- Store an **audit log** for all state-changing actions (who did what, when, from which IP)

### Data Isolation & Security

- Never allow a user to enumerate or access resources from another tenant via predictable IDs — use UUIDs
- Scope all object storage paths by tenant: `s3://bucket/{tenantId}/uploads/{fileId}`
- Validate `tenant_id` on every API call against the authenticated session, not just the request body
- Implement rate limiting per tenant to prevent noisy-neighbour problems

## Examples

```ts
// Tenant-scoped repository base class
class TenantRepository<T> {
  constructor(private readonly tenantId: string, private readonly db: Database) {}

  protected scope() {
    return this.db.where({ tenant_id: this.tenantId });
  }

  async findById(id: string): Promise<T | null> {
    return this.scope().findOne({ id });
  }

  async findAll(): Promise<T[]> {
    return this.scope().find();
  }
}

// Stripe webhook handler with idempotency
app.post('/webhooks/stripe', express.raw({ type: 'application/json' }), async (req, res) => {
  const sig = req.headers['stripe-signature']!;
  const event = stripe.webhooks.constructEvent(req.body, sig, process.env.STRIPE_WEBHOOK_SECRET!);

  const alreadyProcessed = await db.webhookEvents.findOne({ stripeEventId: event.id });
  if (alreadyProcessed) return res.sendStatus(200);

  await db.webhookEvents.create({ stripeEventId: event.id, payload: event });

  switch (event.type) {
    case 'customer.subscription.deleted':
      await subscriptionService.cancel(event.data.object.metadata.tenantId);
      break;
  }

  res.sendStatus(200);
});
```

## References

- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [PostgreSQL Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [The SaaS Playbook – Rob Walling](https://saasplaybook.com/)
- [Twelve-Factor App](https://12factor.net/)
- [LaunchDarkly Feature Flags](https://launchdarkly.com/)
