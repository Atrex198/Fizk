"""
Comprehensive Pairing Verification Test
========================================
Tests that pairing verification is properly enabled in the ZKP system.
Checks all function calls, inputs, and outputs properly.
"""

import sys
import os
import time
import hashlib

# CRITICAL: Force unbuffered output so prints appear immediately
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
os.environ['PYTHONUNBUFFERED'] = '1'

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

print("\n" + "="*80, flush=True)
print("COMPREHENSIVE PAIRING VERIFICATION TEST", flush=True)
print("="*80, flush=True)
print(f"Start time: {time.strftime('%H:%M:%S')}\n", flush=True)

try:
    # Step 1: Import all required modules
    print("[1/7] Importing modules...", flush=True)
    print("      Importing numpy...", flush=True)
    import numpy as np
    print("      Importing torch...", flush=True)
    import torch
    import torch.nn as nn
    print("      Importing zkp_protocols...", flush=True)
    from zkp_protocols.protostar_production import ProductionProtostar
    from zkp_protocols.base import TrainingStatement, TrainingWitness, ProtocolType
    print("      Importing py_ecc...", flush=True)
    from py_ecc.bn128 import curve_order
    print("      [OK] All imports successful", flush=True)
    
    # Step 2: Create minimal model for testing
    print("\n[2/7] Creating minimal neural network model...", flush=True)
    
    class TinyModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(2, 2)
            self.fc2 = nn.Linear(2, 1)
        
        def forward(self, x):
            x = torch.relu(self.fc1(x))
            return self.fc2(x)
    
    model = TinyModel()
    print(f"      [OK] Model created: 2 -> 2 -> 1", flush=True)
    
    # Get initial weights
    initial_weights = {name: param.detach().cpu().numpy() 
                      for name, param in model.named_parameters()}
    print(f"      [OK] Initial weights extracted: {len(initial_weights)} parameters", flush=True)
    
    # Step 3: Create dummy training data
    print("\n[3/7] Creating training data...", flush=True)
    X_data = np.random.randn(4, 2).astype(np.float32)
    y_data = np.random.randn(4, 1).astype(np.float32)
    print(f"      [OK] Training data: X={X_data.shape}, y={y_data.shape}", flush=True)
    
    # Step 4: Perform one training step
    print("\n[4/7] Performing one training step...", flush=True)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    
    X_tensor = torch.from_numpy(X_data)
    y_tensor = torch.from_numpy(y_data)
    
    optimizer.zero_grad()
    output = model(X_tensor)
    loss = nn.MSELoss()(output, y_tensor)
    loss.backward()
    optimizer.step()
    
    final_loss = loss.item()
    print(f"      [OK] Training step complete, loss={final_loss:.6f}", flush=True)
    
    # Get final weights
    final_weights = {name: param.detach().cpu().numpy() 
                    for name, param in model.named_parameters()}
    print(f"      [OK] Final weights extracted: {len(final_weights)} parameters", flush=True)
    
    # Step 5: Create TrainingStatement (public)
    print("\n[5/7] Creating TrainingStatement and TrainingWitness...", flush=True)
    
    initial_weights_hash = hashlib.sha256(
        str([(k, v.shape, v.mean()) for k, v in initial_weights.items()]).encode()
    ).hexdigest()
    
    final_weights_hash = hashlib.sha256(
        str([(k, v.shape, v.mean()) for k, v in final_weights.items()]).encode()
    ).hexdigest()
    
    dataset_hash = hashlib.sha256(
        str(X_data.shape).encode() + str(y_data.shape).encode()
    ).hexdigest()
    
    statement = TrainingStatement(
        model_architecture="TinyTestModel",
        initial_weights_commitment=initial_weights_hash,
        final_weights_commitment=final_weights_hash,
        dataset_commitment=dataset_hash,
        local_epochs=1,
        batch_size=4,
        learning_rate=0.01,
        claimed_accuracy=0.0,
        claimed_loss=final_loss,
        sample_count=4,
        round_number=1,
        client_id="test_client",
        timestamp=time.time()
    )
    print(f"      [OK] TrainingStatement created", flush=True)
    print(f"           - Model: {statement.model_architecture}", flush=True)
    print(f"           - Samples: {statement.sample_count}", flush=True)
    print(f"           - Loss: {statement.claimed_loss:.6f}", flush=True)
    
    # Create TrainingWitness (private)
    witness = TrainingWitness(
        initial_weights=initial_weights,
        final_weights=final_weights,
        dataset_samples=X_data,
        dataset_labels=y_data
    )
    print(f"      [OK] TrainingWitness created", flush=True)
    
    # Step 6: Setup protocol and generate proof
    print("\n[6/7] Setting up ZKP protocol...", flush=True)
    print("      NOTE: This will generate 4096 G1 + 4096 G2 points", flush=True)
    print("      Expected time: 2-3 minutes", flush=True)
    sys.stdout.flush()
    
    protocol = ProductionProtostar(security_level=128)
    setup_start = time.time()
    setup_params = protocol.setup(statement=statement)
    setup_time = time.time() - setup_start
    
    print(f"\n      [OK] Setup complete in {setup_time:.1f}s", flush=True)
    print(f"           - SRS size: {setup_params['srs_size']} elements", flush=True)
    print(f"           - Security: {setup_params['security_level']}-bit", flush=True)
    print(f"           - Curve: {setup_params['curve']}", flush=True)
    
    # Generate proof
    print("\n      Generating cryptographic proof...", flush=True)
    sys.stdout.flush()
    proof_start = time.time()
    
    proof = protocol.generate_proof(statement, witness)
    
    proof_time = time.time() - proof_start
    proof_size = proof.get_size_bytes()
    
    print(f"      [OK] Proof generated in {proof_time:.2f}s", flush=True)
    print(f"           - Proof size: {proof_size:,} bytes", flush=True)
    print(f"           - Protocol type: {proof.protocol_type.value}", flush=True)
    
    # Step 7: Verify proof with pairing checks
    print("\n[7/7] Verifying proof with PAIRING VERIFICATION...", flush=True)
    sys.stdout.flush()
    
    verify_start = time.time()
    result = protocol.verify_proof(statement, proof)
    verify_time = time.time() - verify_start
    
    print(f"      [OK] Verification complete in {verify_time:.3f}s", flush=True)
    
    # Display verification results
    print("\n" + "="*80, flush=True)
    print("VERIFICATION RESULTS:", flush=True)
    print("="*80, flush=True)
    print(f"Valid: {result.is_valid}", flush=True)
    print(f"Message: {result.message if result.message else 'N/A'}", flush=True)
    print(f"Verification time: {result.verification_time:.3f}s", flush=True)
    
    if result.details:
        print("\nDetailed verification info:", flush=True)
        for key, value in result.details.items():
            if key == 'pairing_checks':
                print(f"  {key}:", flush=True)
                for pk, pv in value.items():
                    print(f"    - {pk}: {pv}", flush=True)
            elif isinstance(value, dict):
                print(f"  {key}: {value}", flush=True)
            else:
                print(f"  {key}: {value}", flush=True)
    
    # Check pairing verification status
    print("\n" + "="*80, flush=True)
    print("PAIRING VERIFICATION STATUS:", flush=True)
    print("="*80, flush=True)
    
    pairing_enabled = False
    if result.details and 'pairing_checks' in result.details:
        pairing_status = result.details['pairing_checks'].get('pairing_verification_status', 'unknown')
        print(f"Status: {pairing_status}", flush=True)
        
        if pairing_status == 'enabled':
            print("\n[SUCCESS] PAIRING VERIFICATION IS PROPERLY ENABLED!", flush=True)
            pairing_enabled = True
        elif pairing_status == 'disabled_for_demo':
            print("\n[FAILURE] PAIRING VERIFICATION IS STILL DISABLED!", flush=True)
        else:
            print(f"\n[WARNING] UNEXPECTED STATUS: {pairing_status}", flush=True)
    else:
        print("[ERROR] No pairing check details found!", flush=True)
    
    # Test tampered proof
    print("\n" + "="*80, flush=True)
    print("TESTING TAMPERED PROOF REJECTION:", flush=True)
    print("="*80, flush=True)
    
    # Create tampered proof by modifying the proof data
    tampered_proof_data = proof.proof_data.copy()
    if 'witness_commitment' in tampered_proof_data:
        if isinstance(tampered_proof_data['witness_commitment'], dict):
            if 'point_coords' in tampered_proof_data['witness_commitment']:
                coords = tampered_proof_data['witness_commitment']['point_coords']
                orig = str(coords[0])
                coords[0] = str((int(str(coords[0])) + 77777) % curve_order)
                print(f"Tampering witness commitment:", flush=True)
                print(f"  Original: {orig[:30]}...", flush=True)
                print(f"  Tampered: {coords[0][:30]}...", flush=True)
    
    from dataclasses import replace
    tampered_proof = replace(proof, proof_data=tampered_proof_data)
    
    print("\nVerifying tampered proof...", flush=True)
    sys.stdout.flush()
    result_tampered = protocol.verify_proof(statement, tampered_proof)
    
    print(f"\nTampered proof valid: {result_tampered.is_valid}", flush=True)
    print(f"Message: {result_tampered.message if result_tampered.message else 'N/A'}", flush=True)
    
    if not result_tampered.is_valid:
        print("\n[SUCCESS] Tampered proof was correctly REJECTED!", flush=True)
    else:
        print("\n[FAILURE] Tampered proof was ACCEPTED (security issue!)", flush=True)
    
    # Final test summary
    print("\n" + "="*80, flush=True)
    print("FINAL TEST RESULTS:", flush=True)
    print("="*80, flush=True)
    
    tests_passed = 0
    tests_total = 3
    
    print("\nTest Results:", flush=True)
    if result.is_valid:
        print("  [PASS] Valid proof verification", flush=True)
        tests_passed += 1
    else:
        print("  [FAIL] Valid proof verification", flush=True)
    
    if pairing_enabled:
        print("  [PASS] Pairing verification enabled", flush=True)
        tests_passed += 1
    else:
        print("  [FAIL] Pairing verification enabled", flush=True)
    
    if not result_tampered.is_valid:
        print("  [PASS] Tampered proof rejection", flush=True)
        tests_passed += 1
    else:
        print("  [FAIL] Tampered proof rejection", flush=True)
    
    print(f"\nScore: {tests_passed}/{tests_total}", flush=True)
    print(f"End time: {time.strftime('%H:%M:%S')}", flush=True)
    
    if tests_passed == tests_total:
        print("\n" + "="*80, flush=True)
        print("SUCCESS! ALL TESTS PASSED!", flush=True)
        print("The system is 100% proper with pairing verification enabled.", flush=True)
        print("="*80, flush=True)
        sys.exit(0)
    else:
        print(f"\n[WARNING] {tests_total - tests_passed} test(s) failed", flush=True)
        sys.exit(1)

except KeyboardInterrupt:
    print("\n\n[INTERRUPTED] Test cancelled by user (Ctrl+C)", flush=True)
    sys.exit(130)

except Exception as e:
    print(f"\n[ERROR] Test failed with exception:", flush=True)
    print(f"  {type(e).__name__}: {e}", flush=True)
    
    import traceback
    print("\nFull traceback:", flush=True)
    traceback.print_exc()
    sys.exit(1)
