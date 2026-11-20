# Python Async for AI Engineers — Concise Learning Notes

These notes summarize the core concepts, behavior, and architectural lessons from the course. They are intended for quick revision and as a shareable overview, rather than a replacement for the full learning notebook.

## Table of contents

- [Python Async for AI Engineers — Concise Learning Notes](#python-async-for-ai-engineers--concise-learning-notes)
  - [Table of contents](#table-of-contents)
  - [Sync and Async](#sync-and-async)
    - [Why Async exists](#why-async-exists)
    - [CPU-bound vs. I/O-bound](#cpu-bound-vs-io-bound)
    - [Concurrency and parallelism](#concurrency-and-parallelism)
    - [Processes, threads, tasks, and coroutines](#processes-threads-tasks-and-coroutines)
  - [The Event Loop](#the-event-loop)
  - [Async in Python](#async-in-python)
    - [Coroutine functions, coroutine objects, and tasks](#coroutine-functions-coroutine-objects-and-tasks)
    - [`asyncio.run()` and Jupyter](#asynciorun-and-jupyter)
    - [Awaitables](#awaitables)
    - [`await` vs. `asyncio.create_task()`](#await-vs-asynciocreate_task)
    - [`asyncio.gather()`](#asynciogather)
    - [Structured concurrency with `asyncio.TaskGroup`](#structured-concurrency-with-asynciotaskgroup)
  - [Async Coordination and Debugging](#async-coordination-and-debugging)
    - [Events](#events)
    - [Task inspection and debugging](#task-inspection-and-debugging)
    - [Timeouts](#timeouts)
  - [Async Generators, Streaming, Queues, and Backpressure](#async-generators-streaming-queues-and-backpressure)
    - [Coroutines vs. async generators](#coroutines-vs-async-generators)
    - [Streaming](#streaming)
    - [Buffering and backpressure](#buffering-and-backpressure)
    - [Queue task accounting](#queue-task-accounting)
    - [Producer–consumer failure coordination](#producerconsumer-failure-coordination)
    - [Durability and message brokers](#durability-and-message-brokers)
  - [Context Managers and Resource Lifecycles](#context-managers-and-resource-lifecycles)
  - [#Synchronous context managers](#synchronous-context-managers)
    - [Async context managers](#async-context-managers)
    - [Synchronizing tasks with `asyncio.Lock`](#synchronizing-tasks-with-asynciolock)
  - [Common Async Mistakes](#common-async-mistakes)
    - [Blocking the event loop accidentally](#blocking-the-event-loop-accidentally)
    - [Creating tasks without managing them](#creating-tasks-without-managing-them)
    - [Losing track of task exceptions](#losing-track-of-task-exceptions)
    - [Forgetting to await a coroutine](#forgetting-to-await-a-coroutine)
    - [Understanding `gather()` failure and cancellation](#understanding-gather-failure-and-cancellation)
  - [Performance and Appropriate Concurrency](#performance-and-appropriate-concurrency)
    - [I/O concurrency](#io-concurrency)
    - [Controlling concurrency and memory](#controlling-concurrency-and-memory)
    - [Concurrency limits and performance measurements](#concurrency-limits-and-performance-measurements)
    - [CPU-bound work and process pools](#cpu-bound-work-and-process-pools)
    - [Combining asynchronous I/O and CPU processing](#combining-asynchronous-io-and-cpu-processing)
    - [Completion order with `asyncio.as_completed()`](#completion-order-with-asyncioas_completed)
  - [Running blocking synchronous functions with `asyncio.to_thread()`](#running-blocking-synchronous-functions-with-asyncioto_thread)
    - [Dynamic scheduling and load balancing](#dynamic-scheduling-and-load-balancing)
    - [Bounded pipeline architecture](#bounded-pipeline-architecture)
  - [Reliability and Failure Coordination](#reliability-and-failure-coordination)
    - [Failure levels in a worker pipeline](#failure-levels-in-a-worker-pipeline)
    - [Executor job lifetime and cancellation](#executor-job-lifetime-and-cancellation)
    - [Graceful shutdown](#graceful-shutdown)
    - [Cancellation and resource cleanup](#cancellation-and-resource-cleanup)
    - [Supervision and final architecture](#supervision-and-final-architecture)
  - [Final Mental Model](#final-mental-model)

## Sync and Async

### Why Async exists

**Synchronous execution:** Operations happen one after another. Each operation must finish before the next one starts.

**Asynchronous execution:** An operation can be started and suspended while waiting, allowing other work to make progress before that operation finishes.

A blocking operation prevents the program from making progress until it completes. For example, while waiting for an HTTP response, Python is often not doing useful computation; it is waiting for something outside the process.

Common I/O operations include HTTP requests and LLM API calls, database and vector database queries, file and cloud storage operations, and communication with Redis or another microservice.

Async is especially valuable when operations spend significant time waiting for external resources.

### CPU-bound vs. I/O-bound

**CPU-bound work** spends most of its time actively using the processor.

Examples include matrix multiplication and large numerical computations, image processing and video encoding, model training, and other heavy calculations.

**I/O-bound work** spends most of its elapsed time waiting for input or output.

Examples include HTTP requests, database queries, reading and writing files, and calling an LLM API.

Async concurrency is particularly useful for I/O-bound workloads. It does not automatically make CPU-heavy work execute faster.

### Concurrency and parallelism

**Concurrency** is the ability of a system to make progress on multiple tasks during overlapping periods of time. Tasks may take turns executing while other tasks wait.

**Cooperative concurrency:** A running task yields control so another task can execute. In asyncio, tasks commonly yield at `await` points.

- Efficient for suitable I/O-heavy workloads.
- A task that does not yield can block other tasks on the same event-loop thread.
- The event loop does not forcibly interrupt a running coroutine.

**Preemptive concurrency:** The operating system can interrupt a running thread and schedule another one.

- A thread does not need to voluntarily yield for the operating system to schedule something else.
- Context switching and shared-state coordination introduce overhead and complexity.

**Parallelism** means multiple pieces of work are actually executing simultaneously, typically on different CPU cores.

Concurrency and parallelism are related, but they are not the same thing.

### Processes, threads, tasks, and coroutines

**Process:** An isolated running instance of a program, with its own memory space and operating-system resources. Separate processes do not normally share ordinary Python variables.

**Thread:** An execution context inside a process. Threads in the same process share memory and resources, so concurrent access to shared state can create race conditions.

**Coroutine:** A function-like computation that can suspend and later resume from where it stopped.

**Task:** A coroutine scheduled to run with an independent lifecycle managed by the async runtime.

A useful mental model:

```text
Process
  └── Threads
        └── Event loop (on an event-loop thread)
              └── Async tasks
                    └── Coroutines being executed
```

A thread is an execution context; a task is a unit of work. Many asyncio tasks can share one event-loop thread.

Threads are useful for blocking libraries and certain workloads. Async is attractive when many I/O-bound operations need to share a small number of execution threads. Processes are useful when CPU-bound Python work needs process-level parallelism.

## The Event Loop

The event loop manages and schedules asynchronous tasks.

A task runs until it reaches an operation where it cannot make progress and suspends. The event loop can then schedule another ready task. When the awaited operation becomes ready, the suspended task can resume.

A task can be:

- **Running:** currently executing.
- **Waiting/suspended:** waiting for an operation or event.
- **Ready:** able to continue when scheduled.
- **Complete:** returned a result, raised an exception, or finished through cancellation.

The event loop does not forcibly interrupt a running task. Cooperative scheduling depends on tasks yielding control.

The CPU executes instructions. The thread provides the execution context. The event loop manages which async task gets an opportunity to execute.

## Async in Python

### Coroutine functions, coroutine objects, and tasks

```python
async def fetch_data():
    return "data"
```

Defining an `async def` function creates a coroutine function. Calling it creates a coroutine object; it does not execute the body immediately.

```python
coro = fetch_data()
```

The coroutine must be awaited or scheduled to execute.

```python
result = await fetch_data()
```

`await` runs/continues the awaitable as part of the current task and suspends the current task until a result or exception is available.

```python
task = asyncio.create_task(fetch_data())
```

`asyncio.create_task()` schedules a coroutine as an independent task on the event loop. It does not create a thread.

**Important distinction:** `await` does not automatically create a new task. It waits within the current task. `create_task()` gives the coroutine an independent scheduled task lifecycle.

### `asyncio.run()` and Jupyter

`asyncio.run(main())` is the normal entry point for an async program. It creates and manages an event loop, runs the main coroutine, performs shutdown handling, and closes the loop.

Jupyter already has a running event loop, so you can usually write:

```python
await main()
```

Calling `asyncio.run()` inside an already-running event loop raises a `RuntimeError`.

### Awaitables

An **awaitable** is an object that can be used with `await`.

Common awaitables include coroutine objects, tasks, and futures.

A Future represents a result that will become available later. A Task is an awaitable that schedules and manages a coroutine's execution.

### `await` vs. `asyncio.create_task()`

Sequential execution:

```python
users = await get_users()
products = await get_products()
```

The current task waits for `get_users()` to finish before it starts `get_products()`.

Concurrent execution:

```python
users_task = asyncio.create_task(get_users())
products_task = asyncio.create_task(get_products())

users = await users_task
products = await products_task
```

Both operations are scheduled before the current task waits for their results. They can make progress concurrently.

`await` suspends the current task when the awaited operation is not ready. The event loop can then run other ready tasks. There must be other scheduled work for the event loop to run.

### `asyncio.gather()`

`asyncio.gather()` runs multiple awaitables concurrently and waits for all of them on successful completion.

```python
results = await asyncio.gather(
    fetch_user(),
    fetch_products(),
    fetch_orders()
)
```

The event loop decides when each task executes or resumes. `gather()` coordinates the awaitables and returns results in the order they were supplied, not completion order.

By default, if one awaitable raises an ordinary exception, `gather()` propagates the first exception to its caller. It does **not** automatically cancel the other submitted awaitables; they may continue running.

With `return_exceptions=True`, exceptions are returned as result entries so the caller can inspect partial failures.

Cancellation distinctions:

- Cancelling one child does not automatically cancel its siblings.
- A child raising an ordinary exception does not automatically cancel its siblings.
- Cancelling the `gather()` operation itself cancels its unfinished submitted awaitables.

### Structured concurrency with `asyncio.TaskGroup`

Structured concurrency means concurrent tasks belong to a defined scope, and that scope manages their lifecycle.

```python
async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(work_a())
        tg.create_task(work_b())

    print("Both tasks completed")
```

The TaskGroup waits for its child tasks before leaving the `async with` block. The parent does not continue past the block until the group has finished.

If a child raises an exception other than `CancelledError`, the TaskGroup cancels its remaining child tasks and waits for their cancellation and cleanup before propagating the failure.

If multiple children fail, TaskGroup can raise an `ExceptionGroup`, which contains multiple exceptions.

- `except` handles an exception that matches the raised exception type.
- `except*` handles matching exceptions inside an exception group.

```python
try:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(work_a())
        tg.create_task(work_b())
except* ValueError as group:
    print("Handled ValueError exceptions")
```

A `finally` block still executes during cancellation. It performs cleanup, but it does not by itself suppress the cancellation.

**TaskGroup vs. gather:**

- Both can coordinate multiple concurrent awaitables.
- TaskGroup provides a defined scope for task ownership and lifecycle management.
- A child failure in TaskGroup cancels the remaining children and waits for them.
- By default, `gather()` propagates the first failure without automatically cancelling the other children.

Use TaskGroup when related tasks belong to one operation and should be managed together.

## Async Coordination and Debugging

### Events

`asyncio.Event()` lets one coroutine signal to other coroutines that something has happened. It behaves like a shared flag.

- `event.set()` sets the flag and wakes coroutines waiting for it.
- `event.clear()` resets the flag.
- `await event.wait()` suspends until the flag is set.

### Task inspection and debugging

Useful task methods:

- `task.done()`: whether the task has finished, regardless of outcome.
- `task.cancelled()`: whether it finished through cancellation.
- `task.exception()`: retrieves the exception from a completed task, or returns `None` if it completed without one.
- `task.result()`: retrieves the result; raises the stored exception if the task failed.
- `task.get_coro()`: returns the coroutine associated with the task.
- `task.get_stack()`: provides Python frames showing where a suspended task is paused.
- `task.print_stack()`: prints a formatted stack trace.

`get_stack()` is an inspection tool. It does not resume, pause, or cancel a task. It shows Python execution frames, not necessarily the external reason a task is waiting.

### Timeouts

`asyncio.wait_for()` applies a timeout to an awaitable:

```python
await asyncio.wait_for(slow_operation(), timeout=2)
```

`asyncio.timeout()` establishes a timeout boundary around a block:

```python
async with asyncio.timeout(2):
    await operation_a()
    await operation_b()
```

The timeout applies to the whole block. If several operations run sequentially inside it, their combined elapsed time must fit within the deadline. If independent operations run concurrently with `gather()`, the overall time is determined by the slowest required operation, subject to the deadline.

When a timeout expires, asyncio uses cancellation to stop the awaited work. The caller normally receives `TimeoutError` after the cancellation process completes.

`task.cancel()` is a cancellation request, not an immediate forced termination. `CancelledError` is delivered to the coroutine at a cancellation opportunity. A coroutine can perform cleanup and then allow cancellation to propagate.

If a coroutine catches `CancelledError` and does not re-raise it, it may suppress cancellation. Usually, cancellation should be allowed to propagate after required cleanup.

## Async Generators, Streaming, Queues, and Backpressure

### Coroutines vs. async generators

A coroutine is awaited to obtain a result.

```python
async def get_data():
    return "hello"
```

An async generator can produce multiple values over time.

```python
async def numbers():
    yield 1
    yield 2
    yield 3
```

`yield` produces a value and suspends the generator until the consumer requests the next value. An async generator is commonly consumed with `async for`.

An async generator produces the next value when the consumer requests it. If the consumer suspends after receiving a value, the generator remains suspended until the next request.

### Streaming

Streaming means receiving or producing data progressively instead of waiting for the entire result.

Streaming describes how data is delivered. Async describes how the program handles waiting and concurrency. Streaming can exist without asyncio, and async code does not have to be streaming.

With pull-based streaming, the consumer requests each next item:

```python
async for chunk in stream():
    await process(chunk)
```

The consumer controls the pace. The generator does not independently keep producing values in the background while the consumer is processing the current one.

With push-based streaming, an external source delivers events as they become available, for example through a callback or queue. Push-based and pull-based describe delivery patterns, not whether code is synchronous or asynchronous.

### Buffering and backpressure

**Buffering** temporarily stores produced data so producer and consumer do not have to operate at exactly the same time.

**Backpressure** occurs when the buffer reaches its limit and the producer must slow down or wait because the consumer cannot keep up.

A bounded `asyncio.Queue` can provide this behavior:

```python
queue = asyncio.Queue(maxsize=100)

await queue.put(item)  # waits if the queue is full
item = await queue.get()
```

When the queue is full, `await queue.put()` suspends the producer until space becomes available. The event loop remains free to schedule other tasks.

If production is permanently faster than consumption:
- An unbounded buffer can grow until memory becomes a problem.
- A bounded buffer with backpressure slows the producer, if the source can be slowed down.
- Dropping data may be acceptable when only the latest value matters.
- If every event must be preserved and the source cannot pause, durable storage or a message broker may be needed, along with enough processing capacity.

Backpressure does not make the throughput mismatch disappear. It controls where the backlog accumulates and prevents unlimited in-memory growth.

### Queue task accounting

`asyncio.Queue` tracks unfinished work:

- Each successful `queue.put(item)` increments the unfinished-task count.
- `queue.get()` removes an item from the queue, but does not mark its processing as complete.
- `queue.task_done()` decrements the unfinished-task count after processing has been accounted for.
- `queue.join()` waits until the unfinished-task count reaches zero.

Retrieving an item is not the same as finishing its processing.

### Producer–consumer failure coordination

A producer and consumer running as independent tasks do not automatically manage each other's lifecycle.

If a consumer fails while the producer is filling a bounded queue:
1. The producer may continue producing.
2. The queue may become full.
3. The producer can remain suspended waiting for queue space.
4. If no consumer remains to remove items, the pipeline may stop making progress.

The application needs an explicit failure-coordination strategy: detect which task finished, inspect its outcome, cancel related work when appropriate, await cancellation, and allow resource cleanup to run.

`asyncio.wait(..., return_when=asyncio.FIRST_COMPLETED)` can help detect when one of several tasks finishes. It returns `done` and `pending` task sets. A task in `done` may have completed successfully or with an exception.

### Durability and message brokers

An in-memory `asyncio.Queue` does not survive process termination. If messages must survive application crashes or restarts, they need to be stored outside process memory.

A message broker such as RabbitMQ or Kafka can decouple producers and consumers and provide configurable message retention and delivery behavior.

Important concepts:
- **Durability:** data survives specified failures.
- **Acknowledgement (ACK):** tells the broker that a message has been handled.
- **Idempotency:** prevents repeated delivery or requests from causing repeated effects.

A broker does not automatically guarantee preservation under every failure. Durability, replication, and acknowledgement configuration matter. A consumer may also process a message and crash before acknowledging it, causing redelivery.

## Context Managers and Resource Lifecycles

## #Synchronous context managers

A context manager manages a resource lifecycle: enter/setup, use, and exit/cleanup.

```python
with open("data.txt") as file:
    data = file.read()
```

The `with` statement ensures the context manager's exit behavior is invoked when the block ends, including when an exception occurs.

The context manager protocol uses:

- `__enter__()` for setup/acquisition.
- `__exit__(exc_type, exc_value, traceback)` for cleanup/exit behavior.

If an exception occurs inside the block, Python passes its type, exception object, and traceback to `__exit__()`. Returning `True` from `__exit__()` suppresses that exception; otherwise it propagates.

Context managers are useful for files, database connections, locks, network resources, and other resources that must be released reliably.

### Async context managers

Some resource setup and cleanup operations may involve waiting. An ordinary `__enter__()` or `__exit__()` is synchronous and cannot use `await`.

An asynchronous context manager uses:
- `async def __aenter__()`
- `async def __aexit__(exc_type, exc_value, traceback)`

```python
async with client:
    response = await client.get("/users")
```

Python awaits the asynchronous enter and exit operations. They may suspend, allowing the event loop to run other ready tasks.

`async with` manages the resource lifecycle; it does not make every operation inside the block asynchronous. The body still needs its own asynchronous operations, such as `await`, to suspend.

The resource remains available for the lifetime of the context. A task being suspended does not automatically close or release the resource.

### Synchronizing tasks with `asyncio.Lock`

When multiple coroutines access shared mutable state, their operations can interfere if a coroutine suspends between reading and writing the shared value.

A critical section is the part of the code that must be protected from concurrent access by other tasks using the same lock.

```python
lock = asyncio.Lock()

async def update_shared_state():
    async with lock:
        # access or modify shared state
        ...
```

Only one coroutine at a time can hold an `asyncio.Lock`. Other coroutines attempting to acquire it wait until it is released.

`async with lock` handles acquisition and release, including when an exception occurs. Keep the critical section as small as possible; do not hold the lock across unnecessary operations.

## Common Async Mistakes

### Blocking the event loop accidentally

Declaring a function with `async def` does not make synchronous code inside it non-blocking.

```python
async def fetch_data():
    time.sleep(2)  # blocks the event-loop thread
```

`time.sleep()` blocks the thread running the event loop. Other tasks on that loop cannot run during that time.

Use an asynchronous operation such as `await asyncio.sleep(2)` when an async wait is intended. For blocking synchronous functions, consider offloading them to a thread.

### Creating tasks without managing them

`asyncio.create_task()` schedules work, but does not guarantee that it will finish before the creating coroutine or event loop ends.

If the operation is essential, await it or manage it with a TaskGroup. If it runs in the background, its lifecycle and exceptions still need to be observed and managed.

A task can outlive the coroutine that created it, but it is not guaranteed to outlive the event loop.

### Losing track of task exceptions

A background task's exception does not automatically propagate into the coroutine that created it if that coroutine never awaits the task or retrieves its exception.

Use `await task`, inspect a completed task's exception, or manage related tasks with a structured approach. Otherwise, asyncio may report that a task exception was never retrieved.

### Forgetting to await a coroutine

Calling an async function creates a coroutine object:

```python
result = fetch_data()  # coroutine object, not the result
```

To execute it as part of the current task:

```python
result = await fetch_data()
```

Or schedule it independently:

```python
task = asyncio.create_task(fetch_data())
```

Creating a task and awaiting it are separate decisions. A task can run while the current task does other work, and its result or exception can be retrieved later by awaiting it.

### Understanding `gather()` failure and cancellation

Do not assume that `gather()` cancels every other operation when one child fails.

- A child raises an ordinary exception: the first exception is propagated by default; other children are not automatically cancelled.
- A child is cancelled: `CancelledError` is propagated to the awaiter; other children are not automatically cancelled.
- `return_exceptions=True`: exceptions and child cancellations are returned as result entries.
- The `gather()` operation itself is cancelled: its unfinished children are cancelled.

## Performance and Appropriate Concurrency

### I/O concurrency

When independent operations spend most of their time waiting for I/O, concurrency allows their waiting periods to overlap.

For three independent operations that each take about two seconds:

- Sequential execution takes approximately six seconds.
- Concurrent execution can take approximately two seconds, assuming similar conditions and no additional bottleneck.

On a typical asyncio event loop, Python code for tasks runs one task at a time on the event-loop thread. Their waiting periods overlap; their Python instructions are not executing simultaneously on that same thread.

### Controlling concurrency and memory

Creating thousands of tasks immediately can consume memory and overwhelm an external service.

Different mechanisms control different parts of the workload:

- `asyncio.Semaphore(N)` limits how many coroutines can enter a protected section concurrently.
- A fixed worker pool limits how many worker tasks exist.
- `asyncio.Queue(maxsize=N)` limits how many items can wait in the queue and provides backpressure.

```python
semaphore = asyncio.Semaphore(100)

async def limited_fetch(document):
    async with semaphore:
        return await fetch(document)
```

Limiting active requests and limiting task creation are separate concerns.

A semaphore initialized with `1` permits one coroutine at a time, behaving similarly to a lock for access control.

- **Lock:** provides exclusive access to a shared resource.
- **Semaphore:** controls how many coroutines may access a resource or enter a section simultaneously.

Both can be used with `async with`.

### Concurrency limits and performance measurements

Important metrics:

- **Concurrency:** how many operations can be in progress at once.
- **Throughput:** how many operations complete per unit of time.
- **Latency:** how long an individual operation takes.

Increasing concurrency can improve throughput until a bottleneck appears. Beyond that point, more concurrency may consume resources, increase latency, and provide little benefit.

The slowest required dependency determines when a combined operation can proceed. Optional work may be handled separately, but background tasks still need lifecycle and exception management.

### CPU-bound work and process pools

Async concurrency overlaps waiting time. It does not automatically provide parallel execution for CPU-heavy Python code.

A process pool can execute CPU-bound functions in separate processes:

```python
loop = asyncio.get_running_loop()

result = await loop.run_in_executor(
    process_pool,
    process_document,
    document
)
```

`run_in_executor()` submits synchronous work to an executor. Awaiting the returned future suspends the current coroutine while the event loop remains available to run other tasks.

A `ProcessPoolExecutor` manages separate worker processes. It can allow CPU-bound Python work to run in parallel on multiple cores, but speedup is not guaranteed to scale perfectly because of process startup, data transfer, scheduling, contention, and uneven job durations.

### Combining asynchronous I/O and CPU processing

A common architecture uses:

1. Async I/O to download or retrieve documents concurrently.
2. A process pool to perform CPU-bound processing.
3. Async coordination to collect results and manage the pipeline.

The event loop coordinates I/O and submission/retrieval of CPU work, while the process pool performs the computation.

### Completion order with `asyncio.as_completed()`

`asyncio.gather()` returns results in the order the awaitables were supplied.

`asyncio.as_completed()` allows results to be handled in completion order. This is useful when operations have different durations and completed results should be processed without waiting for slower operations.

## Running blocking synchronous functions with `asyncio.to_thread()`

`asyncio.to_thread()` runs a synchronous function in a separate thread, allowing the event loop to continue running other coroutines.

```python
result = await asyncio.to_thread(blocking_function, arg1, arg2)
```

Pass the function reference, not the result of calling the function:

```python
# Correct
asyncio.to_thread(blocking_function)

# Incorrect: calls the function immediately on the current thread
asyncio.to_thread(blocking_function())
```

`to_thread()` is especially useful for blocking I/O functions. It does not turn the synchronous function into an async function. For ordinary Python CPU-bound code, the GIL generally limits CPU parallelism, although offloading can still protect event-loop responsiveness.

### Dynamic scheduling and load balancing

When jobs have different processing times, static assignment can leave some workers idle while others are still busy.

Dynamic scheduling allows available workers to take new jobs as they finish their current work. A shared work queue is one way to implement it. `ProcessPoolExecutor` also manages submitted jobs and distributes them among its worker processes.

The process pool schedules work to worker processes; the operating system schedules those processes onto CPU cores.

### Bounded pipeline architecture

A bounded pipeline controls pending work and submitted CPU jobs:

- A bounded queue limits waiting documents.
- A fixed number of asyncio workers limits orchestration concurrency.
- Each worker can submit a CPU job and await its result.
- The process-pool size limits how many CPU jobs can execute simultaneously.

The asyncio worker count and process-pool size are separate configuration decisions. More asyncio workers do not automatically increase CPU throughput when the process pool is already fully occupied; they may instead increase pending work and memory usage.

## Reliability and Failure Coordination

### Failure levels in a worker pipeline

- **Document-level failure:** One document fails, but the worker handles the exception and continues processing other documents.
- **Worker-level failure:** A worker itself terminates unexpectedly and can no longer process queue items.

Worker-level failure is more serious because it reduces the number of available consumers. If enough workers fail, the pipeline may stop making progress.

### Executor job lifetime and cancellation

Cancelling an asyncio task that is awaiting a process-pool job does not guarantee that an already-running process-pool function stops.

The asyncio coroutine can stop waiting, while the computation in the worker process continues until it finishes. Task cancellation and executor-job termination are separate lifecycle concerns.

### Graceful shutdown

Graceful shutdown means stopping a pipeline in an orderly way while allowing existing work to finish.

A common sequence:

```text
Stop producing new work
        ↓
Send one sentinel per worker
        ↓
Workers finish current work
        ↓
Workers consume sentinels and exit
        ↓
await queue.join()
        ↓
await worker tasks
        ↓
Shut down the process pool
```

A **sentinel** is a special queue value used as a control signal rather than actual work. If there are multiple workers, send one sentinel per worker.

Queue accounting must be handled correctly: each item retrieved with `queue.get()` needs a corresponding `queue.task_done()` once its processing has been accounted for.

### Cancellation and resource cleanup

`asyncio.CancelledError` inherits directly from `BaseException`, not `Exception`. Therefore, an ordinary `except Exception:` does not catch cancellation.

A `finally` block is commonly used for cleanup because it runs when a coroutine exits through normal completion, an exception, or cancellation.

Cleanup may itself involve `await`. A further cancellation can interrupt asynchronous cleanup, so important cleanup work needs deliberate supervision.

`asyncio.shield()` prevents cancellation of the outer task from propagating to the inner awaitable. It does not automatically make the outer coroutine wait for the inner operation to finish; the inner operation still needs lifecycle management.

### Supervision and final architecture

A supervisor is responsible for overseeing the execution and lifecycle of other components.

In a worker-based pipeline:

- **Producer:** downloads documents and submits them to the queue.
- **Queue:** distributes work and provides bounded buffering.
- **Workers:** retrieve documents and submit CPU-bound jobs to the process pool.
- **Process pool:** executes CPU-bound functions in separate processes.
- **Supervisor:** monitors tasks, detects failures, coordinates cancellation, and manages shutdown.

It is important to distinguish failure from cancellation:

- A worker failure is an unexpected error that requires the pipeline's failure policy.
- Cancellation may be an intentional part of shutdown.

A reliable concurrent pipeline needs more than concurrency. It needs controlled work submission, task ownership, failure detection, cancellation coordination, resource cleanup, and orderly shutdown.

## Final Mental Model

- **Async concurrency:** overlaps waiting time.
- **Parallelism:** executes computations simultaneously, typically on multiple CPU cores.
- **Event loop:** schedules and coordinates async tasks.
- **Task:** a scheduled unit of asynchronous work.
- **`await`:** suspends the current task while an awaitable is not ready.
- **`create_task()`:** schedules a coroutine as an independent task.
- **`gather()`:** coordinates multiple awaitables and collects results.
- **`TaskGroup`:** gives related tasks a shared lifecycle and failure scope.
- **Queue:** buffers work between producers and consumers.
- **Backpressure:** prevents a producer from overwhelming a slower consumer.
- **Lock:** protects exclusive access to shared state.
- **Semaphore:** limits concurrent access.
- **`to_thread()`:** runs blocking synchronous functions in a worker thread.
- **Process pool:** runs CPU-bound work in separate processes.
- **Cancellation and supervision:** coordinate how work stops and how resources are cleaned up.
