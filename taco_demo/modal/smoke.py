import modal
app = modal.App("taco-smoke")
img = modal.Image.debian_slim().pip_install("torch")
@app.function(gpu="A10G", image=img, timeout=300)
def gpu_check():
    import subprocess, torch
    out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                         capture_output=True, text=True).stdout.strip()
    return f"gpu={out} | torch.cuda={torch.cuda.is_available()} dev={torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none'}"
@app.local_entrypoint()
def main():
    print("RESULT:", gpu_check.remote())
