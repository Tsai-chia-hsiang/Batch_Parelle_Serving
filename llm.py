import numpy as np
import torch
import asyncio
from typing import Literal
import os
from pathlib import Path
from time import time
import os.path as osp
from transformers import (
    LlamaForCausalLM, AutoTokenizer,
    PreTrainedTokenizer, PreTrainedTokenizerFast
)
WORKING_DIR = str(Path(osp.abspath(__file__)).parent)

class LLama_Namespace():
    
    SUPPORT_LLAMA ={
        'meta':osp.join(WORKING_DIR, "Meta-Llama-3-8B-Instruct"),
        'tw': osp.join(WORKING_DIR, "Llama3-TAIDE-LX-8B-Chat-Alpha1")
    }

    def __init__(self, use_model:Literal['meta', 'tw']):
        self.use_model = use_model
        self.proj_dir:os.PathLike = LLama_Namespace.SUPPORT_LLAMA[use_model]
        self.model:LlamaForCausalLM = None
        self.tokenizer:PreTrainedTokenizer | PreTrainedTokenizerFast = None
    
    def load(self, dev:torch.device=torch.device('cuda:0')):        
        
        if self.model is None:
            self.model = LlamaForCausalLM.from_pretrained(self.proj_dir , torch_dtype=torch.bfloat16)
            self.model = self.model.to(dev)
            self.tokenizer = AutoTokenizer.from_pretrained(self.proj_dir)
            if self.use_model == 'meta' :
                self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.padding_side = "left"


class Llama_Inference_Wrapper():
    
    support_pretrained_models = {k:LLama_Namespace(use_model=k) for k in LLama_Namespace.SUPPORT_LLAMA}
    
    def __init__(self, use_model:Literal['meta', 'tw']='meta', dev:torch.device=torch.device('cuda:0')):
        self.use_model = use_model
        self.dev = dev
        Llama_Inference_Wrapper.support_pretrained_models[self.use_model].load(dev=self.dev)
    
    def _t_and_g(self, batch_prompts:list[str], max_out:int=256) -> list[str]:
        
        inputs = Llama_Inference_Wrapper.support_pretrained_models[self.use_model].tokenizer(
           batch_prompts, return_tensors='pt', padding=True
        ).to(self.dev)
        
        gen_ids = Llama_Inference_Wrapper.support_pretrained_models[self.use_model].model.generate(
            inputs.input_ids, max_new_tokens=max_out, 
            attention_mask=inputs.attention_mask
        )

        r =  [
            Llama_Inference_Wrapper.support_pretrained_models[self.use_model].tokenizer.decode(
                gi[inputs.input_ids.size(-1):], skip_special_tokens=True, clean_up_tokenization_spaces=True
            ).lstrip().strip()
            
            for gi in gen_ids
        ]
        return r

    async def __call__(self, batch_prompts:list[str], max_out:int=256) -> list[int]:
        
        results = await asyncio.to_thread(self._t_and_g, batch_prompts, max_out)
        return results


async def unit_test():
    
    prompts =[
        "用 c語言 寫一個 hello world",
        "寫一個 python 的小程式?",
        "冷氣要開幾度比較適合呢?",
        "一天要喝多少水比較健康?"
    ]
    meta_llama = Llama_Inference_Wrapper(use_model='tw')
    respond = await meta_llama(batch_prompts=prompts, max_out=256)
    for r in respond:
        print(r)
        print("="*40)
    
if __name__ == "__main__":
    asyncio.run( unit_test() )
