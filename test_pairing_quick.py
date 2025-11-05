"""
Quick Pairing Verification Test
================================
Fast test with minimal SRS for quick verification that pairing is enabled.
"""

import sys
import os
import time

# CRITICAL: Force unbuffered output so prints appear immediately in terminal
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
os.environ['PYTHONUNBUFFERED'] = '1'

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

print("\n" + "="*80, flush=True)
print("QUICK PAIRING VERIFICATION TEST", flush=True)
print("="*80, flush=True)
print(f"Start time: {time.strftime('%H:%M:%S')}\n", flush=True)

# Import dependencies
import numpy as np
from zkp_protocols.protostar_production import ProductionProtostar
from py_ecc.bn128 import curve_order

print("[1/5] Creating protocol with minimum security (128-bit)...", flush=True)
# Use minimum allowed security level
protocol = ProductionProtostar(security_level=128)
print("      [OK] Protocol created", flush=True)

print("\n[2/5] Running setup (this will take 2-3 minutes for 4096 SRS elements)...", flush=True)
print("      NOTE: Progress updates will appear every 256 elements", flush=True)
print("      This is cryptographically required - please wait...", flush=True)
sys.stdout.flush()
start = time.time()
setup_params = protocol.setup()
print(f"\n      [OK] Setup done in {time.time()-start:.1f}s - {setup_params['srs_size']} elements\n", flush=True)

print("[3/5] Generating simple proof...", flush=True)
witness = np.array([1, 2, 3, 4, 5], dtype=int)
public_inputs = np.array([10, 20], dtype=int)
print(f"      Using witness: {witness}", flush=True)
print(f"      Using public inputs: {public_inputs}", flush=True)
sys.stdout.flush()

start = time.time()
proof = protocol.prove(statement=None, witness=witness, public_inputs=public_inputs)
print(f"      [OK] Proof generated in {time.time()-start:.2f}s\n", flush=True)

print("[4/5] Verifying proof (checking pairing verification)...", flush=True)
sys.stdout.flush()
start = time.time()
result = protocol.verify(proof=proof, statement=None, public_inputs=public_inputs)
verify_time = time.time()-start

print(f"      [OK] Verification done in {verify_time:.3f}s", flush=True)
print(f"      Valid: {result.is_valid}", flush=True)
print(f"      Message: {result.message}\n", flush=True)

# Check pairing status
pairing_enabled = False
if hasattr(result, 'details') and result.details and 'pairing_checks' in result.details:
    pairing_status = result.details['pairing_checks'].get('pairing_verification_status', 'unknown')
    
    print("="*80, flush=True)
    print("PAIRING VERIFICATION STATUS:", flush=True)
    print("="*80, flush=True)
    print(f"Status: {pairing_status}", flush=True)
    
    if result.details['pairing_checks']:
        for key, value in result.details['pairing_checks'].items():
            print(f"  - {key}: {value}", flush=True)
    
    if pairing_status == 'enabled':
        print("\n[SUCCESS] Pairing verification IS PROPERLY ENABLED!", flush=True)
        pairing_enabled = True
    else:
        print(f"\n[FAIL] Pairing verification is NOT enabled (status: {pairing_status})", flush=True)
    print("="*80 + "\n", flush=True)
else:
    print("[WARNING] No pairing check details found in verification result\n", flush=True)

print("[5/5] Testing tampered proof rejection...", flush=True)
tampered_proof = proof.copy()
if 'witness_commitment' in tampered_proof and isinstance(tampered_proof['witness_commitment'], dict):
    if 'point_coords' in tampered_proof['witness_commitment']:
        coords = tampered_proof['witness_commitment']['point_coords']
        if len(coords) > 0:
            orig_coord = str(coords[0])
            coords[0] = str((int(str(coords[0])) + 99999) % curve_order)
            print(f"      Tampering witness commitment: {orig_coord[:20]}... -> {coords[0][:20]}...", flush=True)
sys.stdout.flush()

result_tampered = protocol.verify(proof=tampered_proof, statement=None, public_inputs=public_inputs)

print(f"      Tampered proof valid: {result_tampered.is_valid}", flush=True)
if not result_tampered.is_valid:
    print(f"      [SUCCESS] Tampered proof correctly rejected!", flush=True)
else:
    print(f"      [FAIL] Tampered proof was accepted (security issue!)", flush=True)

print("\n" + "="*80, flush=True)
print("FINAL RESULT:", flush=True)
print("="*80, flush=True)

tests_passed = 0
tests_total = 3

if result.is_valid:
    print("[PASS] Valid proof verification", flush=True)
    tests_passed += 1
else:
    print("[FAIL] Valid proof verification", flush=True)

if pairing_enabled:
    print("[PASS] Pairing verification enabled", flush=True)
    tests_passed += 1
else:
    print("[FAIL] Pairing verification enabled", flush=True)

if not result_tampered.is_valid:
    print("[PASS] Tampered proof rejection", flush=True)
    tests_passed += 1
else:
    print("[FAIL] Tampered proof rejection", flush=True)

print(f"\nScore: {tests_passed}/{tests_total}", flush=True)
print(f"End time: {time.strftime('%H:%M:%S')}", flush=True)

if tests_passed == tests_total:
    print("\n" + "="*80, flush=True)
    print("[SUCCESS] ALL TESTS PASSED - SYSTEM IS 100% PROPER!", flush=True)
    print("Pairing verification is working correctly.", flush=True)
    print("="*80 + "\n", flush=True)
    sys.exit(0)
else:
    print(f"\n[WARNING] {tests_total-tests_passed} test(s) failed\n", flush=True)
    sys.exit(1)
