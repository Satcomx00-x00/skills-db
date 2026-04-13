---
name: nextjs
description: Next.js best practices — App Router conventions, rendering strategies, data fetching, routing, performance optimisation, and deployment patterns for production Next.js applications.
license: MIT
metadata:
  author: Satcomx00-x00
  version: 1.0.0
---

# nextjs

Next.js best practices — App Router conventions, rendering strategies, data fetching, routing, performance optimisation, and deployment patterns for production Next.js applications.

## Instructions

Apply these practices when building Next.js applications:

### App Router Conventions

Use the **App Router** (`app/`) for all new projects (Next.js 13+). Understand the file conventions:

| File | Purpose |
|------|---------|
| `layout.tsx` | Shared UI wrapper; persists across navigation |
| `page.tsx` | Route segment UI; publicly accessible |
| `loading.tsx` | Suspense boundary fallback for the segment |
| `error.tsx` | Error boundary for the segment (client component) |
| `not-found.tsx` | Rendered when `notFound()` is called |
| `route.ts` | API route handler (replaces `pages/api/`) |
| `middleware.ts` | Runs before request; use for auth guards, redirects |

**Server vs. Client Components:**
- Components are **Server Components by default** — they run on the server only, have no JS bundle cost, and can `async`/`await` directly
- Add `'use client'` only when you need: browser APIs, event listeners, React hooks (`useState`, `useEffect`), or third-party client-only libraries
- Push `'use client'` boundaries as far down the component tree as possible

```tsx
// Server Component — fetch directly, no useEffect needed
export default async function UserProfile({ params }: { params: { id: string } }) {
  const user = await db.user.findUnique({ where: { id: params.id } });
  if (!user) notFound();
  return <ProfileCard user={user} />;
}
```

### Rendering Strategies

Choose the right rendering strategy per route:

| Strategy | When to use | Next.js mechanism |
|----------|-------------|-------------------|
| **SSR** (Dynamic) | Personalised, real-time data | Default for routes using `cookies()`, `headers()`, or dynamic params |
| **SSG** (Static) | Public, infrequently changing content | `export const dynamic = 'force-static'` or no dynamic APIs |
| **ISR** | High-traffic pages that can tolerate slight staleness | `export const revalidate = 60` (seconds) |
| **Streaming** | Long data fetches; show content progressively | Wrap with `<Suspense>` |

Avoid `export const dynamic = 'force-dynamic'` globally — apply it only to routes that truly need it.

### Data Fetching

- Fetch data in **Server Components** wherever possible — avoids client round-trips
- **Co-locate** fetches with the component that needs the data; React deduplicates concurrent identical `fetch()` calls automatically
- Use `cache()` from React to share expensive computations across a request:

```ts
import { cache } from 'react';
import { db } from '@/lib/db';

export const getUser = cache(async (id: string) => {
  return db.user.findUnique({ where: { id } });
});
```

- Mutations must go through **Server Actions** (preferred) or API route handlers

```tsx
// Server Action
'use server';

export async function updateProfile(formData: FormData) {
  const name = formData.get('name') as string;
  await db.user.update({ where: { id: session.userId }, data: { name } });
  revalidatePath('/profile');
}
```

### Routing & Navigation

- Use `<Link>` for all internal navigation (prefetches on hover)
- Use `useRouter().push()` for programmatic navigation in Client Components
- Use `redirect()` in Server Components / Server Actions
- Parallel routes (`@slot`) for modals or split-pane layouts
- Intercepting routes (`(.)segment`) for route-level modals (e.g., photo lightbox)
- Protect routes in `middleware.ts` by checking session tokens before the response is rendered

```ts
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';

export function middleware(req: NextRequest) {
  const token = req.cookies.get('session')?.value;
  if (!token && req.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', req.url));
  }
}

export const config = { matcher: ['/dashboard/:path*'] };
```

### Performance

- **Images**: always use `next/image` — auto-resizes, converts to WebP/AVIF, lazy-loads
- **Fonts**: use `next/font` — zero layout shift, self-hosted, tree-shaken
- **Scripts**: use `next/script` to control third-party script loading strategy
- **Bundle analysis**: run `ANALYZE=true next build` with `@next/bundle-analyzer` to spot large dependencies
- **Partial Prerendering (PPR)**: wrap dynamic shells in `<Suspense>` to serve a static outer shell instantly (Next.js 14+)
- Keep Server Component trees free of unnecessary `'use client'` directives — every client boundary increases bundle size

### Environment Variables

- `NEXT_PUBLIC_*` — exposed to the browser bundle; use only for non-secret config
- All other `process.env.*` — server-only; never leaked to the client
- Validate env vars at startup with `zod`:

```ts
// lib/env.ts
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  NEXTAUTH_SECRET: z.string().min(32),
  NEXT_PUBLIC_APP_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
```

### Error Handling

- Every route segment should have an `error.tsx` Client Component to catch render errors
- Use `notFound()` to render `not-found.tsx` for missing resources
- Wrap Server Actions in try/catch and return typed error objects — never throw unhandled errors to the client

## Examples

```tsx
// app/dashboard/layout.tsx — persistent sidebar
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  );
}

// app/dashboard/page.tsx — streaming with Suspense
import { Suspense } from 'react';

export default function DashboardPage() {
  return (
    <>
      <h1>Dashboard</h1>
      <Suspense fallback={<StatsSkeletons />}>
        <Stats />  {/* async Server Component */}
      </Suspense>
    </>
  );
}
```

## References

- [Next.js Documentation](https://nextjs.org/docs)
- [App Router Migration Guide](https://nextjs.org/docs/app/building-your-application/upgrading/app-router-migration)
- [Server Components RFC](https://github.com/reactjs/rfcs/blob/main/text/0188-server-components.md)
- [Vercel Deployment](https://vercel.com/docs)
- [next/image](https://nextjs.org/docs/app/api-reference/components/image)
