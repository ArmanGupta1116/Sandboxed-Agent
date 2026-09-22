from transformers import AutoTokenizer, AutoModelForCausalLM


MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"


class LocalModel:
    def __init__(self):
        print("Loading tokenizer...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID,
            local_files_only=True,
        )

        print("Loading model...")

        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            local_files_only=True,
        )

        self.model.eval()

    def generate(
        self,
        messages: list[dict],
        max_new_tokens: int = 512,
    ) -> str:

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
        )

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
        )

        generated = outputs[0][inputs["input_ids"].shape[1]:]

        return self.tokenizer.decode(
            generated,
            skip_special_tokens=True,
        )