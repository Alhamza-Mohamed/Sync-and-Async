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

---

### CPU-bound vs I/O bound

**CPU-bound**: a task is CPU bounded when the processor is actively doing calculations. i.e. Tasks use the processor heavily.

Example:

- Training a neural network.
- Matrix multiplication.
- Image processing.
- Video encoding.
- Large numerical computations.

**I/O bound**: task that spend most of its time waiting for input or output.

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

---

### Concurrency and parallelism

**Concurrency:** The ability of a system to make progress on multiple tasks during overlapping periods of time, by switching between tasks when appropriate. example if A waits for the database while B runs, A and B are progressing concurrently.  

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

**Parallelism:** Multiple pieces of work are actually executing simultaneously, typically on different CPU cores.  

