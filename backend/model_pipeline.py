import os
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
import torch.nn as nn
import time
from generate_openelm import load_model, generate_text

class LLMModel:
    def __init__(
        self,
        # checkpoint_num,
        llm_checkpoint,
        half_precision=True,
        llm_device=torch.device("cuda:0"),
        inference_device = torch.device("cuda:0")
    ):
        """
        LLM Model class.
        This class initializes the LLM model and tokenizer.
        """
        self.llm_device = llm_device
        self.inference_device = inference_device
        # self.checkpoint_num = checkpoint_num
        self.llm_checkpoint = llm_checkpoint

        if llm_checkpoint=="apple/OpenELM-3B":
            print("loading tokenizer")

            self.llm_tokenizer = AutoTokenizer.from_pretrained('meta-llama/Llama-2-7b-hf', token=os.environ.get("HF_TOKEN", ""))
            print("loading the model...............................")
            self.llm = load_model(model_checkpoint=llm_checkpoint, hf_access_token=os.environ.get("HF_TOKEN", ""), device=self.llm_device)
            print("model loading finished")
        elif llm_checkpoint=="tiiuae/falcon-7b":
            llm_tokenizer_checkpoint = llm_checkpoint
            print("loading tokenizer")
            self.llm_tokenizer = AutoTokenizer.from_pretrained(llm_tokenizer_checkpoint, torch_dtype=torch.float16)
            print("loading the model...............................")
            print(f"checkpoint selected is: {llm_checkpoint}")
            self.llm = AutoModelForCausalLM.from_pretrained(llm_checkpoint, torch_dtype=torch.float16).to(self.llm_device)
            print("model loading finished")
        elif llm_checkpoint == "meta-llama/Meta-Llama-3-8B-Instruct":
            llm_tokenizer_checkpoint = llm_checkpoint
            print("loading tokenizer")
            self.llm_tokenizer = AutoTokenizer.from_pretrained(llm_tokenizer_checkpoint, device_map="auto", torch_dtype=torch.float16)
            print("loading the model...............................")
            print(f"checkpoint selected is: {llm_checkpoint}")
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
                )
            self.llm = AutoModelForCausalLM.from_pretrained(llm_checkpoint,device_map="cuda",quantization_config=bnb_config, torch_dtype=torch.float16)
            print("model loading finished")
        else:
            llm_tokenizer_checkpoint = llm_checkpoint
            print("loading tokenizer..")
            self.llm_tokenizer = AutoTokenizer.from_pretrained(llm_tokenizer_checkpoint, torch_dtype=torch.float16)
            print("loading the model...............................")
            print(f"checkpoint selected is: {llm_checkpoint}")
            self.llm = AutoModelForCausalLM.from_pretrained(llm_checkpoint, torch_dtype=torch.float16).to(self.llm_device)
            print("model loading finished")
        # if half_precision:
        #     self.llm = self.llm.half()
        # self.llm = self.llm.to(llm_device)



    def lama_inference(self, 
        prompt, 
        min_new_tokens=20, 
        max_new_tokens=600, 
        llm_max_length=8192,
        inference_device=None):

        inference_device = self.inference_device or self.llm_device
        
        terminators = [
            self.llm_tokenizer.eos_token_id,
            self.llm_tokenizer.convert_tokens_to_ids("<|eot_id|>")]
        
        # terminators = self.llm_tokenizer.eos_token_id

        input_ids = self.llm_tokenizer.apply_chat_template(prompt,add_generation_prompt=False,return_tensors="pt").to(inference_device)
        input_length = input_ids.size(1)
        # attention_mask = input_ids.attention_mask.to(self.llm_device)
        generated_ids = self.llm.generate(
            input_ids=input_ids, 
            # attention_mask=attention_mask, 
            eos_token_id = terminators, 
            min_length=input_length + min_new_tokens, 
            max_length=input_length + max_new_tokens, 
            do_sample=True,
            pad_token_id = self.llm_tokenizer.eos_token_id,
            temperature=0.2,
            top_p=0.9,
        )
            
        generated_text = self.llm_tokenizer.decode(generated_ids[0][input_ids.shape[-1]:], skip_special_tokens=True)
        
        return generated_text

    def mistral_inference(self, 
        prompt, 
        min_new_tokens=20, 
        max_new_tokens=200, 
        llm_max_length=4096):
        
        self.llm_tokenizer.pad_token = self.llm_tokenizer.eos_token

        model_input = self.llm_tokenizer(prompt, truncation=True, padding=True, max_length=llm_max_length, return_tensors="pt")
        input_ids = model_input.input_ids.to(self.llm_device)
        input_length = input_ids.size(1)
        attention_mask = model_input.attention_mask.to(self.llm_device)

        generated_ids = self.llm.generate(
            input_ids=input_ids, 
            attention_mask=attention_mask, 
            min_new_tokens=min_new_tokens, 
            max_new_tokens=max_new_tokens, 
            do_sample=True
        )

        generated_text = self.llm_tokenizer.decode(generated_ids[0][input_length:], skip_special_tokens=False)
        return generated_text

    def falcon_inference(self, 
        prompt,
        llm_max_length=1024):
 
        self.llm_tokenizer.pad_token = self.llm_tokenizer.eos_token

        model_input = self.llm_tokenizer(prompt, truncation=True, padding=True, max_length=llm_max_length, return_tensors="pt")
        input_ids = model_input.input_ids.to(self.llm_device)
        input_length = input_ids.size(1)
        attention_mask = model_input.attention_mask.to(self.llm_device)

        generated_ids = self.llm.generate(
            input_ids=input_ids, 
            attention_mask=attention_mask, 
            max_length=llm_max_length, 
            do_sample=True,
            temperature=0.9,
            # top_k=10,
            # num_return_sequences=1,
            # repetition_penalty=1.2,
            eos_token_id=self.llm_tokenizer.eos_token_id

        )

        generated_text = self.llm_tokenizer.decode(generated_ids[0][input_length:], skip_special_tokens=False)
        return generated_text



    def Openelm_inference(self,
        prompt,
        device = "cuda:0"):
        repetition_penalty=1.9
        generate_kwargs = {"repetition_penalty": repetition_penalty}
        # Call the generate function
        output_text, generation_time = generate_text(
        prompt=prompt,
        model=self.llm,
        tokenizer=self.llm_tokenizer,
        device=device,
        generate_kwargs=generate_kwargs,
        max_length=2048)

        return output_text