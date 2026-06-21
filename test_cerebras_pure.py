# test_cerebras_pure.py
import os
import json
import urllib.request
import urllib.error

def load_env_manually():
    env = {}
    if not os.path.exists(".env"):
        print("[✗] Error: No .env file found in this directory!")
        return env
    
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            # Strip quotes and spacing
            env[key.strip()] = val.strip().strip('"').strip("'")
    return env

def test_connection():
    print("=" * 60)
    print(" CEREBRAS .ENV PURE CONNECTION TEST")
    print("=" * 60)
    
    env = load_env_manually()
    
    # Check both potential key naming patterns
    api_key = env.get("ATIS_LLM_API_KEY") or env.get("CEREBRAS_API_KEY")
    api_url = env.get("ATIS_LLM_BASE_URL") or env.get("API_URL") or "https://api.cerebras.ai/v1/chat/completions"
    model = env.get("ATIS_LLM_MODEL") or env.get("MODEL") or "gpt-oss-120b"
    
    # Fix URL pathing if it's just the base domain
    if not api_url.endswith("/chat/completions"):
        api_url = api_url.rstrip("/") + "/chat/completions"
        
    print(f"[*] Loaded URL  : {api_url}")
    print(f"[*] Loaded Model: {model}")
    print(f"[*] Key Found   : {'YES' if api_key else 'NO'}")
    print("-" * 60)
    
    if not api_key:
        print("[✗] Action Required: Ensure your .env file has your key specified as:")
        print("    ATIS_LLM_API_KEY=your_key_here")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Say 'Cerebras Alignment Confirmed' and nothing else."}
        ],
        "temperature": 0.0
    }
    
    req = urllib.request.Request(
        api_url, 
        data=json.dumps(payload).encode("utf-8"), 
        headers=headers, 
        method="POST"
    )
    
    try:
        print("[*] Sending secure HTTP POST frame directly to Cerebras backend...")
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode("utf-8")
            data = json.loads(res_body)
            answer = data["choices"][0]["message"]["content"]
            print(f"\n[✔] Success! Remote cluster output: {answer.strip()}")
            print("=" * 60)
            print("[STATUS] Your .env file and network path are perfectly configured.")
            print("=" * 60)
    except urllib.error.HTTPError as e:
        print(f"\n[✗] API Connection Refused (HTTP Error {e.code})")
        try:
            error_details = json.loads(e.read().decode("utf-8"))
            print(f"    Details: {json.dumps(error_details, indent=2)}")
        except Exception:
            print(f"    Reason : {e.reason}")
    except Exception as e:
        print(f"\n[✗] Network/System Exception Encountered: {str(e)}")

if __name__ == "__main__":
    test_connection()