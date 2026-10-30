import os
import logging
import time
from typing import Optional, Union
import torch

from transformers import AutoTokenizer, AutoModelForCausalLM

def load_model(model_checkpoint: str, hf_access_token: str, device: str = None) -> Union[AutoModelForCausalLM, None]:
    """Load the model from the checkpoint."""
    if not torch.cuda.is_available() or not torch.cuda.device_count():
        device = 'cpu'
        logging.warning('No CUDA device detected, using CPU, expect slower speeds.')
    elif device is None:
        device = 'cuda:0'

    if not hf_access_token:
        raise ValueError('Hugging Face access token needs to be specified.')

    model = AutoModelForCausalLM.from_pretrained(
        model_checkpoint,
        trust_remote_code=True
    )
    model.to(device).eval()

    return model

def generate_text(
    prompt: str,
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    device: str,
    max_length: int = 1024,
    assistant_model: Optional[AutoModelForCausalLM] = None,
    generate_kwargs: Optional[dict] = None,
) -> str:
    """Generate output given a prompt using a pre-loaded model."""
    tokenized_prompt = tokenizer(prompt, return_tensors="pt")
    tokenized_prompt = tokenized_prompt.to(device)
    attention_mask = tokenized_prompt["attention_mask"]
    stime = time.time()
    output_ids = model.generate(
        tokenized_prompt.input_ids,
        max_length=max_length,
        attention_mask = attention_mask,
        pad_token_id=tokenizer.pad_token_id,
        assistant_model=assistant_model,
        **(generate_kwargs if generate_kwargs else {}),
    )
    generation_time = time.time() - stime

    output_text = tokenizer.decode(
        output_ids[0].tolist(),
        skip_special_tokens=True
    )

    return output_text, generation_time

if __name__ == '__main__':
    model_checkpoint = "apple/OpenELM-3B-Instruct"
    hf_access_token = os.environ.get("HF_TOKEN", "")
    prompt = "data visualisation is "
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    tokenizer = AutoTokenizer.from_pretrained('meta-llama/Llama-2-7b-hf', token=hf_access_token)
    model = load_model(model_checkpoint, hf_access_token, device)

    output_text, generation_time = generate_text(
        prompt=prompt,
        model=model,
        tokenizer=tokenizer,
        device=device,
        max_length=256,  # specify the max length as needed
        # other optional parameters can be provided here
    )

    print_txt = (
        f'\n{"=" * os.get_terminal_size().columns}\n'
        '\033[1m Prompt + Generated Output\033[0m\n'
        f'{"-" * os.get_terminal_size().columns}\n'
        f'{output_text}\n'
        f'{"-" * os.get_terminal_size().columns}\n'
        f'\nGeneration took \033[1m\033[92m{round(generation_time, 2)}\033[0m seconds.\n'
    )
    print(print_txt)
