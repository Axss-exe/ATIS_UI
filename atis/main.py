# atis/main.py
import sys
import logging
from atis.orchestrator.compiler_orchestrator import AtisCompilerOrchestrator

# Configure high-scannability terminal logging layout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
# Keep operational networking dependencies quiet
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

def main():
    # Fallback to default check if no CLI arguments are supplied
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Which Chinese state-backed companies own lithium assets in Masvingo and who regulates them?"

    print("=" * 60)
    print(" ATIS ENGINE RUNTIME EXECUTION FRAME")
    print("=" * 60)
    
    try:
        orchestrator = AtisCompilerOrchestrator()
        payload = orchestrator.compile(query)
        
        print("\n" + "=" * 60)
        print(" COMPILED INTELLIGENCE REPORT")
        print("=" * 60)
        print(payload["report"])
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[✗] Critical Engine Panic: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()