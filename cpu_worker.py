def cpu_work(n: int) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total