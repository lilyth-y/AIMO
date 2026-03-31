from transformers import AutoTokenizer
model_name = "Qwen/Qwen2.5-Math-1.5B-Instruct"
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    print(f"Chat template: {tokenizer.chat_template}")
    messages = [{"role": "user", "content": "Hello"}]
    templated = tokenizer.apply_chat_template(messages, tokenize=False)
    print(f"Templated: {templated}")
except Exception as e:
    print(f"Error: {e}")
