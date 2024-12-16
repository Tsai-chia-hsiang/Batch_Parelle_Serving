from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from contextlib import asynccontextmanager
import uvicorn
from llm import Llama_Inference_Wrapper
import os
LLM = None 
if os.getenv("RUN_MAIN") == "true":  # RUN_MAIN is set only in the worker process
    LLM = Llama_Inference_Wrapper()

# Asynchronous queues for pending requests and responses
pending_Q = asyncio.Queue()
finished_Q = asyncio.Queue()

# Schema for incoming requests
class InferenceRequest(BaseModel):
    request: str  # Single request instead of batch

# Global request ID counter
request_id_counter = 0

# Background task to process requests from the pending queue
async def process_requests_from_queue(app: FastAPI):
    
    try:
        while True:
            batch = []
            batch_ids = []

            # Dequeue up to 4 items
            for _ in range(4):
                if not pending_Q.empty():
                    request_id, req = await pending_Q.get()
                    batch.append(req)
                    batch_ids.append(request_id)

            if batch:
      
                results = await app.state.LLM (batch)

                # Add results to the finished queue
                for request_id, result in zip(batch_ids, results):
                    await finished_Q.put((request_id, result))

            await asyncio.sleep(0.1)  # Avoid busy looping
    except asyncio.CancelledError:
        print("process_requests_from_queue task cancelled. Cleaning up...")

# Background task to pop results from finished_Q and respond to clients
async def return_responses_to_clients(app: FastAPI):
    try:
        while True:
            if not finished_Q.empty():
                request_id, result = await finished_Q.get()

                # Resolve the corresponding response future
                if request_id in app.state.response_futures:
                    app.state.response_futures[request_id].set_result(result)
                else:
                    print(f"Warning: No client waiting for request_id {request_id}")

            await asyncio.sleep(0.1)  # Avoid busy looping
    except asyncio.CancelledError:
        print("return_responses_to_clients task cancelled. Cleaning up...")

# Define a lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting server...")
    # Start background tasks for request processing and response handling
    app.state.LLM = Llama_Inference_Wrapper(use_model="tw")
    app.state.processing_task = asyncio.create_task(process_requests_from_queue(app))
    app.state.response_task = asyncio.create_task(return_responses_to_clients(app))
    app.state.response_futures = {}
    try:
        yield  # Let the server run
    finally:
        print("Stopping server...")
        # Cancel background tasks on shutdown
        app.state.processing_task.cancel()
        app.state.response_task.cancel()
        try:
            await app.state.processing_task
            await app.state.response_task
        except asyncio.CancelledError:
            pass  # Gracefully handle task cancellation

# Initialize FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)
app.state.response_futures = {}

@app.post("/inference")
async def enqueue_request(request: InferenceRequest):
    global request_id_counter

    # Increment the request ID
    request_id_counter += 1
    request_id = request_id_counter
    
    # Create a future to hold the result for this request
    loop = asyncio.get_event_loop()
    response_future = loop.create_future()
    app.state.response_futures[request_id] = response_future

    # Add the request to the pending queue
    await pending_Q.put((request_id, request.request))

    # Wait for the result asynchronously
    result = await response_future

    # Cleanup the response future
    del app.state.response_futures[request_id]

    return {"request_id": request_id, "content": result}

# Run the server with Uvicorn
if __name__ == "__main__":
    
    uvicorn.run("server_with_queue:app", host="0.0.0.0", port=8000, reload=True)
