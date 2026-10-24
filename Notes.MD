
- [Sync and Async](#sync-and-async)
  - [Why Async exists](#why-async-exists)
  - [CPU-bound vs I/O bound](#cpu-bound-vs-io-bound)
    - [CPU-bound](#cpu-bound)
    - [I/O bound](#io-bound)
  - [Concurrency and parallelism](#concurrency-and-parallelism)
    - [Concurrency](#concurrency)
    - [`await` vs `yield`](#await-vs-yield)
    - [Parallelism](#parallelism)
  - [Processes and threads](#processes-and-threads)
    - [Process](#process)
    - [Thread](#thread)
  - [Event loop](#event-loop)
  - [Async in python](#async-in-python)
    - [`await` vs `asyncio.create_task`](#await-vs-asynciocreate_task)
    - [`asyncio.gather()`](#asynciogather)
    - [Timeouts](#timeouts)
    - [Async generators and streaming](#async-generators-and-streaming)
    - [Context managers](#context-managers)
      - [Lifecycle of a `with` statement](#lifecycle-of-a-with-statement)
    - [Async context managers](#async-context-managers)
    - [Async Context Manager with a Network Resource](#async-context-manager-with-a-network-resource)
    - [Async streaming](#async-streaming)
    - [Common async mistake](#common-async-mistake)
      - [Blocking the event loop accidentally](#blocking-the-event-loop-accidentally)
      - [Creating tasks without properly managing them](#creating-tasks-without-properly-managing-them)
      - [Losing track of a task's exceptions](#losing-track-of-a-tasks-exceptions)
      - [Retrieving exceptions without awaiting immediately](#retrieving-exceptions-without-awaiting-immediately)
      - [Assuming `async def` makes a function non-blocking automatically](#assuming-async-def-makes-a-function-non-blocking-automatically)
      - [Forgetting to await a coroutine](#forgetting-to-await-a-coroutine)
      - [Assuming `asyncio.gather()` automatically cancel all other operations when one fails](#assuming-asynciogather-automatically-cancel-all-other-operations-when-one-fails)

# Sync and Async

Synchronous (Sync) execution: The operations happen one after another  in order. Each operation must finish (executed) before the next one starts.

Asynchronous (Async) execution: An operation can be started and suspended while waiting, instead of blocking allowing other work to make progress before that operation finishes.

## Why Async exists

Blocking operation: operation that prevents your program from making progress until the operation finishes.

``` python
data = request.get(...)
```

The program cant execute the next line until that HTTP request completes. It is blocked.  
Not because python is "busy thinking", but because it is a waiting for something  outside that process to respond.

That "something" could be:

- An LLM API.
- Data base.
- File on disk.
- Another microservice.
- Vector database.
- Cloud storage.

Python isn't doing hte work, the remote server is. Python is just waiting.  

## CPU-bound vs I/O bound

### CPU-bound

A task is CPU bound when the processor is actively doing calculations. i.e. Tasks use the processor heavily.

**Example**:

- Training a neural network.
- Matrix multiplication.
- Image processing.
- Video encoding.
- Large numerical computations.


### I/O bound

Task that spend most of its time waiting for input or output.

**Example**:

- HTTP requests.
- Database queries.
- reading files.
- Writing files.
- communication with Redis.
- Querying a vector database.
- Calling an LLM API.'

The CPU does very little word. Most of the elapsed is waiting.

> Don't waste a scarce computational resource waiting for something that doesn't require that resource to be continuously occupied.  

Async/concurrency is especially valuable when work contains periods where it cannot make progress because it is waiting for something external. I.e it is very valuable with I/O bound tasks not CPU bound tasks.

**preemption:** An operating system can interrupt a running CPU task and switch to another task.

## Concurrency and parallelism

### Concurrency

 The ability of a system to make progress on multiple tasks during overlapping periods of time, by switching between tasks when appropriate. example if A waits for the database while B runs, A and B are progressing concurrently.  

It has 2 types:

**Cooperative Concurrency:** A concurrency model where running tasks voluntarily yield control so that other tasks can execute.

Pros:

- Very efficient for suitable workloads.
- The task controls when it gives up execution.
- Particularly well suited to I/O-heavy workloads.

Cons:

- A badly behaved task that does't yield can block other tasks.
- The system can't force it to cooperate.

**Preemptive concurrency:**  A concurrency model where the system can interrupt a running task and give anther task CPU time, without requiring the running task to voluntarily yield.

Pros:

- One task can't normally monopolize the CPU indefinitely.
- Better protection against badly behaved CPU-heavy tasks.

Cons:

- Context switching has overhead.
- Scheduling becomes more complex
- Shared state can become harder to reason about because a task can be interrupted at essentially any point.

### `await` vs `yield`

`await`: suspends a coroutine while waiting for an awaitable.

`yield`: produces a value and suspends a generator, preserving its state until the next value is requested

### Parallelism

 Multiple pieces of work are actually executing simultaneously, typically on different CPU cores.  

## Processes and threads

### Process

A process is an isolated running instance of a program, with its own memory space and operating-system resources.

The important property is **isolation**.  
IF your FastAPI process has `x = 10`, and VS Code has `x = 500` they don't share the same `x`.  
They are separate memory spaces.

THis isolation is extremely useful for stability and security, but it also makes communication between processes more expensive and more complicated.  

### Thread

A thread is a unit of execution inside a process. It executes instructions on the CPU and shares the process's memory and resources with other threads belonging to the same process.

Thread is an execution context managed by the operating system. It is not a task.

Distinction:

``` text
Process = container + resources + memory
Thread  = execution path inside that process
Task    = work that needs to be done
```

A process can contain multiple threads. The threads belong to the same process and therefore can share much of the process's memory/resources.  

The problem: If thread A and thread B both modify the same piece of data at the same time, you can get race conditions.  

Task: a work that needs to be performed.  

You can have thread of multiple tasks where the thread switches between tasks:

```text
Thread 1
   │
   ├── Task A
   ├── Task B
   └── Task C
```

Layers of the process:

```text
Process
   ↓
Threads
   ↓
Tasks
   ↓
CPU execution
```

CPU execute instructions that some execution context has been scheduled to run.  
> The thread can execute other work, and the CPU executes the instruction of that thread.  

**Cooperative async**  
One thread manages many tasks and switches between them when a task yields/waits.

Tasks are not threads. Many tasks can live on the same thread.

**One thread per request/task**  
for every task/request we make it in one thread alone.

Each request has its own OS-manged execution context.

One thread per request is not a rule. It is one possible design, but production systems use a thread pool, where a limited number of threads handle many requests over time.

Why we don't create 1000 threads for 1000 questions?  
Because threads are'nt free. They consume memory and OS resources, and scheduling thousands of threads introduces overhead.

Mental model:

``` text
                 Concurrency
                     │
          ┌──────────┴──────────┐
          │                     │
      One Threads           Cooperative
          │                   async
          │                     │
 Multiple execution        One execution
 contexts                  context
          │                     │
          ↓                     ↓
   OS manages threads     Tasks yield
                          to each other
```

No one is universally better that other.  

Threads can be excellent when you have blocking libraries or certain workloads.  

Async is particularly attractive when you have huge numbers of I/O-bound operations and want many light weight tasks sharing a small number of execution threads.  

Thread is an execution context, while task is a unit of work that needs to be executed.

For this ordinary function:

``` text
process_order()

1. Read order
2. Query database
3. Process result
4. Call payment service
5. Save result
6. Return response
```

If this function executing on a thread, the thread is effectively following that sequence.

Suppose step 2 requires waiting 2 seconds for the database.

In blocking model:

```text
Thread
  ↓
Task: process_order()
  ↓
Query DB
  ↓
WAIT 2 seconds
  ↓
Continue
```

The thread is stuck inside the task. But in the cooperative async model we want something more like:

```text
Thread
  │
  ├── Task A
  │      └── DB query → waiting
  │
  ├── Task B
  │      └── HTTP query → waiting
  │
  └── Task C
         └── CPU work
```

The thread needs t keep track of where each task currently is.

**Example**:

```text
Task A:
"I sent the DB query.
I'm waiting for its result.
When it arrives, continue from step 3."

Task B:
"I sent the HTTP request.
I'm waiting for the response.
When it arrives, continue from step 4."

Task C:
"I'm currently executing step 2."
```

A cooperative task needs to be pausable and resumable.  

It is not enough to say "Stop A", the system needs to preserve A's execution state so latter can say "Resume A exactly where you left off."

The crucial property is **execution state of the task survives the suspension.**  
And this is the conceptual reason we eventually need coroutines.

**coroutines**: It is essentially a function-like computation that can suspend its execution and later resume from where it stopped(suspended).

When a task resumes, it doesn't start over. It effectively continues from the suspended point with its previous state intact.

A thread has execution state too. The difference is that a thread is an operating-system execution context, while a coroutine/task is much lighter unit of suspended/resumable work managed by the program/runtime.

---

## Event loop

The component that is responsible for managing the coroutines.  

The event loop is the mechanism that enables cooperative concurrency in async programs. It runs on a thread and manages multiple coroutines/tasks.  

A task runs until it reaches an `await` point where it cannot make progress, then it yields control back to the event loop.  The event loop can then give the execution opportunity to another ready task.

**Task state:** A task can be running, waiting/suspended, ready to resume, or completed:

- Running: currently executing.
- Waiting/suspended: cannot currently make progress, usually because it is waiting for an awaited operation.
- Ready: able to continue execution when the event loop schedules it.
- Complete: finished execution and produces a result or execution

The scheduling is **cooperative** because the event loop does not forcibly interrupt a running task. The task must reach a point where it yields control,  typically through `await`.

The relationship is  like:

``` text
Process
  │
  └── Thread
        │
        └── Event Loop
              │
              ├── Task A
              ├── Task B
              ├── Task C
              └── Task D
```

While thread provides the execution context. The event loop is the scheduler that manages the async tasks.

**Example**

``` text
Thread
  │
  ▼
Event Loop
  │
  ├── Task A → waiting for I/O
  │              ↓
  │            suspended
  │
  ├── Task B → running
  │              ↓
  │            await
  │              ↓
  │            yields control
  │
  └── Task C → ready
                 ↓
               runs
```

So when A reaches an `await` and suspends, the event loop essentially says "A can't make progress right now. what else can I run", then it can run B or C.

Later when A's I/O operation is ready, the event loop knows that A can make progress again and schedules A to resume.

Three-layer model:

``` text
CPU
 ↓
Thread
 ↓
Event Loop
 ↓
Coroutines / Tasks
```

The CPU executes instruction.  
The thread is the execution context running those instructions.  
The even loop;o manages which async task gets that execution opportunity.  

**Example** on how even loop work:**

``` text
A → waiting for database
B → ready to run
C → waiting for HTTP
```

The event loop chooses B, B runs and reaches an `await` for another HTTP request. At that exact moment the event loop can run another ready task.  
The event loop does something like:

``` text
A → waiting for DB
B → running
C → waiting for HTTP
        ↓
B reaches await because the awaited operation isn't ready
        ↓
B suspends
        ↓
Event loop checks what can make progress
        ↓
A? ready?
C? ready?
other tasks? ready?
        ↓
Choose something that can run
```

The event loop doesn't necessarily necessarily "check A, then C then D ..." by repeatedly asking every task whether it is ready.  
The underlying I/O system can  notify the event loop about which operations became ready.  
That is one of the reasons event-driven systems scale well.

**conceptual progression:**

```text
Thread
  ↓
Can execute many tasks cooperatively
  ↓
But who manages that cooperation?
  ↓
Event Loop
  ↓
Schedules the tasks
  ↓
Tasks yield at await points
  ↓
Event loop runs another ready task
```

Coroutine: The suspendable computation/function.
Task: A coroutine that has been scheduled to run by the async runtime/event loop.
Event loop: the mechanism that manages and schedules those tasks.

## Async in python

```python
async def fetch_data():    
    print ("started")
```

When writing async function python coroutine function.

```python
fetch_data()
```

When calling the function only the python does not execute the body like a normal function call. It creates a coroutine object representing the computation that can be executed/resumed later.

A coroutine object is not "running asynchronously", it is just an object representing work that can be run.  
A task is what gives that coroutine an independent scheduled execution lifecycle with in the event loop.

```text
normal function

call()
  ↓
execute immediately
  ↓
return result
```

```text
coroutine function

call()
  ↓
create coroutine object
  ↓
nothing in the body executes yet
  ↓
someone must schedule/await it
  ↓
execution begins
```

calling an async function creates a coroutine object, it does note execute the coroutine body. The  coroutine must later must be awaited or scheduled for execution.

**Example**:

``` python
coro = fetch_data()
```

At this point, conceptually:

``` text
Coroutine object
┌─────────────────────────┐
│ Code: fetch_data        │
│ State: not started      │
│ Local state: ...        │
│ Resume information: ... │
└─────────────────────────┘
```

It exists, but the body hasn't started.

Later, something can say:

``` python
await coro
```

Eventually it may reach another `await`

`async def` suspends the current coroutine until the awaited operation can make progress, giving the event loop an opportunity to run other work.

`await` is not merely "wait until this function finishes". It means gives the current execution flow a coroutine to execute and allows that coroutine to suspend when it reaches an awaitable operation. i.e. "Suspend this coroutine while this awaitable is incomplete allowing the event loop to run other work"

**await vs yield**  

`await`: suspends a coroutine while it waits for an awaitable to make progress.

`yield`: produces a value from a generator and suspends the generator until the consumer requests the next value.

`asyncio.create_task`  Means schedules a coroutine as a task on the event loop. It does not create a thread.

`asyncio.run()` is the entry point that takes the coroutine-based program and gives it an event loop to execute it. It establish the environment in with the async program can run.

It is doing something like:

```text
Create event loop
       ↓
Start event loop
       ↓
Run main() coroutine
       ↓
main() creates/schedules other tasks
       ↓
Event loop manages them
       ↓
main() finishes
       ↓
Clean up
       ↓
Close event loop
```

If you tried to run `await task_A` in normal ordinary Python script at the top level, python would complain Because there is not already an event loop actively managing your code at that point.

Jupyter notebook however, runs an environment that already has an event loop;o available for interactive execution.  
So when you write `await task_A` inside Jupyter you already entering an already-running async environment.  

But `asyncio.run(main())` in the same environment with error along lines of:

``` text
RuntimeError:
asyncio.run() cannot be called from a running event loop
```

Because you are essentially trying to create a new event loop inside an already running one.

Normal `.py` app:

``` python
async def main():
    ...

if __name__ == "__main__":
    asyncio.run(main())
```

In Jupyter, you can often simply do:

```python
await main()
```

Awaitable: something that represents asynchronous work whose result may not be available yet, and that python know hwo to suspend and later resume around.

Kinds of awaitables:

1- Coroutine

```python
async def fetch():
  ...
  
coro = fetch() # coro is Coroutine (awaitable) 

result = await coro # The value returned by the coroutine
```

2- Task

```python
task = asyncio.create_task(fetch())

result = await task
```

3- Future: think of it as an object that representing a result that will become available later.

Conceptually:

``` text
Future
   │
   ├── result not ready yet
   │
   │       ... something happens ...
   │
   └── result becomes available
```

### `await` vs `asyncio.create_task`

Suppose we have:

```python
async def get_users():
    return await client.get("/users")
```

There is two fundamentally different ways to use it:

```python
result = await get_users()
```

`await` means "Run/continue this awaitable as part of my current task, and suspend my current task until it produce a result."

```python
task = asyncio.create_task(get_users())
```

`create_task` means "schedule this coroutine as an independent task (new task), and give me the task object immediately so the current task can continue immediately."

Suppose we have:

```python
async def main():
    result = await get_users()
    print(result)

async def background():
    while True:
        print("background")
        await asyncio.sleep(1)

async def program():
    task = asyncio.create_task(background())

    await main()
```

Then there is 2 tasks:

- Task1: program
- Task2: Background

`program` and call `await main()`, so `main()` runs as part of Task 1 (runs before `background()`).  
Then suppose `main()` reaches `await get_users()`, and `get_users()` is waiting for the network I/O.

Task 1 is suspended, but task 2 already exists:

```text
Task 1: program → main → waiting for network
                                  ↓
                              SUSPENDED

Task 2: background → ready/runs
```

So the event loop can run `background`.  
`await` does not magically make another coroutine run. There must already be another task scheduled (or some other ready event for the event loop to handle).

Now return to the original HTTP example:

```python
async with client:
    response = await client.get("/users")
```

the `get()` call produces a coroutine/awaitable, but hte actual network I/O happen inside the client function. Suppose `client.get()` do something like:

```python
async def get(url):
    request = prepare_request(url)
    response = await send_request(request)
    return response
```

what happen is `client.get()` calls the client function, if the client function have waiting time this mean the current task that executing the `get()` coroutine will be suspended.  

i.e. The current task is executing the `get()` coroutine (`get()` is part of the task). When the `get()` coroutine reaches an operation that cannot complete immediately, the whole current task suspended so the event loop gives another task a chance to be executed.

**Running multiple asynchronous operations concurrently**  

Since `await` adds new coroutine to the current task

```python

async def get_users():
    ...

async def get_products():
    ...

users = await get_users()
products = await get_products()
```

The current task start `get_users()` and waits for it to finish. Only after `get_users()` has completed, it start `get_products()`.

The structure:

```text
Current Task
    │
    ├── await get_users()
    │       ↓
    │    wait
    │       ↓
    │    result
    │
    ├── await get_products()
    │       ↓
    │    wait
    │       ↓
    │    result
    │
    └── continue
```

Even though both operations are asynchronous, they are not being started concurrently.

Now compare that with:

```python
users_task = asyncio.create_task(get_users())
products_task = asyncio.create_task(get_products())

users = await users_task
products = await products_task
```

Both operations have been scheduled as independent tasks before the current task waits for their results.  
`create_task()` exists so we can start asynchronous work now and await its result later.

### `asyncio.gather()`

`asyncio.gather()`: It run concurrently, and don't continue until all of them have finished.

Conceptually

```python
results = await asyncio.gather(
    A(),
    B(),
    C()
)
```

```text
                gather()
                   │
       ┌───────────┼───────────┐
       ↓           ↓           ↓
      A()         B()         C()
       │           │           │
     await       await       await
       │           │           │
       └───────────┼───────────┘
                   ↓
             all complete
                   ↓
               results
```

`gather` expresses start A, start B, Start C and let them progress concurrently then wait until all of them are complete.  
It does not control the order in which the task execute. The event  loop does that. `gather` coordinates multiple awaitables concurrently and collects their results in the order the awaitables were provided.

Event loop -> Determines when each task gets to execute/resume.
`gather()` -> collects the corresponding results then return them in order.

If `gather()` has multiple tasks inside it and one failed it does not automatically cancel the rest.  
Falling doesn't necessarily mean al the underlying tasks are cancelled.  

By default, `gather()` propagates the first exception it encounters to the caller, but it does not automatically cancel the other awaitables. The other operations may continue running.

With `return_exceptions=True`, exceptions are returned as results instead of being immediately propagated, allowing the caller to handle partial failures.

`task.cancel()` it does not end the whole process. It targets specific task and it and request its cancellation. It does not immediately kill the coroutine. It marks the task as being cancelled/schedules a cancellation request.

Cancellation can be delivered cleanly in suspended task.

``` text
task.cancel()
     ↓
request cancellation
     ↓
coroutine reaches a suspension point
     ↓
CancelledError is raised inside the coroutine
     ↓
coroutine can terminate
```

`task.cancel` is a cancellation request, not an immediate termination.  
The task becomes cancelled only after the coroutine actually respond to the cancellation and finishes as cancelled.

> **Coroutine can handle the cancellation or terminate**

A coroutine can catch  `CancelledError`, perform cleanup, and potentially even suppress the cancellation.

**`gather` with `cancel()`**  

Suppose having a task that is a gathering of 2 async functions, cancelling the gathered task will cancel both of the functions as the `gather()` operation itself is being cancelled.

```text
parent Task
    │
    │ await gather(...)
    ↓
 gather()
   ├── A
   └── B
```

Suppose having 2 function `A()` and `B()` that they are gathered together

```python
results = await asyncio.gather(
    A(),
    B(),
    return_exceptions=True
)
```

If A raises `ValueError` and B succeeded, gather() not cancel B. It return `[ValueError(), 'B finished']`.

```text
A fails
    ↓
gather notices the failure
    ↓
return_exceptions=True
    ↓
failure becomes a result
    ↓
B continues
    ↓
gather waits for B
    ↓
both outcomes returned
```

where:

```text
gather itself is cancelled
    ↓
gather cancels its children
    ↓
A + B are cancelled
```

### Timeouts

`wait_for` function that is used for cancelling an async function after passing specific amount of time, If an operation hasn't completed in specific time, request its cancellation.

Using a raise in the exception will cause TimeoutError.  

``` python
async def slow_operation():
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        print("operation cancelled")
        raise
```

`raise` is used after the `except`. It re-throw the exception that is currently being handled.  
It is like: "Yes, I caught it, but I am not claiming that the cancellation didn't happen. Pass it upward."

The cancellation is the mechanism used to stop the operation, while `TimeoutError` is what the caller ultimately sees as the reason the timeout wrapper failed.

Without a raise in the exception it will cause CancellationError.

``` python
async def slow_operation():
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        print("operation cancelled")
        # no raise
```

When `wait_for()` reaches its timeout, it cancels the awaited operation. Once the cancellation is handled, the timeout is reported to the caller as `TimeoutError`.


`wait_for()` is not receiving `CancelledError` and then deciding to "I will call this `TimeoutError`" in a simple exception-conversion sense.  
Internally, it knows it initiated the cancellation because its timeout expired, and once the cancellation completes, teh timeout boundary is reported to the caller as `TimeoutError`.

`asyncio.timeout()` and `asyncio.wait_for()` both enforce time limits. `wait_for()` applies teh timeout directly to an awaitable, while `timeout()` establish a timeout boundary around a block of code.

Instead of:

```python
await asyncio.wait_for(work(), timeout=2)
```

You can write:

```python
async with asyncio.timeout(2):
    await work()
```

 Both are ways of enforcing a time limit. The difference is mainly where the timeout boundary is expressed.

In `timeout` each individual operations collectively have to fit within the deadline.

```python
async with asyncio.timeout(5):
    await get_user() → 1 second
    await get_preferences() → 2 seconds
    await get_recommendations() → 4 seconds
```

So the execution is:

```text
get_user()
   ↓ await
   ↓ 1 sec
returns
   ↓
get_preferences()
   ↓ await
   ↓ 2 sec
returns
   ↓
get_recommendations()
   ↓ await
   ↓ 4 sec
returns

Total: 1 + 2 + 4 = 7 seconds
```

Using `gather` allows the operations to make progress concurrently.

```python
async with asyncio.timeout(5):
    await asyncio.gather(
        get_user(),
        get_preferences(),
        get_recommendations()
    )
```

The structure:

```text
asyncio.timeout(5)
        │
        └── gather(...)
              ├── get_user()           → 1s
              ├── get_preferences()    → 2s
              └── get_recommendations()→ 4s
max(1, 2, 4) = 4 seconds
```

So they finish before the 5 second deadline.

The timeout is a single deadline shared by everything inside the `asyncio.timeout()` block.

`asyncio.timeout()` does not give `gather()` a separate timeout for each operation. It establish one deadline for the entire block containing the `gather()`.  
If one operation in gather is cancelled due to timeout the whole gather operation is cancelled. 

### Async generators and streaming

**Async generator**  

`yield`: produces a value and suspends the generator, preserving its state so it can resume later.

**Coroutine vs. Async generator**  

**Coroutine**  

```python
async def get_data():
    return "hello"

coro = get_data() # coro is coroutine object
```

Coroutine object: represents the computation that eventually produces one result when awaited.

**Async generator**  

```python
async def numbers():
    yield 1
    yield 2
    yield 3

result = numbers() # result is async generator object
```

Async generator object: represents a computation that can produce multiple results overtime.

Key distinction: A coroutine is awaited to obtain its result; an async generator is iterated asynchronously to receive a sequence of values produced over time.

**Async iterator**  

`__aiter__()`: Returns the async iterator.

`__anext__()`: return the next value.

```python
async for x in asynchronous(): # Async iterator where asynchronous() is async generator function
```

```python

# async iterator

async def async_iterator_numbers():
    for i in range(3):
        await asyncio.sleep(1)
        yield i

# async iterator with sleep
async for number in async_iterator_numbers():
    print(number)
    await asyncio.sleep(5)



```

Using time delay in iterator with async generator will result in the generator stopping until the iterator's time delay is over, then the generator start to be resumed.  
The async generator (the producer) is suspended because the consumer (`async for`) is currently waiting/sleeping, not because the iterator somehow blocks it.

Async generator produces the next value only when the consumer request it. if the consumer suspends after receiving a value, the generator remains suspended until the consumer requests the next value.

**Backpressure**  

in back pressure the producer work independently from the consumer, while the consumer is suspended the producer can continue running and produce outputs(data).  
The outputs is stored in queue (`asyncio.Queue`).

The queue is a buffer between a fast producer and a slow consumer.

**Buffering vs backpressure**  

**Buffering** means temporarily storing produced data so the producer and consumer do not need to operate at exactly the same time.

**Backpressure** mechanism happens when the buffer reaches its limit and the producer forced to slow down or wait because the consumer cannot keep up.

Suppose the producer generates 1000 times per seconds, but the consumer can produce only 10 per second, we will find a problem which is the maximum capacity of the queue, and eventually the producer fills it.

When the queue is full the producer waits until the consumer removes something so it can have some free space, and this called **backpressure**.

**Backpressure:** The slow consumer effectively pushes pressure backward toward the producer, preventing the producer from endlessly creating data and consuming unlimited memory.

Backpressure is what happens when a producer is forced to slow down because the consumer can't keep up.

When the queue gets full the producer itself become suspended while the consumer continues running, after the consumer get the data, space becomes available in the queue allowing producer to resume.  
`asyncio.Queue` is FIFO by default, so `get()` takes the oldest item first. `get()` is the queue's consumption operation, so it removes and returns the oldest item.

Suspending one task does not suspend the event loop. The producer can be suspended while the consumer runs, then the consumer can be suspended while the producer runs, the event loop coordinates both.

We can deal with slow consumer by using backpressure, so producer waits temporarily and consumer eventually progress.  
For stuck consumer the producer may wait forever and the consumer never progresses, so we can use timeouts and cancellation

The queue is useful when:

- The consumer can be suspended but we want the generator/producer to keep producing data.
- The producer is needed to be independent from the consumer.

> Use a queue when the producer should be able to continue independently of the consumer and therefore needs somewhere to buffer its output.

### Context managers

When you manually acquire resource:

```python
file = open("data.txt")

# use the file
data = file.read()

file.close()
```

The life cycle is acquire resource -> use it -> release resource.
The problem is what happens if something goes wrong while using it?

**Example**:

```python
file = open("data.txt")

data = file.read()

process(data)   # imagine this raises an exception

file.close()
```

If `process(data)` raises an exception, execution jumps out of that normal sequence. normal sequence. The `file.close` line may never execute.  
So we acquired the resource but we potentially never released.

The same pattern appears every where in programming:

```text
open file -> close file
open database -> close connection
acquire lock -> release lock
open network -> close connection
allocate temp resource -> clean it up
```

Here is  why `with` exists.

iIt acquire resource -> use it -> cleanup.  
The important part is that cleanup belongs to the lifecycle of the resource rather than being something manually you remember to do at the end.  

`with` does'nt mean "close the resource". It guarantees that the context manager's exit behavior is invoked.  
So, it:

- Prevents the caller from having to manually remember the cleanup step.
- The context manager's `__exit__()` is invoked when leaving the `with` block.

**Why is leaving a resource open actually a problem?**  
Because a resource usually represents  something that the operating system, a server, or another system is actively keeping track of.

**Example** for a file, if you do `f = open("data.txt")` python doesn't merely create a python object. It asks the operating system to open the file and gives your process access to that OS-level resource.  

So if the file was never closed, that OS resource can remain allocated. For a single file, we might not notice anything but imagine doing this for thousands of files. 

```python
for filename in thousands_of_files:
    f = open(filename)
    # use f
    # forget to close it
```

Eventually you can run into limits on how many files/resources your process is allowed to have open.

The files are not the only example, this can happen with database connection, where leaving a connection open unnecessarily can consume connection-pool/server capacity.  

Other case is lock:

```python
lock.acquire()

# something goes wrong

# lock.release() never happens
```

In this case the lock will never got released so another task/thread might wait indefinitely for that lock.

**Lock:** it is a synchronization mechanism used when multiple concurrent pieces of code need to access something shared. The lock provides a way of allowing one piece of code to access shared thing.

**Example**: 2 tasks (A,B) accessing the same shared variable `balance = 100` task A: withdraw 80, task B: withdraw 50. Without some coordination both could observe `balance = 100` and before either one updates it they both read it in the same time resulting in a wrong final value calculation:

```text
Task A: reads balance → 100
Task B: reads balance → 100

Task A: calculates → 20
Task B: calculates → 50

Task A: writes → 20
Task B: writes → 50
```

The final value becomes 50, even both withdrawals together were 130.  
The concurrency problem caused by multiple operations interacting with shared state.

With lock: task B waits until task A finish using hte shared resources then release the lock:

```text
             Lock
              ↓
Task A → [ acquire ] → use shared resource → [ release ]
                                                ↑
                                                │
Task B → waits ─────────────────────────────────┘
```

**Resource leak:** the program acquires some resource but fails to properly release it after  no longer needed.

**What actually makes an object work with `with`?**  

`with` manages a resource's lifecycle: enter/setup → use → exit/cleanup.  
python needs a way to know what "enter" and "exit" mean for a particular object.  
That's where `__enter__()` and `__exit__()` come in.

Suppose `with resource: ---` the resource lifecycle:

```text
        with block starts
              ↓
        __enter__()
              ↓
        code inside with
              ↓
        __exit__()
              ↓
        with block finished
```

`__enter__()` is responsible for the entering/setup side, like:

- Open resource.
- Acquire lock.
- Start transaction.
- Establish connection.

`__exit__()` is responsible for the leaving/cleanup side, like:

- Close resource.
- Release lock.
- Rollback/commit transaction.
- Close connection.

**Tiny custom context manger**  

```python
class Resource:
    def __enter__(self):
        print("ENTER")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("EXIT")


with Resource():
    print("INSIDE")
    raise ValueError("Something went wrong")

print("AFTER")
```

The output of the previous code is:

```text
ENTER
INSIDE
EXIT
ValueError: Something went wrong
```

Notice that "Enter", "INSIDE", "EXIT" got printed before the ValueError.  
Also the error Continue outside the `with` block and "After" wasn't printed.  

The three arguments of `__exit__` becomes important in the error cases:

``` python
def __exit__(self, exc_type, exc_value, traceback):
```

In our example:

`exc_type`: ValueError.
`exc_value`: ValueError("Something went wrong").
`traceback`: traceback information.

The `exc_value` is the actual exception object, not just the "Something went wrong".

- `exc_type`: What kind of exception.
- `exc_value`: "what exception object / message?"
- `traceback`: "where in the execution path did it happen?"

A traceback is the execution history that tells python where the exception came from.

Without the 3 args "EXIT"  will not be printed and we receive TypeError in addition to the Value error, why?  
Because `__exit__()` is the method responsible for the exit part of teh context manager protocol (when we use `with`). But python can only invoke the method if the method has the required signature.

So in case of:

``` python
def __exit__(self):
```

When error happens the python called it like:

```python
resource.__exit__(exc_type, exc_value, traceback)
```

Since `self` is passed automatically we have 4 positional argument total, and our method only have one which is `self`.  
So python attempted to call `__exit__()` but the call itself failed with TypeError:

```text
TypeError:
Resource.__exit__() takes 1 positional argument but 4 were given
```

Thats why `"EXIT"` never printed.

The sequence:

```text
ENTER
  ↓
INSIDE
  ↓
ValueError occurs
      ↓
Python tries to call __exit__(...)
      ↓
__exit__ has the wrong signature
      ↓
TypeError occurs while trying to call __exit__
```

If nothing goes wrong, `__exit_()` is still called. but if there is an error (like `raise ValueError(`error`)`) `__exit_()` is also called, but python gives it information about the exception:

`exc_type` = None
`exc_value` = None
`traceback` = None

If an exception occurs inside the `with` bock, python calls `__exit__()` with information about that exception.

Note: `__exit__` can handle the exception depending on what it does with the received arguments.

#### Lifecycle of a `with` statement

```python
with Resource() as x:
    do_something(x)
```

There is two important moments in the code:

Entering

```python
x = resource.__enter__()
```

Leaving:

```python
resource.__exit__(...)
```

Python invokes the exit behavior regardless of whether the block finished normally or an exception.  

When the block finishes normally:

exc_type = None  
exc_value = None  
traceback = None  

When an error occurs:

exc_type = the exception type  
exc_value = the exception object  
traceback = traceback information  

So:

```text
Normal execution:

__enter__()
    ↓
body
    ↓
__exit__()
    ↓
continue


Exception:

__enter__()
    ↓
body
    ↓
exception
    ↓
__exit__()
    ↓
exception propagated OR suppressed
```

This is the key reason `with` solved the resource-lifecycle problem.

```python
class Connection:
    def __enter__(self):
        print("Connection opened")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Connection closed")

with Connection() as conn:
    print("Doing work")
```

`conn` is a variable(name) that refers to whatever object `__enter__()` returns.  
Because `__enter__()` returns `self` in this example, `conn` refers to the same `Connection` object created by `Connection()`

`return self` means return this particular `Connection` object, and `conn` refers to that object, which mean that `conn` is a name/variable that points to an object in memory.

> An object is the actual thing in memory; a variable/name is a way to refer to that object. `return self` returns the current object so `conn` receive a reference to that same object.


```python
class Resource:
    def __enter__(self):
        print("ENTER")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("EXIT")
        return True

with Resource():
    print("INSIDE")
    raise ValueError("Something went wrong")

print("AFTER")
```

In the previous example, the output will be:

```text
ENTER
INSIDE
EXIT
AFTER
```

and there is no unhandled `ValueError`, why?  
The return value of `__exit__()` has special meaning. When `__exit__()` returns `True`, it tells python "The exception that occurred inside this context has been handled. Do not propagate it."  

The flow:

```text
ValueError occurs
       ↓
__exit__(ValueError, ...)
       ↓
__exit__ returns True
       ↓
Python suppresses the exception
       ↓
execution continues after the with block
       ↓
print("AFTER")
```

`__exit__()` didn't magically make the exception disappear. it made a decision about what python should do with the exception by returning `True`.

**The complete context manager-mental model:**

```text
with Resource() as x:
        ↓
create Resource
        ↓
__enter__()
        ↓
x = whatever __enter__ returns
        ↓
run body
        ↓
body finishes OR exception occurs
        ↓
__exit__(exc_type, exc_value, traceback)
        ↓
__exit__ performs exit/cleanup behavior
        ↓
return True?
   ↙       ↘
 yes        no/None
  ↓           ↓
suppress    propagate
exception   exception
```

### Async context managers

The life cycle of context mangers includes getting the resource at the start and close it at the end. The question is why ordinary `__enter__()` and `__exit__()` are not enough?  
The process of getting the resource and closing it may have a waiting time depends on the resource itself. Suppose an HTTP client needs to establish or clean up network-related state, this time can be used to execute other ready tasks.

for the ordinary `with`, python uses:  
`__enter__()` for entering/setup the resource , and for exiting/close the resource `__exit__(...)`.

An ordinary context manager `__enter__()` and `__exit__()` can't use `await` because those are normal functions.  
As async context manager `async def __aenter__()` and `async def __aexit__()`.

In the `async with`, python uses:  
`await __aenter__()` for entering/setup the resource asynchronously, and for exiting/close the resource asynchronously`await __aexit__(...)`.

```python
async def __aenter__(self):
    await asyncio.sleep(2)
    print("CONNECTED")
    return self
```

For this code, during the 2 seconds of sleeping the event loop suspends the current task then go for execute ready tasks.  
The suspension happens at the `await` inside `__aenter__()` not because `async with` itself magically pauses.

`async` does not mean `__aenter__()` must suspended, if the awaited operation is already immediately complete, there may no meaningful scheduling opportunity.

```text
ordinary context manager
    with
      ↓
__enter__()
__exit__()


asynchronous context manager
    async with
      ↓
await __aenter__()
await __aexit__()
```

Async does not remove the waiting time. It prevents the waiting time from unnecessarily occupying the event loop.

**We can't simply do:**

```python
class Resource:
    async def __enter__(self):
        ...

    async def __exit__(self, exc_type, exc_value, traceback):
        ...
```

Because `with` and `async with` are two different protocols.  
Ordinary `with resource:` expects the synchronous context-manager protocol `resource.__enter__()`,`resource.exit()`.  

While `async with resource:` expects teh asynchronous context-manager protocol: `await resource.__aenter__()`, `await resource.__aexit__(...)`. The distinction matters because python needs to know whether entering/leaving the resource can involve asynchronous suspension.  

In ordinary `with`:  
`with resource:`  
The entering operation is synchronous:

```text
__enter__()
   ↓
must finish
   ↓
body starts
```

If `__enter__` did some blocking network operation, that operation could block the event loop if called from async code.

With `async with`:  
`async with resource:`  
Python explicitly knows:  

```text
__aenter__()
     ↓
await
     ↓
may suspend
     ↓
event loop can run other Tasks
     ↓
finished
     ↓
body starts
```

The same distinction with applies when leaving:

```text
with
 ↓
__exit__()
 ↓
done
```

versus:

```text
async with
 ↓
await __aexit__()
 ↓
may suspend
 ↓
event loop runs other Tasks
 ↓
done
```

So `__aenter__` and `__aexit__` aren't just differently named versions of `__enter__` and `__exit__`, They represent different protocols:

```text
Synchronous context manager
        ↓
with
        ↓
__enter__ / __exit__


Asynchronous context manager
        ↓
async with
        ↓
__aenter__ / __aexit__
        ↓
awaitable lifecycle operations
```

An async context manager doesn't necessarily have to perform I/O in both methods. `__aenter__()` and `__aexit__()` can be asynchronous even if a particular implementation happens to complete immediately.  
The protocol simply allows those lifecycle operations to suspend.

### Async Context Manager with a Network Resource

Imagine an HTTP client:

```python
async with client:
    response = await client.get("/users")
```

There are two different asynchronous operations happening here.  

First: `async with clint:` this managed the client's lifecycle:

```text
__aenter__()
    ↓
possibly establish/setup resources
    ↓
client becomes ready
```

Second: `await client.get("/users")` this performs an asynchronous network operation:

```text
send request
    ↓
await network response
    ↓
current Task suspends
    ↓
event loop runs other Tasks
    ↓
response arrives
    ↓
Task resumes
```

Then when the block ends:

```text
__aexit__()
    ↓
cleanup/close client resources
    ↓
possibly await network/OS cleanup
```

So there is two different kinds of async behavior:  
`async with`: manages resource lifecycle.  

`await client.get(...)`: performs an asynchronous operation using that resource.  

`async with` does not makes everything inside the block asynchronous, for example:

```python
async with client:
    result = expensive_cpu_calculation()
```

The `async with` only affects the lifecycle of `client`. It does not change the nature of `expensive_cpu_calculation()`

when it is time for this task to be executed, it will take long time and we cant stop it to start a new ready task.  
Thats because it is just an operation that require a lot of CPU computation time (CPU bonded operation).  

It is not simply i/o bound so we can hold it till we got the respond from external source (like getting database values).

Also there is no `await` in the calculation, so the coroutine has no suspension point during that computation and can monopolize the event loop until the calculation finishes.

```python
async with client:
    response = await client.get(...)
```

Here, the `await` on `client.get()` allows the current task to suspend while the asynchronous operation is waiting for I/O.

However, the `await` makes the suspension possible but it does not guarantee that a scheduling switch actually occurs.  
If the awaited operation is already complete, the coroutine may continue without meaningfully giving another task a chance to run

The principle that the two example are illustrate is: `async with` does not transform the code inside the block into asynchronous code.  
The code inside the block is still synchronous unless that code itself performs asynchronous operations, such as `await`.

**Example**

```python
class AsyncResource:
    async def __aenter__(self):
        print("ENTER")
        await asyncio.sleep(2)
        print("READY")
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        print("EXIT")
        await asyncio.sleep(2)
        print("CLOSED")


async def main():
    async with AsyncResource() as resource:
        print("USING")
        await asyncio.sleep(3)
        print("DONE")

```

There is 3 separate suspension periods:

1. `__aenter__()`: `await asyncio.sleep(2)`.
2. The body: `await asyncio.sleep(3)`
3. `__aexit__()`: `await asyncio.sleep(2)`

This gives us clear distinction:

1. Resource acquisition (`__aenter__()`): may suspend.
2. Resource usage (body): may suspend.
3. Resource cleanup `__aexit__()`: may suspend.

`async with` does not create these suspension points by itself, the suspension happens because the as ync context-manager methods and the body contain awaitable operations.

Imagine as async HTTP client with this lifecycle:

```python
async with client:
    response = await client.get("/users")
    data = await response.json()
```

There are tree different asynchronous operations:

1. `__aenter__()`: establish/prepare the client resource
2. `client.get(...)`: perform network I/O
3. `response.json()`: possibly perform additional asynchronous work

And then `__aexit__()`: clean up the client resource.

All four can potentially contain suspension points, but they serve different purposes.

The operations are asynchronous but all of them depend each other, so we can't work concurrently within the same block.  

We can't start `client.get()` before the client has been successfully acquired, and you can't start `response.json()` before you have the response.

The operations within this particular workflow are sequential/dependent, but the task execute concurrently with other tasks whenever it reaches an actual suspension point.

**Client with cpu bound function**  

Suppose the client have function:

```python
async with client:
    result = client.calculate_something()
```

Where `calculate_something()` is an ordinary CPU-bound synchronous function.  
The `async with` will not make `calculate_something()` asynchronous, as `calculate_something()` is ordinary synchronous CPU-bound code.  
The execution of the function consume CPU computation, the event loop can't take control away from the task simply because the calculation is taking a long time.

### Async streaming

**Streaming** means receiving or producing data progressively over time instead of waiting for the entire result to be available before receiving anything.  
Streaming itself is not an async concept. We can have streaming without python `asyncio`, and we can have async code that is not streaming.

Streaming describes how the data is delivered: " Don't wait for the complete result; deliver pieces as they become available."  
Async describes how the program handles waiting and concurrency: "When I have to wait for the next piece, don't block the execution thread; suspend and let other work run."

Suppose we have:

```python
async def stream_data():
    async with AsyncResource() as resource:
        async for chunk in resource:
            yield chunk
```

and the consumer does:

```python
async for chunk in stream_data():
    print(chunk)
```

What happens is when the consumer receives the first `chunk`,  the resource was acquired, the stream produced the first `chunk`, **and the resource is still held** because the stream is still active.  
Thats because the resource is still needed after receiving the first `chunk`.  

When the stream is waiting for the next chunk the task can suspend:

```text
Task
 ↓
process chunk 1
 ↓
await next chunk
 ↓
SUSPENDED
        ↓
        event loop runs other Tasks
        ↓
chunk 2 arrives
        ↓
Task resumes
 ↓
process chunk 2
```

So we have two different things happening simultaneously at the concept level:  

- The resource life cycle: determine how long the underlying resource remains available.  
- The stream: determines how data progressively moves through that resource.  

And the task may repeatedly suspend while waiting for more data.  

The resource stays open while its owning context is active (in our example it is the task that uses it is suspended). It closes when execution exits that context and cleanup runs.  
Task suspension does not mean resource suspension or resource closer.  
The resource is released/closed when the stream/lifecycle is finished, which may involve detecting end-of-stream and performing cleanup.

Suppose:  

```python
async def consume():
    async with resource:
        async for chunk in stream:
            process(chunk)
```

The stream produces 3 chunks and after the last chunk, the stream signals "there is no more data."  
When the stream signals that there are no more chunks:

```text
stream ends
   ↓
async for finishes
   ↓
execution continues after the async for
   ↓
execution reaches the end of async with
   ↓
__aexit__() runs
   ↓
resource is closed/released
```

In the notebook `Streaming example 1`:  
The end of the stream does not automatically mean the resource is closed.  
The stream ended first. Execution was still inside the `async with` block, so the resource remained available until the `async with` scope actually ended.

``` text
async with
┌────────────────────────────────────────┐
│                                        │
│   async for                            │
│   ┌────────────────────────────────┐   │
│   │ A → B → C → END                │   │
│   └────────────────────────────────┘   │
│                                        │
│   still inside resource lifecycle      │
│                                        │
└────────────────────────────────────────┘
                    ↓
                __aexit__()
```

The `async with` owns the resource lifecycle; the stream uses the resource during part of that lifecycle.

**Streaming does not necessarily mean buffering.**  
Consider if producer is generating chunks faster than the consumer can process them.  
If the producer and consumer are independent, something has to happen to the chunks that the consumer hasn't processed yet.

>If production and consumer happen at different rates, the difference has to be handled somewhere

If the producer produces 10 chunks/sec, and the consumer consumes 2 chunks/sec then the system has to deal with the extra 8 chunks/sec somehow.  
**Buffering** is one solution:

``` text
Producer
   ↓
[A B C D E F G H]
   ↓
Consumer
   ↓
processes A
```

The producer doesn't necessarily have to stop immediately, and the consumer doesn't have to process everything at the exact moment it is produced.

When the buffer reaches its limit, backpressure prevent unlimited accumulation by making the producer slow down or wait.  

When the suspension due to the backpressure is happen the resource stays open.

> Suspension doesn't necessarily mean the resource is closed.

**Limitation of buffering**  

Suppose our producer is permanently faster than the consumer:  
Producer: 10 chunks/sec, and consumer: 2 chunks/sec.  

A buffer can absorb the difference temporarily but it won't make the rates equal. If the buffer is unbounded:  

```text
time →       1s   2s   3s   4s   5s
produced     10   20   30   40   50
consumed      2    4    6    8   10
buffer        8   16   24   32   40
```

An unbounded buffer keeps growing if production persistently exceeds consumption.  

If the buffer is bounded, eventually it becomes full, and backpressure forces the producer to wait. So buffering solves a temporary rate mismatch, not permanent one.  

Suppose we are monitoring a temperature sensor that produce 10 readings per seconds, but our consumer process only 2 reading per second.  
Since the goal is to know the current temperature, rather than preserve even historical reading. This called dropping data.  

**For example** if the sensor produces readings `20`,`21`,`23`,`24` while the consumer is busy, keeping `24` and discarding the older readings may be sufficient. This is often called a **latest-value strategy**.

**Latest-value strategy:** The system deliberately prioritizes the newest value over older, potentially stale values. It is useful when the consumer cares about the current state, not the complete history.

**Buffering Strategies for Producer–Consumer Speed Mismatches:**

- **Dropping data:** control resource usage by sacrificing some data, when the application can tolerate it. It doesn't specify which items must be discarded.
- **Unbounded buffering:** preserve everything, but risk unbounded memory growth.
- **Bounded buffering with backpressure:** preserve everything while slowing the producer when necessary.

Why backpressure is safer for the LLM chunks than dropping chunks?  
Because we want to preserve every chunk so that the consumer receives the complete response in the correct order. Dropping chunks can corrupt the output.

The limitations of backpressure

- Resource lifetime and cost: if the producer depends on an open connection to a paid API, slowing consumption can prolong the connection's lifetime and potentially increase cost depends on the service's billing model.
- Latency: the consumer takes longer to finish, and the producer cannot progress freely.

Backpressure does not inherently delay unrelated async tasks. While the producer is suspended at `await queue.put(chunk)`, the event loop can run other ready tasks. The problem is the backpressure cannot make the underlying work disappear. If the resource must remain open until streaming finishes, that resource stays occupied for longer.

**Consumer failing**  

Suppose the consumer raises an exception after second chunk:  

```python 
async with FakeResource() as resource:
    producer = asyncio.create_task(producing(queue, resource))
    consumer = asyncio.create_task(consuming(queue))

    await producer
    await consumer
```

1. The consumer task fails.
2. The producer task is not automatically cancelled just because the consumer failed.
3. The producer continue generating chunks and filling the bounded queue.
4. Eventually, The queue becomes full, and the producer suspends at `await queue.put(chunk)`
5. The producer can remain suspended indefinitely because the consumer is no longer removing items.

This is **deadlock-like situation:** The producer is waiting for the consumer to free queue space, but the consumer has already failed.

In notebook **Example** 2: consumer Task failing independently:  
The consumer retrieves an item and raises an exception. ITs tasks finishes with an exception, but the producer task continues running independently.  
The producer continues generating chunks and putting them into the bounded queue.

Does `main()` reach `await consumer`?  
No, the `main()` is still awaiting producer first:

```python
await producer
await consumer
```

Since the producer gets stuck, `main` never reaches `await consumer`. THe consumer's exception is not automatically propagated to `main()` just because the task failed.  
The `async` with block doesn't exit, and `FakeResource.__aexit__()` isn't called.

Suppose the consumer fails, and we detect its exception, and we want to:

1. Cancel the producer so it stops trying to generate chunks.
2. Allow cancellation to propagate through the producer's coroutine and its async generator.
3. Exit the `async with` block so `FakeResource.__aexit__()` runs.

If we call `producer.cancel()` it request cancellation; it doesn't immediately terminate the task.  
When producer reaches a cancellation point, such as an `await` that allows cancellation to be delivered, `asyncio.CancelledError` can be raised inside the producer coroutine.

When running:  

```python
producer = asyncio.create_task(producing(queue, resource))
consumer = asyncio.create_task(consuming(queue))
```

The `main()` needs a way to discover when one of them finishes.  

There are three approaches:

|Approach |Behavior|
|:------|:-------|
|`await producer`|Wait for the producer to finish   |
|`await asyncio.gather(producer, consumer)` |Await both together; by default, propagate the first exception without automatically cancelling the other task |
|`await asyncio.wait(...)` | Wait according to a specified completion condition, such as the first task finishing |

The third approach is useful when the failure of one task may require us to intervene while another task is still running.

In example 4 using `asyncio.wait` to solve example 3 in notes:

```python
    done, pending = await asyncio.wait( 
        {producer, consumer},
        return_when = asyncio.FIRST_COMPLETED
    )
```

- `asyncio.FIRST_COMPLETED`: the condition for returning.
- `done`: a set of task that have finished, whether successfully or with an exception.
- `pending`: a set of task that haven't finished yet.

In our example, the consumer raises `TypeError`, so the consumer Task finishes with an exception, The producer is still running or stuck waiting for the queue space.

Therefore, `asyncio.wait()` returns:

- `consumer` is in `done`.
- `producer` is in `pending`

The failed task is still a completed tasK. That the central idea.

**Producer failing**  

Suppose `resource.stream()` raises an `OSError` while reading chunk `2`.  

```python
    done, pending = await asyncio.wait( 
        {producer, consumer},
        return_when = asyncio.FIRST_COMPLETED
    )
```

If the producer fails first, it will be in `done`, and the consumer will likely be in pending. We are going to use the same technique used with the failed consumer.

```python
        # Handle producer failure
        if producer in done and producer.exception() is not None and consumer in pending:
            consumer.cancel()

            try:
                await consumer
            except asyncio.CancelledError:
                print("ERROR: Producer failed")
                print("CONSUMER: cancellation completed")

```

When the producer is failed it will be stored in `done` but it will have an exception so `producer.exception()` will have value.  
In `task.exception()` if the task the completed successfully, `task.exception()` returns `None` so the condition will be false. If the task raised an exception, `task.exception()` returns exception so the condition is True

To handle more edge cases we should make sure that the consumer is not finished before the producer so its cancellation will not be meaning less, so we are going to check if the consumer is still not finished or not by checking `consumer in pending`

**Pull-based streaming vs. push-based streaming**  

1- **Pull-based streaming**  

Consider async generator:  

```python
async def stream():
    for i in range(5):
        await asyncio.sleep(1)
        yield i
```

and its consumer:

```python
async for chunk in stream():
    await process(chunk)
```

The consumer controls the pace of iteration. It request a chunk, receives it, process it, and then requests the next one.  
If `process(chunk)` takes two seconds, the generator doesn't independently continue producing chunks in hte background. It resumes when the consumer requests the next item.  

This **pull-based streaming**: the consumer puls data from the source.

2- **Push-based streaming**

Imagine an external system that sends events to your application whenever new data becomes available. Your application does not explicitly request each individual event; the source delivers events to a callback, queue, or other receiving mechanism.

**Example**, a notification service might push incoming events to your application as they arrive.  
The source controls when new events are delivered, while your application must decide how to handle them.

Important distinction: Push-based doesn't automatically mean asynchronous, and pull-based doesn't automatically mean synchronous.  
These terms describe how data is delivered, not whether the code uses `async` and `await`.

**Durability and reliable message processing**  

**Example**: suppose an external service push 100 events per second, while the consumer can only process 20 per second  and the service cannot be slowed down.  

If the source cannot slow down and hte consumer is permanently slower; the system has a fundamental throughput mismatch.  
If the last few events are more important then we could use dropping data. A bounded queue with backpressure works only if the source can actually be slowed down or paused.  
If every event must be preserved and the source cannot pause, alternatives include durable storage, a message broker, or scaling up the consumer capacity. These approaches still require sufficient storage or processing capacity; no buffering strategy can eliminate a permanent rate mismatch for free.

**Durability**: means that the data is stored in a way that allows it to survive the relevant failures, such as an application crash or restart. That exact guarantees depend on how and where the data is stored.

**Example**, instead of keeping and important event only in RAM, an application could save it to a file or a database on persistent storage. After restarting, it could read the saved event and continue processing it.

This is the idea of **durable storage**: data isn't dependent solely on the lifetime of the python process.

Note: saving an event does not automatically mean it has been processed. Storage and processing are separate stages.

In python, when a process terminates, its in-memory queue disappears. if those events weren't saved somewhere else, they can't be recovered from that queue after a restart.

**Message broker**: an intermediary system that accepts messages from producers and makes them available to consumers.  
It allows producers and consumers to operate more independently, the producer doesn't necessarily need to wait for the consumer to precess each message before sending the next one.

**Example**s of message brokers: RabbitMQ and Apache Kafka.

Note: a broker doesn't automatically guarantee preservation under every failure.  
Its durability configuration, replication and acknowledgement behavior matter.  
Also if the consumer crashes after performing an operation but before acknowledging its message, that message may be delivered again.

- **Durability**: preserve messages across relevant failures.
- **Acknowledgements** (ACKs): Tell the broker that a message has been handled.
- **Idempotency**: Prevent repeated requests from producing repeated effects.

```text
Producer
(Publishes payment request)
        ↓
Durable message broker
(Retains messages and manages delivery)
        ↓
Consumer
(Receives and processes the request)
        ↓
Payment provider
(Executes the payment using an idempotency key)
        ↓
ACK to broker
(Sent after the consumer reaches the appropriate success point)
```

**Recall our scenario:** the producer generates 100 events per second, while the consumer process only 20 events per second. Every event matter, and the producer cannot pause.

Option A: unbounded `asyncio.Queue:

```text
Producer (100 events/sec)
        ↓
In-memory queue (+80 events/sec)
        ↓ 
Consumer (20 events/sec)
```

The queue preserves the events while the process is running, but memory usage grows continuously. If the process crashes, queued events are lost unless they were preserved elsewhere.

Option B: durable message broker:

```text
Producer (100 events/sec)
        ↓
Message broker
(Stores messages persistently and manages delivery , +80 events/sec)
        ↓ 
Consumer (20 events/sec)
```

The broker can preserve messages across consumer crashes and restarts, subject to its durability and delivery configuration.  
It also separates the producer and consumer into independently operating components.

**Notice:** The broker does not solve the throughput mismatch by itself. The backlog still grows by 80 events per second it changes where and how messages are stored, and how they survive failures.

---

### Common async mistake

#### Blocking the event loop accidentally

In **Example 1: async task with no suspension**:  

```python
async def task_a():
    print("A: started")
    time.sleep(3) # Doesn't suspend task A
    print("A: finished")

async def task_b():
    print("B: started")
    await asyncio.sleep(1)
    print("B: finished")

async def main():
    await asyncio.gather(task_a(),task_b())
```

`time.sleep(3)` does not suspend task a; it blocks the thread running the event loop.  
Even task B is ready to run it cannot start during that time.  
Only after the blocking sleep finished, task A prints `A: finished`. The event loop can then run task B, which prints `B: started` and awaits `asyncio.sleep(1)`.  
After task B's one-second asynchronous sleep, it prints `B:finished`.

**Example** suppose async FastAPI endpoint:

``` python
async def endpoint():
    result = calculate_something()
    return result
```

Assume `calculate_something` takes 3 seconds to execute and performs CPU-heavy computation without yielding control.  
This is CPU-bound synchronous function that runs for three seconds without yielding control will block the event-loop for those three seconds, even when called inside an `async def` function.

For CPU-heavy work, there are two common options:

- **Treads**: Run the work in a separate thread so the event-loop thread can continue. This can help responsiveness, although python GIL can limit parallel execution of CPU-bound python code.
- **Processes**: Run the work in another process, allowing CPU-bound python code to execute in parallel on multiple CPU cores.

So if we change that endpoint to:

```python
async def endpoint():
    result = await asyncio.to_thread(calculate_something)
    return result
```

While the CPU-heavy function is executing in the worker thread, the event loop can run other tasks on its own thread, thats because both run on 2 independent threads.

What happens:

1. The event loop executes `endpoint()`.
2. `await asyncio.to_thread(calculate_something) submits the synchronous function to a worker thread.
3. The endpoint's task suspends while waiting for the result.
4. The event loop's thread remains free to run other ready tasks.
5. After the computation finishes, the result becomes available, and the endpoint can resume.

**Important note:** The event loop isn't necessarily running another task continuously. It can run other ready tasks whenever scheduling permits.

#### Creating tasks without properly managing them

**In Example 1 Fire-and-Forget Task:**  

```python
async def save_result():
    print("Save: started")
    await asyncio.sleep(2)
    print("Save: completed")

async def main():
    task = asyncio.create_task(save_result())
    print("Main: completed")
```

`Save: completed` will not always be printed.  
After asyncio.create_task(save_result()), the new task is scheduled to run, but creating it doesn't mean it has already executed.  
Meanwhile, `main()` can finish immediately after printing `"Main: completed"`.

**What happens when `main()` finishes?**  
Calling `asyncio.create_task(save_result())` schedules a separate task. The task is owned by the event loop not owned by the life time of `main()` in the sense that it automatically finishes when `main()` finishes.  

In the Jupyter notebook:

- After `main()` finishes `await main()` return the control to the event loop.  
- The event loop continue to exist, so the background task may continue running.
- If the event loop shuts down, pending tasks my be cancelled during shutdown.

Therefore, the task might finish successfully after `main()` returns or it might not. The exact outcome depends on what happens next in the environment.

**Why is this risky in production?**  
Because the code has no explicit guarantee that the operation completes or that its failure is observed.  
If saving the result is essential, returning a successful response before the save completes could have application reporting success when the data was never persisted.

**In Example 2: Fire-and-Forget **Task**:  

```python
async def save_result():
    print("Save: started")
    await asyncio.sleep(2)
    print("Save: completed")

async def main():
    task = asyncio.create_task(save_result())
    print("Main: completed")
    return task
```

`print(task.done())` output `False` as at the moment `task.done()` is evaluated, the Task hasn't completed.

**Important distinction:** a task can outlive the coroutine that created it, but that doesn't guarantee it will outlive the event loop.

In endpoints that do behavior like save answer to database:  
It is better to use `await save_result()` that return only after the save finishes over `asyncio.create_task(save_result())` that return the response immediately.  
Because `await save_result()` establishes a **completion guarantee**: the end point won't proceed past that `await` until the save operation finishes successfully or raises an exception.

**In Example 3: await **task**:  

```python
async def save_result():
    print("Save: started")
    await asyncio.sleep(2)
    print("Save: completed")


async def main():
    task = asyncio.create_task(save_result()) 
    print("Main: waiting")
    await task # suspends main() until that task finishes
    print("Main: completed")

await main()
print(task.done())
```

Notice that creating a task and awaiting it are two separate decision. You can schedule work to run concurrently with other work, then wait for its result when it is necessary.

Also if `save_result()` raises an exception, `await task` propagates that exception to `main()`. The save failure won't simply be hidden from the caller.

#### Losing track of a task's exceptions

Suppose a background operation fails, but nobady awaits its task or retrieves its exception, Python's asyncio may eventually report a warning such as `Task exception was never retrieved`.

In **Example 1: task fails in the **background**:  

```python
async def background_work():
    await asyncio.sleep(1)
    raise ValueError("Something went wrong!")

async def main():
    asyncio.create_task(background_work())
    print("Main completed")
```

The `ValueError` won't automatically propagate out of `await main()` since `main()` does not await that task or other wise retrieve its exception, the exception won't automatically propagate through `await main()`.

#### Retrieving exceptions without awaiting immediately

Sometimes you want a task to run the background while other work proceeds. You may not want to await it immediately, but you still need to observe whether it succeeded or failed.  

Asyncio tasks provide methods as `task.done()` and `task.exception()` for inspecting their state.

In **Example 1: independent task failure**:  

```python
import asyncio

async def background_work():
    await asyncio.sleep(1)
    raise ValueError("Something went wrong!")

async def main():
    task = asyncio.create_task(background_work())

    await asyncio.sleep(2)

    print("Main continues")
    print(task.done())
    print(type(task.exception()).__name__)
```

The background task runs independently. If it raises `ValueError`, the failure does not automatically propagate into `main()`. The main coroutine can continue and finish normally.

In **Example 2: await the task**:  

```python
async def background_work():
    await asyncio.sleep(1)
    raise ValueError("Something went wrong!")

async def main():
    task = asyncio.create_task(background_work())

    await asyncio.sleep(2)
    await task

    print("Main continues")
    print(task.done())
    print(type(task.exception()).__name__)
```

We added `await task` so if background task raises `ValueError`, the exception propagates through `await task`.  
Unless we catch it, `main()` exist with that exception, and `Main continues` is never printed

So `await` does 2 important things:

1. It suspends the current coroutine until the awaited operation completes, allowing the event loop to run other tasks.
2. It delivers the awaited operation's result to the current coroutine, or propagates its exception into that coroutine.

Awaiting task doesn't create the error or make the task fail. The task fails independently; awaiting makes that failure propagate into the awaiting coroutine.

without awaiting, the failure remains in the background Task unless something else retrieves or handles it; with awaiting, the failure propagates to the caller

In **Example 3: Checking Task Completion and Exception Availability**:  

```python
async def main():
    task = asyncio.create_task(background_work())

    # Note there is no yielding control back to the event loop (await asyncio.sleep(2) )
    print(task.done()) 
    print(task.exception()) 
```

`asyncio.create_task()` schedules the coroutine; but it doesn't guarantee that the task executed.  
Since `main()` hasn't yielded control to the event loop, `background_work()` hasn't had an opportunity to finish.

At this point:

- `task.done()` returns `False`.
- `task.exception()` raises `asyncio.InvalidStateError` because the task hasn't finished yet.

Notice that `task.exception()` doesn't mean "tell me whether an exception might happen." it means "retrieve the exception from this completed task."

#### Assuming `async def` makes a function non-blocking automatically

Async functions can be blocked by having blocking calls such as `time.sleep()` inside asynchronous functions.

In **Example 1: blocking async function**:  

```python
import asyncio
import time

async def  fetch_data():
    time.sleep(2)
    print("data")


async def main():
    task = asyncio.create_task(fetch_data())
    await asyncio.sleep(0)
    print("Main continues")
await main()
```

#### Forgetting to await a coroutine  

In **Example 1: calling async function without await**:  

```python
async def fetch_data():
    print("Fetching data")
    return "data"

async def main():
    result = fetch_data()
    print(result)
```

When calling an `async def` function without `await`, you create a coroutine object but you don't execute the coroutine body.

In **Example 3: calling a function in different task**:  

```python
async def fetch_data():
    print("Fetching data")
    return "data"

async def main():
    result = asyncio.create_task(fetch_data())
    print(result)
```

When calling `asyncio.create_task(fetch_data())`, the coroutine is scheduled to run independently. It doesn't need to be awaited to start executing.

The `main()` does not yield control after creating the task. It prints the task representation and returns.  
The event loop then gets an opportunity to run the scheduled task so `"Fetching data"` will normally appear afterward.

Also `"data"` is not printed as `"data"` is returned value.  
while `"Fetching data"` will be printed because `print("Fetching data")` is executed inside the coroutine.

The distinction:

- calling `fetching_data()` alone creates a coroutine object.
- `asyncio.create_task(fetch_data())` schedules that coroutine to run. When it executes, `print("Fetching data")` displays the message, and `return "data"` supplies the string as the coroutine result.
- `await task` waits for the task to finish and retrieves that result, allowing you to assign it to a variable or print it.

#### Assuming `asyncio.gather()` automatically cancel all other operations when one fails

`asyncio.gather()` propagates the first ordinary exception it encounters to the awaiting coroutine immediately by default.  
It does not wait for all other awaitables to finish, and does not automatically cancel the remaining ones.  

It is important to distinct between the behavior of `asyncio.gather()` when a child coroutine is being cancelled and a child coroutine rasing an ordinary exception.

- Ordinary exception: `asyncio.gather()` propagates the first ordinary exception to its awaiter without automatically cancelling the other children.
- Child cancellation: `gather()` propagates CancelledError to its awaiter without automatically cancelling the other children.
- `return_exceptions=True`: Exceptions and child cancellations are returned as result entries.
- Gather cancellation: Cancelling `gather()` itself cancels unfinished submitted awaitables.