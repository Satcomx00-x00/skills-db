---
name: code-quality
description: Code quality mastery — programming principles (SOLID, DRY, KISS, YAGNI…), refactoring techniques, and design patterns to write clean, maintainable, extensible software.
license: MIT
metadata:
  author: Satcomx00-x00
  version: 1.0.0
---

# code-quality

Code quality mastery — programming principles (SOLID, DRY, KISS, YAGNI…), refactoring techniques, and design patterns to write clean, maintainable, extensible software.

## Instructions

Apply code quality practices to continuously improve codebases:

### Programming Principles

Core principles every codebase should follow regardless of language or paradigm.

#### SOLID

Five OOP principles that make systems easy to extend and maintain:

| Principle | Full name | Rule |
|-----------|-----------|------|
| **S** | Single Responsibility | A class/module has one reason to change |
| **O** | Open/Closed | Open for extension, closed for modification |
| **L** | Liskov Substitution | Subtypes must be substitutable for their base type |
| **I** | Interface Segregation | Prefer many small interfaces over one fat interface |
| **D** | Dependency Inversion | Depend on abstractions, not concretions |

**S — Single Responsibility**
```ts
// ❌ one class handles both data and formatting
class Report { generate() {} formatAsPdf() {} sendByEmail() {} }

// ✅ each class has one job
class Report      { generate(): ReportData {} }
class PdfRenderer { render(data: ReportData): Buffer {} }
class Mailer      { send(to: string, body: Buffer) {} }
```

**O — Open/Closed**
```ts
// ❌ must edit existing class to add discount type
class Discount { calc(type: string, price: number) {
  if (type === 'vip') return price * 0.8;
  if (type === 'seasonal') return price * 0.9;
}}

// ✅ add new behaviour by adding a new class
interface Discount { apply(price: number): number; }
class VipDiscount      implements Discount { apply(p) { return p * 0.8; } }
class SeasonalDiscount implements Discount { apply(p) { return p * 0.9; } }
```

**L — Liskov Substitution**
```ts
// ❌ Square overrides setWidth in a way that violates Rectangle's contract
class Rectangle { setWidth(w: number) {} setHeight(h: number) {} area() {} }
class Square extends Rectangle { setWidth(w: number) { super.setWidth(w); super.setHeight(w); } }

// ✅ use a shared Shape interface instead of inheritance
interface Shape { area(): number; }
class Rectangle implements Shape { area() { return this.w * this.h; } }
class Square    implements Shape { area() { return this.side ** 2; } }
```

**I — Interface Segregation**
```ts
// ❌ Printer forced to implement fax it doesn't support
interface Machine { print(): void; scan(): void; fax(): void; }

// ✅ split into focused interfaces
interface Printer { print(): void; }
interface Scanner { scan(): void; }
interface Fax     { fax(): void; }
class SimplePrinter implements Printer { print() {} }
```

**D — Dependency Inversion**
```ts
// ❌ high-level module depends on low-level concrete class
class OrderService { private db = new MySqlDatabase(); }

// ✅ depend on an abstraction; inject the implementation
interface Database { save(data: object): void; }
class OrderService { constructor(private db: Database) {} }
```

---

#### DRY — Don't Repeat Yourself

> "Every piece of knowledge must have a single, unambiguous, authoritative representation within a system." — The Pragmatic Programmer

- **Duplication of logic** → extract into a shared function, class, or module
- **Duplication of data** → derive it from a single source of truth; don't copy-paste constants
- **Duplication of structure** → use generics, templates, or higher-order functions
- **What DRY is NOT**: don't blindly deduplicate code that looks the same but represents different concepts — premature abstraction is worse than duplication

```ts
// ❌ same validation logic copy-pasted in three places
function createUser(email: string) { if (!email.includes('@')) throw new Error('Invalid'); }
function updateUser(email: string) { if (!email.includes('@')) throw new Error('Invalid'); }

// ✅ single source of truth
function assertValidEmail(email: string) { if (!email.includes('@')) throw new Error('Invalid email'); }
function createUser(email: string) { assertValidEmail(email); }
function updateUser(email: string) { assertValidEmail(email); }
```

---

#### KISS — Keep It Simple, Stupid

> "Simplicity is the ultimate sophistication." — Leonardo da Vinci

- Write the simplest solution that solves the problem
- Avoid clever tricks, unnecessary abstractions, and premature generalisation
- Code is read far more often than it is written — optimise for the reader
- If you need a comment to explain *what* code does, the code is probably too complex

```ts
// ❌ over-engineered
const isAdult = (age: number) => !!(age >= 18 ? true : false) === true;

// ✅ simple and clear
const isAdult = (age: number) => age >= 18;
```

---

#### YAGNI — You Aren't Gonna Need It

> "Always implement things when you actually need them, never when you just foresee that you need them." — Ron Jeffries (XP)

- Don't add functionality, abstractions, or configuration hooks "just in case"
- Every line of speculative code must be maintained, tested, and understood
- Prefer to refactor when the need arises; don't design for imaginary requirements
- Works in tandem with KISS — both fight accidental complexity

---

#### Law of Demeter (LoD) — Principle of Least Knowledge

> "Only talk to your immediate friends."

A method should only call methods on:
1. Its own object (`this`)
2. Objects passed as parameters
3. Objects it creates itself
4. Its direct component objects

```ts
// ❌ "train wreck" — violates LoD
const city = customer.getAddress().getCity().getName();

// ✅ ask the object, don't dig into it
const city = customer.getCityName();
```

---

#### CQS — Command-Query Separation

Every method should be **either**:
- A **Query**: returns a value, has no side effects (safe to call multiple times)
- A **Command**: performs an action/mutation, returns `void`

Never both. (See also the [`separate-query-from-modifier`](separate-query-from-modifier/SKILL.md) refactoring.)

---

#### SoC — Separation of Concerns

Different concerns (UI, business logic, persistence, networking) must live in separate modules with clear boundaries. Changes to one concern should not ripple into others.

- **MVC / layered architecture**: Controller ↔ Service ↔ Repository
- **CSS/HTML/JS separation** in frontend
- **Domain logic must not import HTTP or DB packages**

---

#### Fail Fast

Detect and surface errors as early and loudly as possible:
- Validate inputs at the entry point (constructor, API boundary)
- Throw/return errors immediately when a precondition is violated
- Never silently swallow exceptions
- Prefer explicit `null` / `undefined` checks over optional chaining that hides bugs

```ts
// ❌ silent failure — caller has no idea something went wrong
function parseAge(s: string): number { return parseInt(s) || 0; }

// ✅ fail fast — caller is informed of the problem
function parseAge(s: string): number {
  const n = parseInt(s, 10);
  if (isNaN(n)) throw new TypeError(`Invalid age: "${s}"`);
  return n;
}
```

---

#### Composition over Inheritance

Favour assembling behaviour from small, focused objects (composition) over deep inheritance hierarchies.

- Inheritance creates tight coupling between parent and child classes
- Composition allows behaviour to be mixed in, swapped, or reused across unrelated classes
- Use inheritance only when a genuine **is-a** relationship exists; use composition for **has-a**

```ts
// ❌ fragile inheritance hierarchy
class Animal { breathe() {} }
class FlyingAnimal extends Animal { fly() {} }
class SwimmingAnimal extends Animal { swim() {} }
// What about a duck? It both flies and swims — multiple inheritance problem.

// ✅ compose capabilities
const canFly   = { fly:  () => console.log('flying') };
const canSwim  = { swim: () => console.log('swimming') };
const duck = Object.assign({ name: 'Duck' }, canFly, canSwim);
duck.fly(); duck.swim();
```

### Refactoring Techniques

Improve internal structure without changing external behaviour:

| Skill | Purpose |
|-------|---------|
| [`extract-method`](extract-method/SKILL.md) | Pull fragment into a named method |
| [`inline-method`](inline-method/SKILL.md) | Replace trivial delegation with direct body |
| [`extract-variable`](extract-variable/SKILL.md) | Name a complex expression |
| [`replace-temp-with-query`](replace-temp-with-query/SKILL.md) | Replace temp variable with method call |
| [`replace-magic-number`](replace-magic-number/SKILL.md) | Replace literal with named constant |
| [`decompose-conditional`](decompose-conditional/SKILL.md) | Extract condition/branches into methods |
| [`guard-clauses`](guard-clauses/SKILL.md) | Eliminate nesting with early returns |
| [`replace-conditional-polymorphism`](replace-conditional-polymorphism/SKILL.md) | Replace type-switches with polymorphism |
| [`extract-class`](extract-class/SKILL.md) | Split a class with too many responsibilities |
| [`move-method`](move-method/SKILL.md) | Move method to the class that uses it most |
| [`introduce-parameter-object`](introduce-parameter-object/SKILL.md) | Replace parameter group with object |
| [`separate-query-from-modifier`](separate-query-from-modifier/SKILL.md) | Split read/write methods |

### Design Patterns

**Creational** — object creation mechanisms:

| Skill | Purpose |
|-------|---------|
| [`singleton`](singleton/SKILL.md) | One shared instance |
| [`factory-method`](factory-method/SKILL.md) | Subclass decides which class to instantiate |
| [`abstract-factory`](abstract-factory/SKILL.md) | Families of related objects |
| [`builder`](builder/SKILL.md) | Step-by-step complex object construction |
| [`prototype`](prototype/SKILL.md) | Clone existing objects |

**Structural** — compose objects into larger structures:

| Skill | Purpose |
|-------|---------|
| [`adapter`](adapter/SKILL.md) | Convert incompatible interfaces |
| [`bridge`](bridge/SKILL.md) | Decouple abstraction from implementation |
| [`composite`](composite/SKILL.md) | Tree of uniform single/container objects |
| [`decorator`](decorator/SKILL.md) | Wrap to add behaviour dynamically |
| [`facade`](facade/SKILL.md) | Simple interface to a complex subsystem |
| [`flyweight`](flyweight/SKILL.md) | Share state among many fine-grained objects |
| [`proxy`](proxy/SKILL.md) | Controlled access to another object |

**Behavioral** — communication between objects:

| Skill | Purpose |
|-------|---------|
| [`chain-of-responsibility`](chain-of-responsibility/SKILL.md) | Pass request along a handler chain |
| [`command`](command/SKILL.md) | Encapsulate request as an object |
| [`iterator`](iterator/SKILL.md) | Traverse collection without exposing structure |
| [`mediator`](mediator/SKILL.md) | Centralise cross-object communication |
| [`memento`](memento/SKILL.md) | Save and restore object state |
| [`observer`](observer/SKILL.md) | Notify dependents of state changes |
| [`state`](state/SKILL.md) | Alter behaviour when internal state changes |
| [`strategy`](strategy/SKILL.md) | Swap interchangeable algorithms at runtime |
| [`template-method`](template-method/SKILL.md) | Define algorithm skeleton; subclasses fill steps |
| [`visitor`](visitor/SKILL.md) | Separate algorithm from object structure |

### Principles

- **Refactor before adding features** — clean code is easier to extend
- **Small, safe steps** — run tests after each refactoring
- **Apply patterns to solve problems, not to show off** — prefer simplicity; use patterns when they reduce coupling or duplication
- **Boy Scout Rule** — leave code cleaner than you found it
- **Principle of Least Surprise** — code should behave as a reasonable reader would expect

## References

- [Refactoring Guru — Refactoring](https://refactoring.guru/refactoring)
- [Refactoring Guru — Design Patterns](https://refactoring.guru/design-patterns)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [The Pragmatic Programmer — DRY](https://www.amazon.com/Pragmatic-Programmer-journey-mastery-Anniversary/dp/0135957052)
- [Refactoring by Martin Fowler](https://martinfowler.com/books/refactoring.html)
- [Design Patterns (GoF)](https://www.amazon.com/Design-Patterns-Elements-Reusable-Object-Oriented/dp/0201633612)
- [Law of Demeter](https://en.wikipedia.org/wiki/Law_of_Demeter)
- [Command-Query Separation (Martin Fowler)](https://martinfowler.com/bliki/CommandQuerySeparation.html)
