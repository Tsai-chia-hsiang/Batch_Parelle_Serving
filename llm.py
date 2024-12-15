import numpy as np
import torch
import asyncio

async def llm_inference(req:list[str]):
    await asyncio.sleep(2) # simulation
    return [f"Infer {r}" for r in req]