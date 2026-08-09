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

**CPU-bound**: a task is CPU bounded when the processor is actively doing calculations.

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