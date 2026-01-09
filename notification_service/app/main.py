import os
import json
import asyncio
import aio_pika

from fastapi import FastAPI

app = FastAPI(title="Notification Service")

RABBIT_URL = os.getenv("RABBIT_URL")
BOOKING_QUEUE = os.getenv("BOOKING_QUEUE", "bookings_queue")


async def consume():
    connection = await aio_pika.connect_robust(RABBIT_URL)
    channel = await connection.channel()

    queue = await channel.declare_queue(BOOKING_QUEUE, durable=True)

    print(f"Waiting for messages on '{BOOKING_QUEUE}'...")

    async with queue.iterator() as q:
        async for message in q:
            async with message.process():
                data = json.loads(message.body)
                print("Received:", data)


@app.on_event("startup")
async def startup():
    print("Startup: consumer task starting...")
    asyncio.create_task(consume())


@app.get("/health")
def health():
    return {"status": "ok"}
