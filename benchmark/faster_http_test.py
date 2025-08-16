import asyncio
import collections
import multiprocessing
import time

try:
    import uvloop
except ImportError:
    uvloop = None

import faster_http as http

URL = "http://nginx:21000"


async def fetch(client: http.AsyncClient):
    """Performs a single HTTP GET request."""
    url = URL
    # The client timeout will handle request timeouts. For non-streaming requests,
    # http automatically reads the response body and releases the connection.
    await client.get(url)


async def worker(
    client: http.AsyncClient,
    counters: collections.Counter,
    start_event: asyncio.Event,
):
    """A worker that runs until cancelled, performing requests and counting results."""
    await start_event.wait()
    while True:
        try:
            await fetch(client)
            counters["success"] += 1
        except asyncio.CancelledError:
            # The task was cancelled, which is the signal to stop.
            break
        except Exception:
            # Any other exception is treated as a failure.
            counters["failed"] += 1


async def run_test(duration: int, concurrency: int):
    """Runs the workload for a specified duration and concurrency, and returns the results."""
    counters = collections.Counter()
    start_event = asyncio.Event()

    # A timeout is set on the client, so individual requests will time out if they take too long.
    async with http.AsyncClient(timeout=10) as client:
        # Create worker tasks. They will wait for the start_event.
        tasks = [asyncio.create_task(worker(client, counters, start_event)) for _ in range(concurrency)]

        # All tasks are created and waiting. Now, signal them to start and begin timing.
        start_event.set()
        start_time = time.monotonic()

        # Let the workers run for the specified duration.
        await asyncio.sleep(duration)

        # Cancel all worker tasks to stop them gracefully.
        for task in tasks:
            task.cancel()

        # Wait for all tasks to finish their cancellation.
        await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.monotonic()
        actual_duration = end_time - start_time
        return counters["success"], counters["failed"], actual_duration


async def single_core_test(
    duration: int = 30,
    concurrency: int = 24,
) -> float:
    test_duration = duration  # seconds
    concurrency = concurrency
    print(f"Starting single-core test for {test_duration}s with a concurrency of {concurrency}...")

    success, failed, duration = await run_test(test_duration, concurrency)

    print("\n--- Single-Core Test Results ---")
    print(f"Test ran for: {duration:.2f} seconds")
    print(f"Successful requests: {success}")
    print(f"Failed requests: {failed}")

    rps = 0.0
    if duration > 0:
        rps = success / duration
        print(f"Successful requests per second (RPS): {rps:.0f}")

    return rps


def process_worker(result_queue: multiprocessing.Queue, duration: int, concurrency: int):
    """The target function for each process in the multi-core test."""
    # Enable uvloop for this process if available
    if uvloop is not None:
        uvloop.install()
    success, failed, actual_duration = asyncio.run(run_test(duration, concurrency))
    result_queue.put((success, failed, actual_duration))


if __name__ == "__main__":
    # Enable uvloop for better performance if available
    if uvloop is not None:
        uvloop.install()
        print("Using uvloop for enhanced performance")
    else:
        print("uvloop not available, using default asyncio event loop")

    single_rps = asyncio.run(single_core_test(duration=10, concurrency=50))
