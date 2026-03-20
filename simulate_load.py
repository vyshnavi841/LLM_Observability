import random
import time
import os
from llm_app import LLMCallWrapper, MockLLMClient, LLMOpsLogger

def main():
    log_file = "logs.jsonl"
    if os.path.exists(log_file):
        os.remove(log_file) # Clean start
        print(f"Removed old {log_file}")
        
    client = MockLLMClient()
    logger = LLMOpsLogger(log_file=log_file)
    wrapper = LLMCallWrapper(client, logger)
    
    routes = ["summarize_article", "code_expert", "chat", "extraction"]
    users = ["user_1", "user_2", "user_42", "admin_01"]
    models = ["gpt-4o", "gpt-3.5-turbo", "claude-sonnet-4-20250514"]
    
    print("Starting load simulation (50+ requests)...")
    
    for i in range(1, 61): # Simulating 60 requests
        print(f"Sending Request {i}/60...", end=" ")
        
        # Randomize parameters
        route = random.choice(routes)
        user_id = random.choice(users)
        model = random.choice(models)
        
        # Randomize prompt length
        prompt_length = random.randint(10, 200)
        prompt = "word " * prompt_length
        
        # Decide the fate of this request
        # 70% normal success
        # 10% error
        # 5% short response
        # 10% refusal
        # 5% repetition
        chance = random.random()
        
        force_error = False
        force_short = False
        force_refusal = False
        force_repetition = False
        
        if chance < 0.10:
            force_error = True
        elif chance < 0.15:
            force_short = True
        elif chance < 0.25:
            force_refusal = True
        elif chance < 0.30:
            force_repetition = True
            
        # Add latency variability
        latency = random.uniform(0.1, 1.5)
        if random.random() < 0.05: # 5% chance of severe latency spike
            latency = random.uniform(3.0, 5.0)
            
        try:
            wrapper.generate(
                prompt=prompt,
                model=model,
                user_id=user_id,
                route=route,
                force_error=force_error,
                force_short=force_short,
                force_refusal=force_refusal,
                force_repetition=force_repetition,
                force_latency=latency
            )
            print("Success")
        except Exception as e:
            print(f"Failed ({str(e)})")
            
        # Sleep tight between calls to emulate real usage over a few seconds
        time.sleep(0.05)

    print("\nSimulation complete!")
    print(f"Logs written to {log_file}")

if __name__ == "__main__":
    main()
