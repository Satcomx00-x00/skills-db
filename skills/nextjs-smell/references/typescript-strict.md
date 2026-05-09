# TypeScript Strict Reference

For smells T1–T11. The goal is types that describe reality, with validation at
the boundaries where data enters your program.

## tsconfig flags worth turning on

```jsonc
{
  "compilerOptions": {
    "strict": true,                          // umbrella flag (always on)
    "noUncheckedIndexedAccess": true,        // arr[i] is T | undefined → catches T5
    "exactOptionalPropertyTypes": true,      // {x?: number} ≠ {x: number | undefined}
    "noImplicitOverride": true,              // class methods need `override`
    "noFallthroughCasesInSwitch": true,
    "noPropertyAccessFromIndexSignature": true,  // require obj["x"] for index sigs
    "isolatedModules": true,                 // matches Next.js / SWC reality
    "verbatimModuleSyntax": true             // type-only imports must say `type`
  }
}
```

`strict: true` covers `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`,
`strictBindCallApply`, `strictPropertyInitialization`, `noImplicitThis`, and
`alwaysStrict`. The flags above add to it.

## Validation at the boundary

The fix for T1 (`any`) and T2 (type lie) is almost always: validate, then infer.
Three good libraries:

| Lib | Style | Bundle (gz) | Notes |
|---|---|---|---|
| **zod** | chained builders | ~13KB v4 (smaller than v3) | Most popular, great DX, mature |
| **valibot** | functional, tree-shakable | ~1–3KB | Modular, very small per-validator |
| **arktype** | TS-syntax DSL | ~10KB | Fastest at runtime, nicest types |

### Pattern: validate at the edge, infer the type

```ts
import {z} from "zod";

const User = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  role: z.enum(["admin", "member", "guest"]),
});
type User = z.infer<typeof User>;  // ← single source of truth

// fetch boundary
export async function getUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  return User.parse(await res.json());  // throws if shape lies
}

// server action / route handler boundary
export async function updateUser(formData: FormData) {
  const input = User.partial().parse(Object.fromEntries(formData));
  // input is now safe, typed
}
```

Same pattern for: `localStorage` reads, env vars, URL params, message events.
**If data crosses a trust boundary, validate it.**

## Smell-specific fixes

### T3: Boolean Soup → discriminated union

```ts
// ❌
type State = {
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  data: Data | null;
};
// 16 possible states; most invalid

// ✓
type State =
  | {status: "idle"}
  | {status: "loading"}
  | {status: "success"; data: Data}
  | {status: "error"; error: Error};
// 4 states, all valid; switch is exhaustive
```

### T4: Stringly Typed → literal union or branded type

```ts
// ❌
function setRole(role: string) { /* what values are valid? */ }

// ✓ literal union
type Role = "admin" | "member" | "guest";
function setRole(role: Role) {}

// ✓ branded — when string format matters
type UserId = string & {readonly __brand: "UserId"};
type OrgId  = string & {readonly __brand: "OrgId"};
// Now setUser(orgId) is a type error
```

### T5: Index access without guard

```ts
// With noUncheckedIndexedAccess on:
const items: string[] = [];
const first = items[0];  // string | undefined  ✓

// In a Record:
const map: Record<string, User> = {};
const u = map["x"];  // User | undefined  ✓
if (u) u.name;       // narrowed
```

### T6: Optional chain theatre
4+ `?.` deep usually means the type isn't honest:
```ts
// ❌
const name = response?.data?.user?.profile?.displayName ?? "anon";
```
Either the API response is `unknown` and you should validate it, or you have
the type for `response` and it's lying. Validate at the boundary, then access
without chains.

### T7: `Function`/`object`/`{}`
- `Function` matches anything callable — banned by `@typescript-eslint`. Use
  `(...args: A) => R` with concrete `A`/`R`, or `(...args: unknown[]) => unknown`.
- `object` means "any non-primitive" — almost never what you want. Use
  `Record<string, unknown>` if you mean a generic dict.
- `{}` means "any non-nullish value" (essentially `unknown`). Confusing.

### T8: Enum vs union

```ts
// ❌ TS enum — runtime cost, awkward iteration, tricky with isolatedModules
enum Role { Admin, Member, Guest }

// ✓ string literal union — zero runtime, easy iteration
const ROLES = ["admin", "member", "guest"] as const;
type Role = typeof ROLES[number];

// (use `const enum` only if you understand its caveats with isolatedModules)
```

### T9: Implicit any from JS / 3rd party
Module without types? Don't:
```ts
declare module "untyped-pkg";  // ❌ becomes `any`
```
Do:
```ts
declare module "untyped-pkg" {
  export function foo(x: number): string;
  // narrow to what you actually use
}
```

## Quick checklist

- [ ] `strict: true` and `noUncheckedIndexedAccess: true` in tsconfig
- [ ] No `any`, `as any`, `// @ts-ignore` (use `// @ts-expect-error <reason>`
      with a tracking link if unavoidable)
- [ ] Network/storage/env reads are validated (zod/valibot/arktype)
- [ ] State with mutually-exclusive flags is a discriminated union
- [ ] IDs and similar opaque strings are branded types
- [ ] Multi-state UI uses `switch` on the state field with a `never` default
      (exhaustiveness)