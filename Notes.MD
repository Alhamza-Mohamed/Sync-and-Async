
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
    - [Timeouts.](#timeouts)
    - [Async generators and streaming](#async-generators-and-streaming)
    - [Context mangers](#context-mangers)
      - [Lifecycle of a `with` statement](#lifecycle-of-a-with-statement)

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

A task is CPU bounded when the processor is actively doing calculations. i.e. Tasks use the processor heavily.

Example:

- Training a neural network.
- Matrix multiplication.
- Image processing.
- Video encoding.
- Large numerical computations.

### I/O bound

Task that spend most of its time waiting for input or output.

Example:

- HTTP requests.
- Database queries.
- reading files.
- Writing files.
- communication with Redis.
- Querying a vector database.
- Calling an LLM API.'

The CPU does very little word. Most of the elapsed is waiting.

> Don't waste a scarce computational resource waiting for something that doesn't require that resource to be continuously occupied.  

Async/concurrency is especially valuable when work contains periods where it cannot make progress because it is waiting for something external. I.e it is very valuable with I/O bounded tasks not CPU bounded tasks.

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

Example:

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

Example

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

**Example on how even loop work:**

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

For example:

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

Because this is exactly what you are going to discover in your notebook. A coroutine can catch  `CancelledError`, perform cleanup, and potentially even suppress the cancellation.

`gather` with `cancel()`

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

### Timeouts.

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

**Backpressure** happens when the buffer reaches its limit and the producer must slow down or wait because the consumer cannot keep up.

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

### Context mangers

When you manually acquire resource:

```python
file = open("data.txt")

# use the file
data = file.read()

file.close()
```

The life cycle is acquire resource -> use it -> release resource.
The problem is what happens if something goes wrong while using it?

Example:

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

Example for a file, if you do `f = open("data.txt")` python doesn't merely create a python object. It asks the operating system to open the file and gives your process access to that OS-level resource.  

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

Example: 2 tasks (A,B) accessing the same shared variable `balance = 100` task A: withdraw 80, task B: withdraw 50. Without some coordination both could observe `balance = 100` and before either one updates it they both read it in the same time resulting in a wrong final value calculation:

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
