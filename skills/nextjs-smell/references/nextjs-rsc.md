# Next.js RSC / Boundary Reference

Quick-reference for App Router boundary smells (N1–N15, R3, B3).

## The mental model in one paragraph

Every file in `app/` is a Server Component **by default**. Adding `"use client"`
at the top is a one-way door: that file *and everything it imports statically*
ships to the browser. Server Components never ship — they render on the server,
serialise to RSC payload, and the client receives HTML + JSON, not JS. The
single most common smell is putting `"use client"` higher than it needs to be,
which drags subtrees into the client bundle.

## Boundary rules

| You can do this | In a Server Component | In a Client Component |
|---|:---:|:---:|
| `await fetch(...)` directly in body | ✓ | ✗ (use `useEffect` or query lib) |
| Read DB, fs, secrets | ✓ | ✗ |
| `useState`, `useEffect`, `useRef`, custom hooks | ✗ | ✓ |
| Event handlers (`onClick`, `onChange`) | ✗ | ✓ |
| `cookies()`, `headers()` | ✓ (forces dynamic) | ✗ |
| Use Context (`useContext`) | ✗ | ✓ |
| Render a Server Component as a child | ✓ | ✓ (only via `children` prop) |
| Render a Client Component as a child | ✓ | ✓ |

## The `children` pattern (most useful)

A Client Component cannot import a Server Component, but it **can** receive one
as `children`. This lets you keep interactivity at the leaf without dragging
data fetching to the client.

```tsx
// app/dashboard/Sidebar.tsx — client (interactivity)
"use client";
import {useState} from "react";
export default function Sidebar({children}: {children: React.ReactNode}) {
  const [open, setOpen] = useState(true);
  return (
    <aside data-open={open}>
      <button onClick={() => setOpen(o => !o)}>toggle</button>
      {children}
    </aside>
  );
}

// app/dashboard/page.tsx — server (data)
import Sidebar from "./Sidebar";
import {getRecentDocs} from "@/lib/db";
export default async function Page() {
  const docs = await getRecentDocs();
  return (
    <Sidebar>
      <ul>{docs.map(d => <li key={d.id}>{d.title}</li>)}</ul>
    </Sidebar>
  );
}
```

The list is rendered on the server. `Sidebar` toggles a CSS attribute on the
client. No DB calls in the bundle.

## Hard guards: `server-only` / `client-only`

```ts
// lib/db.ts
import "server-only";  // throws at build time if a Client Component imports this
import {Pool} from "pg";
export const pool = new Pool({connectionString: process.env.DATABASE_URL});
```

Use `server-only` in any module that touches secrets, DB, fs, or server-side
SDKs. It turns N1/N2 from a runtime mystery into a build error.

## Common mistakes (smell → fix)

### N1: Server secret in client bundle
```tsx
"use client";
const KEY = process.env.STRIPE_SECRET_KEY;  // 🔴 baked into JS
```
Fix: move the call to a Server Action or route handler. Anything in a
`"use client"` file with `process.env.X` (where X is not `NEXT_PUBLIC_*`) is
either undefined at runtime or a leak.

### N2: Boundary violation via shared util
```ts
// lib/utils.ts — no directive, mixed concerns
import {db} from "@/lib/db";  // server
export function formatDate(d: Date) { return d.toISOString(); }  // pure
export async function getUser(id: string) { return db.user.findUnique(...); }
```
```tsx
"use client";
import {formatDate} from "@/lib/utils";  // 🔴 drags db & secrets in
```
Fix: split. `lib/format.ts` (universal), `lib/db.ts` (`import "server-only"`).

### N3: Hydration mismatch
```tsx
// Server renders different timestamp than client → React warns and replaces DOM
export default function Footer() {
  return <p>© {new Date().getFullYear()}</p>;  // OK on server, but tricky if dynamic
}
```
Fix: render the dynamic part in a Client Component using `useEffect`, or accept
it server-side (year doesn't change between SSR and hydration in the same
request). For real client-only values: `useSyncExternalStore` with an SSR
fallback, or render after `useEffect`.

### N6: Layout reads cookies
```tsx
// app/(dashboard)/layout.tsx — bad
import {cookies} from "next/headers";
export default async function Layout({children}) {
  const theme = cookies().get("theme")?.value ?? "light";
  return <div data-theme={theme}>{children}</div>;
}
```
This forces every page under `(dashboard)` to be dynamic — no static rendering,
no PPR. Move the cookie read to the client (a `<ThemeProvider>`) or to a
specific page that needs it.

### N7: Fetch waterfall
```tsx
const user = await fetchUser();
const orders = await fetchOrders();   // 🔴 doesn't depend on user
const recommendations = await fetchRecommendations();
```
Fix:
```tsx
const [user, orders, recommendations] = await Promise.all([
  fetchUser(), fetchOrders(), fetchRecommendations()
]);
```
Or: render each in its own `<Suspense>` boundary so they stream independently.

### N8: Cache reflexes
- `cache: 'no-store'` everywhere "to be safe" → dynamic everything → no PPR.
- `revalidatePath('/')` after every mutation → invalidates the whole site.
Use cache tags. Tag fetches with what they represent, invalidate by tag:
```ts
fetch(url, {next: {tags: ["orders", `order:${id}`]}});
// later, in a server action:
revalidateTag(`order:${id}`);
```

### N11: `"use client"` everywhere
If most of `app/` has `"use client"`, the App Router is being used as a
glorified Pages Router. Audit: take one page, see how much can move up to a
Server Component. Usually a lot — forms and stateful widgets stay client; data
loading, layouts, and static content move to server.

## When `"use client"` is right

- Interactivity: `useState`, `useReducer`, refs, event handlers.
- Browser-only APIs: `localStorage`, `IntersectionObserver`, Web Audio.
- Libraries that use any of the above (Chart.js, Stripe.js, Framer Motion's
  more dynamic features, react-hook-form).
- Context Providers — but consume context in client components only.

The directive is not "advanced": every interactive widget needs it. The smell
is putting it on the wrong file, not using it at all.