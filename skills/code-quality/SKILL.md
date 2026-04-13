---
name: code-quality
description: Code quality mastery — refactoring techniques and design patterns to write clean, maintainable, extensible software.
license: MIT
metadata:
  author: Satcomx00-x00
  version: 1.0.0
---

# code-quality

Code quality mastery — refactoring techniques and design patterns to write clean, maintainable, extensible software.

## Instructions

Apply code quality practices to continuously improve codebases:

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

## References

- [Refactoring Guru — Refactoring](https://refactoring.guru/refactoring)
- [Refactoring Guru — Design Patterns](https://refactoring.guru/design-patterns)
- [Refactoring by Martin Fowler](https://martinfowler.com/books/refactoring.html)
- [Design Patterns (GoF)](https://www.amazon.com/Design-Patterns-Elements-Reusable-Object-Oriented/dp/0201633612)
