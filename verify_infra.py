# verify_infra.py
import sys
from openai import OpenAI
from config import settings

def execute_smoke_test():
    print("=" * 60)
    print(" ATIS INFRASTRUCTURE ALIGNMENT CHECK")
    print("=" * 60)
    print(f"[>] Target Endpoint : {settings.LLM_BASE_URL}")
    print(f"[>] Target Cluster  : {settings.LLM_MODEL}")
    print(f"[>] Key Initialized : {'YES (Length: ' + str(len(settings.LLM_API_KEY)) + ')' if settings.LLM_API_KEY != 'mock-key-or-env-variable' else 'NO [FALLBACK DETECTED]'}")
    print("-" * 60)

    if settings.LLM_API_KEY == 'mock-key-or-env-variable':
        print("[✗] Error: Your configuration layer failed to find your active API key.")
        print("    Ensure your .env file or local environment variables are correctly exported.")
        sys.exit(1)

    # Initialize the engine client using platform configurations
    client = OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL
    )

    try:
        print("[*] Dispatching system intent probe request to Cerebras backend...")
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a network verification entity. Respond only with JSON."},
                {"role": "user", "content": "Ping"}
            ],
            temperature=0.0,
            max_tokens=10
        )
        
        raw_output = response.choices[0].message.content
        print(f"[✔] Cluster Connection Succeeded.")
        print(f"[✔] Response Payload: {raw_output.strip()}")
        print("=" * 60)
        print("[SUCCESS] Environment and routing arrays are perfectly aligned. Safe to execute main.py.")
        print("=" * 60)

    except Exception as e:
        print("\n[✗] Critical Network/Authentication Failure:")
        print(f"    Details: {str(e)}")
        print("-" * 60)
        _suggest_diagnostics(e)
        sys.exit(1)

def _suggest_diagnostics(err):
    err_str = str(err).lower()
    if "411" in err_str or "401" in err_str or "unauthorized" in err_str:
        print("[DIAGNOSTIC] Authentication Denied. Check for typos in your API key value.")
    elif "404" in err_str or "model" in err_str:
        print(f"[DIAGNOSTIC] Model Name Target Mismatch. Verify that 'gpt-oss-120b' is active on your profile limits.")
    else:
        print("[DIAGNOSTIC] Validate localized firewall configurations or proxy rules blocking outbound TLS calls to api.cerebras.ai.")

if __name__ == "__main__":
    execute_smoke_test()