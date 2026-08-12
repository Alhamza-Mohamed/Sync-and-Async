# Sync and Async

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

### Event loop

The component that is responsible for managing the coroutines.  

The event loop is the mechanism that enables cooperative concurrency in async programs. It runs on a thread and manages multiple coroutines/tasks.  

A task runs until it reaches an `await` point where it cannot make progress, then it yields control back to the event loop.  The event loop can then give the execution opportunity to another ready task.

THe scheduling is **cooperative** because the event loop does not forcibly interrupt a running task. The task must reach a point where it yields control,  typically through `await`.

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

