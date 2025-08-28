import argparse
import asyncio
import collections
import threading
import time

import httpx

try:
    import uvloop
except ImportError:
    uvloop = None

URL = "http://nginx:21000"


async def fetch(client: httpx.AsyncClient):
    """Performs HTTP GET request."""
    url = URL
    # The client timeout will handle request timeouts. For non-streaming requests,
    # http automatically reads the response body and releases the connection.
    await client.get(url)


async def worker(
    client: httpx.AsyncClient,
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
    async with httpx.AsyncClient(timeout=10) as client:
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


async def test(
    duration: int = 30,
    concurrency: int = 24,
) -> float:
    test_duration = duration  # seconds
    concurrency = concurrency
    print(f"Starting async test for {test_duration}s with a concurrency of {concurrency}...")

    success, failed, duration = await run_test(test_duration, concurrency)

    print("\n--- Test Results ---")
    print(f"Test ran for: {duration:.2f} seconds")
    print(f"Successful requests: {success}")
    print(f"Failed requests: {failed}")

    rps = 0.0
    if duration > 0:
        rps = success / duration
        print(f"Successful requests per second (RPS): {rps:.0f}")

    return rps


# Synchronous version
def sync_fetch(client: httpx.Client):
    """Performs HTTP GET request."""
    url = URL
    # The client timeout will handle request timeouts. For non-streaming requests,
    # httpx automatically reads the response body and releases the connection.
    client.get(url)


def sync_worker(
    client: httpx.Client,
    counters: collections.Counter,
    start_event: threading.Event,
    stop_event: threading.Event,
):
    """A worker that runs until stopped, performing requests and counting results."""
    start_event.wait()
    while not stop_event.is_set():
        try:
            sync_fetch(client)
            counters["success"] += 1
        except Exception:
            # Any exception is treated as a failure.
            counters["failed"] += 1


def sync_run_test(duration: int, concurrency: int):
    """Runs the workload for a specified duration and concurrency, and returns the results."""
    counters = collections.Counter()
    start_event = threading.Event()
    stop_event = threading.Event()

    # A timeout is set on the client, so individual requests will time out if they take too long.
    with httpx.Client(timeout=10) as client:
        # Create worker threads. They will wait for the start_event.
        threads = [
            threading.Thread(target=sync_worker, args=(client, counters, start_event, stop_event))
            for _ in range(concurrency)
        ]

        # Start all threads
        for thread in threads:
            thread.start()

        # All threads are created and waiting. Now, signal them to start and begin timing.
        start_event.set()
        start_time = time.monotonic()

        # Let the workers run for the specified duration.
        time.sleep(duration)

        # Signal all worker threads to stop.
        stop_event.set()

        # Wait for all threads to finish.
        for thread in threads:
            thread.join()

        end_time = time.monotonic()
        actual_duration = end_time - start_time
        return counters["success"], counters["failed"], actual_duration


def sync_test(
    duration: int = 30,
    concurrency: int = 24,
) -> float:
    test_duration = duration  # seconds
    concurrency = concurrency
    print(f"Starting sync test for {test_duration}s with a concurrency of {concurrency}...")

    success, failed, duration = sync_run_test(test_duration, concurrency)

    print("\n--- Test Results ---")
    print(f"Test ran for: {duration:.2f} seconds")
    print(f"Successful requests: {success}")
    print(f"Failed requests: {failed}")

    rps = 0.0
    if duration > 0:
        rps = success / duration
        print(f"Successful requests per second (RPS): {rps:.0f}")

    return rps


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HTTP performance test for httpx")
    parser.add_argument(
        "--mode", choices=["async", "sync"], default="async", help="Test mode: async or sync (default: async)"
    )
    parser.add_argument("--duration", type=int, default=10, help="Test duration in seconds (default: 10)")
    parser.add_argument("--concurrency", type=int, default=50, help="Concurrency level (default: 50)")

    args = parser.parse_args()

    if args.mode == "async":
        # Enable uvloop for better performance if available
        if uvloop is not None:
            uvloop.install()
            print("Using uvloop for enhanced performance")
        else:
            print("uvloop not available, using default asyncio event loop")

        rps = asyncio.run(test(duration=args.duration, concurrency=args.concurrency))
    else:
        # Sync mode
        rps = sync_test(duration=args.duration, concurrency=args.concurrency)
