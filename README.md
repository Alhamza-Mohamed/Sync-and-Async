# Asynchronous Programming

A structured learning repository documenting my journey into asynchronous programming with Python, with a focus on understanding how concurrency works and how to apply it in real-world applications.

The goal of this repository is not simply to learn `async` and `await`, but to develop a deeper understanding of the execution model behind asynchronous programming, its underlying mechanisms, its limitations, and the design decisions involved in building reliable concurrent systems.

## Learning Objectives

The material covers the fundamental concepts and practical tools needed to understand asynchronous programming in Python:

- **Execution Models:** Synchronous vs. asynchronous execution, concurrency vs. parallelism, and I/O-bound vs. CPU-bound workloads.
- **Python Concurrency:** Processes, threads, coroutines, tasks, and the event loop.
- **Asyncio Fundamentals:** `async`, `await`, task creation, task scheduling, and coroutine execution.
- **Task Coordination:** `asyncio.gather()`, `asyncio.TaskGroup`, events, locks, and semaphores.
- **Timeouts and Cancellation:** Managing task lifecycles, handling cancellation, and implementing reliable cleanup.
- **Asynchronous Iteration and Streaming:** Async iterators, async generators, and streaming architectures.
- **Producer–Consumer Architecture:** Queues, buffering, backpressure, and failure coordination.
- **Performance and Resource Management:** Thread pools, process pools, `asyncio.to_thread()`, concurrency limits, and dynamic task scheduling.
- **Reliability:** Graceful shutdown, resource cleanup, task supervision, and failure handling.

## Repository Contents

| File | Description |
|---|---|
| `Asynchronous Programming - Complete Notes.md` | Detailed notes covering the concepts, explanations, examples, and technical observations from the course. |
| `Asynchronous Programming - Quick Reference.md` | A condensed version of the notes for quick revision and reference. |
| `Synchronous vs Asynchronous Execution.ipynb` | Practical code examples and experiments exploring synchronous and asynchronous execution. |

## Learning Approach

I approached the subject by combining conceptual learning with practical experiments.

Rather than treating asynchronous programming as a collection of syntax and APIs, I focused on understanding:

- What happens behind the scenes when a coroutine is awaited.
- How the event loop schedules and manages tasks.
- Why concurrency does not necessarily mean parallel execution.
- How tasks behave when they encounter failures, timeouts, or cancellation.
- How to coordinate concurrent operations without introducing unnecessary complexity.
- How these concepts translate into reliable application architectures.

The notes and code examples reflect this process, including observations, experiments, and technical explanations.

## Why This Matters

Asynchronous programming is particularly relevant to backend development and AI engineering, where applications frequently interact with external APIs, databases, and other I/O-bound services.

Understanding these mechanisms is essential when working with systems that involve concurrent requests, LLM API calls, streaming responses, and resource-intensive workloads.

## Technologies

- Python
- `asyncio`
- `threading`
- `multiprocessing`
- Jupyter Notebook

---

**This repository is a learning resource and a reference for my continued work in Python, backend engineering, and AI systems.**

[GitHub Repository](https://github.com/Alhamza-Mohamed/asynchronous-programming)
