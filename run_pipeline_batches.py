import sys
import subprocess
import time

def run_batches(start, end, batch_size=20):
    current_start = start
    while current_start <= end:
        current_end = min(current_start + batch_size - 1, end)
        print(f"\n==================================================")
        print(f"Starting batch: lines {current_start} to {current_end}")
        print(f"==================================================")
        
        # Prepare the inputs for the interactive prompts
        inputs = f"{current_start}\n{current_end}\n"
        
        # Run audio_pipeline.py as a subprocess
        try:
            result = subprocess.run(
                [sys.executable, "audio_pipeline.py"],
                input=inputs,
                text=True,
                capture_output=False, # Let it print directly to stdout/stderr so we can monitor progress
            )
            if result.returncode != 0:
                print(f"Error: Batch {current_start}-{current_end} failed with return code {result.returncode}")
            else:
                print(f"Completed batch: lines {current_start} to {current_end}")
        except Exception as e:
            print(f"Exception occurred while running batch {current_start}-{current_end}: {e}")
            
        current_start = current_end + 1
        # Brief pause between batches
        time.sleep(2)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python run_pipeline_batches.py <start_line> <end_line> [batch_size]")
        sys.exit(1)
        
    try:
        start_line = int(sys.argv[1])
        end_line = int(sys.argv[2])
        batch_size = int(sys.argv[3]) if len(sys.argv) >= 4 else 20
    except ValueError:
        print("Error: Arguments must be integers.")
        sys.exit(1)
        
    if start_line > end_line:
        print("Error: Start line cannot be greater than end line.")
        sys.exit(1)
        
    print(f"Running audio pipeline from line {start_line} to {end_line} in batches of {batch_size}")
    run_batches(start_line, end_line, batch_size)
    print("\nAll batches completed!")
