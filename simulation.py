# File: simulate_request_sending.py

import asyncio
import aiohttp
import random

prompts = [
    "用 c語言 寫一個 hello world",
    "寫一個 python 的小程式?",
    "冷氣要開幾度比較適合呢?",
    "一天要喝多少水比較健康?"
]

# Async function to send a single request
async def send_request(session, client_request, results):
    url = "http://localhost:8000/inference"  # Endpoint of the server
    try:
        print(f"Sending request: {client_request}")
        async with session.post(url, json={"request": client_request}) as response:
            if response.status == 200:
                data = await response.json()
                print(f"Received response: {data}")
                results.append(data)  # Save the response
            else:
                print(f"Error: Received status {response.status}, details: {await response.text()}")
    except aiohttp.ClientError as e:
        print(f"Client error: {e}")

# Async function to continuously send requests
async def send_requests(results):
    async with aiohttp.ClientSession() as session:
        while True:
            # Generate a random request
            client_request = prompts[random.randint(0, len(prompts)-1)]

            # Fire off the request asynchronously
            asyncio.create_task(send_request(session, client_request, results))

            # Random delay before sending the next request
            await asyncio.sleep(random.uniform(0.5, 1.0))  # Simulate delay between requests

# Function to handle responses asynchronously
async def process_responses(results):
    while True:
        # Check if there are responses to process
        if results:
            response = results.pop(0)  # Retrieve the next available response
            print(f"Processing response: {response}")
        else:
            await asyncio.sleep(0.1)  # Avoid busy waiting

# Main entry point to start both tasks
async def main():
    results = []  # Shared list to hold responses
    await asyncio.gather(
        send_requests(results),  # Task to send requests
        process_responses(results)  # Task to handle responses
    )

if __name__ == "__main__":
    asyncio.run(main())
