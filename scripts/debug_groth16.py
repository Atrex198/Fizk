from time import perf_counter
import sys
from pathlib import Path
import numpy as np

# Ensure project src is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.zkp_techniques.groth16_real import Groth16Wrapper

print('=== Groth16 debug test ===')
try:
    g = Groth16Wrapper()
    print('Calling setup()...')
    g.setup(32)
    print('Setup done')

    # Create a small deterministic witness likely to satisfy simple matrix-mul circuit
    witness = np.arange(1, 17).reshape((4,4)).astype(float)
    print('Witness:', witness)

    start = perf_counter()
    proof_struct = g.generate_proof(None, witness, 'matrix_mult')
    gen_time = (perf_counter() - start) * 1000
    # Try to get proof size
    proof_bytes = getattr(proof_struct, 'proof', proof_struct)
    try:
        size = len(proof_bytes)
    except Exception:
        size = 'unknown'
    print(f'Proof generated: size={size}, gen_time={gen_time:.2f} ms')

    start = perf_counter()
    try:
        ok = g.verify_proof(proof_bytes, None)
    except Exception as e:
        print('Verification exception:', repr(e))
        ok = False
    verf_time = (perf_counter() - start) * 1000
    print(f'Verification result: {ok}, time={verf_time:.2f} ms')

    if hasattr(proof_bytes, 'hex'):
        print('Proof (hex prefix):', proof_bytes.hex()[:160])
    else:
        try:
            print('Proof prefix bytes:', proof_bytes[:32])
        except Exception:
            pass
except Exception as e:
    print('Groth16 test failed:', repr(e))
