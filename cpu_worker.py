def cpu_work(n: int) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total

def process_document(document_id: int) -> int:

    total = 0

    for i in range(100):
        total += i * i 

        print(f"Processed document: {document_id}")

    return document_id


