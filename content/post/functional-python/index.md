---
title: "Functions Over Classes? Why I Prefer a Simpler, Functional Style in Python 🐍"
subtitle: Embracing small functions and data classes for clarity, testability, and reduced cognitive load in software development.
summary: Exploring my preference for a functional programming style in Python, utilizing small, focused functions and simple data-holding classes while largely avoiding inheritance, leading to more maintainable and testable code, while still using classes where they make sense for APIs.
projects: []
date: "2025-04-14T00:00:00Z"
draft: false
featured: false

authors:
  - admin

tags:
  - python
  - programming
  - functional-programming
  - software-design
  - code-quality
  - testing
  - maintainability
  - unidep
  - pipefunc

categories:
  - development
  - philosophy
  - level:intermediate
---

Over years of building software, from scientific simulation tools like [`Adaptive`](https://github.com/python-adaptive/adaptive) and [`pipefunc`](https://github.com/pipefunc/pipefunc) to package management packages like [`unidep`](https://github.com/basnijholt/unidep), I've found myself preferring a certain coding style: using small, focused functions more than large classes with complex internal state and deep inheritance hierarchies.
This isn't about dogma, but about a pragmatic approach that, in my experience, leads to code that is easier to understand, test, and maintain.

This post outlines why I lean towards this functional-inspired style in my Python projects, while still recognizing where classes are the right tool.

{{< toc >}}

## 1. Taming Complexity: Avoiding the Over-Engineering Trap 🧠

One of the biggest challenges in software development is managing complexity.
As systems grow, keeping track of how different parts interact and understanding the internal state of objects can become a lot to keep track of mentally (high cognitive load).

I've often observed a pattern, especially when developers first start using object-oriented programming: the tendency to use classes *everywhere*.
This can lead to over-engineering – introducing many layers of inheritance, abstract base classes with only a single implementation, and generally creating complexity when simplicity would suffice.
Thinking you're being clever by building complex class structures can sometimes just be a form of overgeneralization that makes the code harder, not easier, to follow.

Classes, particularly those with many methods modifying internal attributes (`self.x`, `self.y`, etc.), require you to constantly hold their state in your head.
When you call a method `object.do_something()`, the outcome might depend not just on the arguments you pass, but also on the object's history – what methods were called before, and in what order?
This hidden state can make reasoning about the code's behavior difficult and debugging tricky.

Functions, particularly when kept small and focused, tend to be more explicit.
Ideally, a function takes inputs and produces outputs, with minimal side effects (or ideally, none - making them pure functions).
Its behavior is primarily determined by its arguments.
This makes the code flow easier to follow: data comes in, transformation happens, data goes out.
There's less hidden context to juggle mentally.

## 2. The Power of Small, Focused Functions 🎯

This leads directly to the preference for small functions, each doing one thing well (adhering to the Single Responsibility Principle).
When functions are concise and have a clear purpose:

-   **Readability Improves:** It's easier to understand what a small, well-named function does quickly.
-   **Reusability Increases:** Small, focused functions are more likely to be reusable in different parts of the codebase or even in other projects.
-   **Refactoring is Simpler:** Modifying or replacing a small unit of logic is less risky than altering a large, complex method within a class.

This philosophy is something I actively apply.
Looking at the codebase for [`unidep`](https://github.com/basnijholt/unidep), for example, you'll find many utility functions in modules like `_dependencies_parsing.py` or `_conda_env.py`, each handling a specific, well-defined task.

## 3. Keeping Classes Simple & Using Them Where They Fit 🛠️

So, where do classes fit in this picture?

Firstly, as **simple data structures** – think `NamedTuple`s or `dataclasses` (preferably with `frozen=True`).
Their main role is to group related data attributes together, providing a clear structure for passing information around.
They hold data, but don't typically manage complex state transitions.

```python
# Example of a simple data class from unidep
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True) # Use frozen=True for immutability
class Spec:
    name: str
    which: Literal["conda", "pip"]
    pin: str | None = None
    # ... other simple attributes ...

# Used to pass structured data, not to manage complex state
def process_spec(spec: Spec) -> Path:
    # ... function logic using spec data ...
    pass
```

Secondly, and importantly, classes are excellent for **defining user-facing APIs**.
For the end-user of a library, having a single object with easily discoverable methods (`object.<tab>`) is often a great user experience.

A good example from my own work is the [`pipefunc`](https://github.com/pipefunc/pipefunc) package.
It provides two main classes, `Pipeline` and `PipeFunc`, which encapsulate the core functionality.
Users interact primarily with these objects and their methods.

```python
# Simplified example from pipefunc's user perspective
from pipefunc import Pipeline

pipeline = Pipeline(...)
pipeline.add(some_function, ...)
results = pipeline.run("output_node")
```

However, **inside** the methods of these API classes (`Pipeline.run`, `Pipeline.add`, etc.), the actual logic is often delegated to smaller, internal functions.
The class acts as a clean interface or facade, orchestrating calls to these more focused, functional units.
This gives the user a nice API while keeping the internal implementation modular and testable.

I also actively avoid deep inheritance hierarchies.
Composition (having objects contain other objects) often provides a more flexible and explicit way to combine functionality without the tight coupling and complexity inheritance can introduce.

## 4. The Testability Advantage ✅

One of the most significant practical benefits of prioritizing functions and simple classes is testability.
Small, pure (or mostly pure) functions are incredibly easy to test:

-   Provide known inputs.
-   Assert expected outputs.
-   Minimal setup or mocking is required because there's no complex internal state to manage.

Even when testing the methods of the API classes (like `Pipeline` in `pipefunc`), the fact that they often delegate to well-tested internal functions simplifies the process.
You focus on testing the orchestration and interaction logic at the class level, knowing the underlying functional units are already verified.

Testing classes with intricate internal state inherently involves more setup (instantiating the object, getting it into the right state before calling the method under test) and potentially more complex assertions to verify state changes.
Aiming for more functional units significantly simplifies the testing process.

## 5. It's About Pragmatism, Not Dogma 🙏

This isn't a wholesale rejection of object-oriented programming.
It's about choosing the right tool for the job and prioritizing clarity, testability, and maintainability.
Classes are fantastic tools, especially for building clear APIs and structuring data.
Deep inheritance and complex state management, however, should be used carefully, not just because the language allows it.

For much of the work I do – building libraries, tools, and performing data analysis or simulations – I've found that prioritizing functions, keeping API classes focused, minimizing internal state, and avoiding deep inheritance leads to code that *I* find easier to write, understand, debug, and maintain in the long run.
The reduction in cognitive load and the ease of testing are strong points for how I work.

If you often find yourself struggling with complex state management or tangled inheritance trees, perhaps consider if a simpler, more functional internal structure, potentially fronted by a clean class-based API, might bring some clarity and simplicity to your projects too.
