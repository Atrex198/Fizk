"""
FINAL PAIRING VERIFICATION TEST - Complete & Working
====================================================
This test properly creates a real model, trains it, and generates/verifies a proof.
"""

import sys
import os
import time

# CRITICAL: Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
os.environ['PYTHONUNBUFFERED'] = '1'

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

print("\n" + "="*80, flush=True)
print("COMPLETE PAIRING VERIFICATION TEST", flush=True)
print("="*80, flush=True)
print(f"Start time: {time.strftime('%H:%M:%S')}\n", flush=True)

try:
    print("[1/8] Importing modules...", flush=True)
    import torch
    import numpy as np
    from zkp_protocols.protostar_production import ProductionProtostar
    from zkp_protocols.base import TrainingStatement, TrainingWitness
    from real_ml_trainer import MedicalMLPModel, RealMLTrainer
    from py_ecc.bn128 import curve_order
    import hashlib
    import json
    print("      [OK] All imports successful\n", flush=True)
    
    print("[2/8] Creating and initializing model...", flush=True)
    # CRITICAL: Must use the EXACT architecture that complete_r1cs_circuit.py expects
    # Circuit hardcodes: network.0 (input->64), network.4 (64->32), network.8 (32->2)
    # This matches RealMLTrainer's architecture: hidden_sizes=[64, 32], num_classes=2
    model = MedicalMLPModel(input_features=11, hidden_sizes=[64, 32], num_classes=2)
    print(f"      Model architecture: 11 -> [64, 32] -> 2 (matches circuit requirements)", flush=True)
    
    # Get initial weights
    initial_weights = {}
    for name, param in model.named_parameters():
        initial_weights[name] = param.detach().cpu().numpy().copy()
    
    # Verify we have the expected layers
    expected_layers = ['network.0.weight', 'network.0.bias', 
                      'network.4.weight', 'network.4.bias',
                      'network.8.weight', 'network.8.bias']
    missing = [l for l in expected_layers if l not in initial_weights]
    if missing:
        print(f"      ERROR: Missing expected layers: {missing}", flush=True)
        print(f"      Available layers: {list(initial_weights.keys())}", flush=True)
        sys.exit(1)
    
    print(f"      All required layers present:", flush=True)
    for name in expected_layers:
        print(f"        {name}: shape {initial_weights[name].shape}", flush=True)
    print("      [OK] Model initialized\n", flush=True)
    
    print("[3/8] Creating training data...", flush=True)
    # Create dataset with 11 features to match model input (cardio dataset has 11 features)
    X_train = torch.randn(20, 11)  # 20 samples, 11 features
    y_train = torch.randint(0, 2, (20,))  # Binary classification
    print(f"      Dataset: {X_train.shape[0]} samples, {X_train.shape[1]} features", flush=True)
    print("      [OK] Data created\n", flush=True)
    
    print("[4/8] Training model for 1 epoch...", flush=True)
    sys.stdout.flush()
    
    # Simple training loop
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    criterion = torch.nn.CrossEntropyLoss()
    
    model.train()
    optimizer.zero_grad()
    outputs = model(X_train)
    loss = criterion(outputs, y_train)
    loss.backward()
    optimizer.step()
    
    final_loss = loss.item()
    with torch.no_grad():
        predictions = torch.argmax(outputs, dim=1)
        accuracy = (predictions == y_train).float().mean().item()
    
    print(f"      Training loss: {final_loss:.4f}", flush=True)
    print(f"      Training accuracy: {accuracy:.4f}", flush=True)
    
    # Get final weights
    final_weights = {}
    for name, param in model.named_parameters():
        final_weights[name] = param.detach().cpu().numpy().copy()
    
    print("      [OK] Training complete\n", flush=True)
    
    print("[5/8] Creating ZKP statement and witness...", flush=True)
    
    # Create commitments
    initial_weights_hash = hashlib.sha256(
        json.dumps({k: v.tolist() for k, v in initial_weights.items()}, sort_keys=True).encode()
    ).hexdigest()
    
    final_weights_hash = hashlib.sha256(
        json.dumps({k: v.tolist() for k, v in final_weights.items()}, sort_keys=True).encode()
    ).hexdigest()
    
    dataset_hash = hashlib.sha256(
        str(X_train.shape).encode() + str(y_train.shape).encode()
    ).hexdigest()
    
    # Create statement (public information)
    statement = TrainingStatement(
        model_architecture="TestMLP",
        initial_weights_commitment=initial_weights_hash[:16] + "...",
        final_weights_commitment=final_weights_hash[:16] + "...",
        dataset_commitment=dataset_hash[:16] + "...",
        local_epochs=1,
        batch_size=10,
        learning_rate=0.01,
        claimed_accuracy=accuracy,
        claimed_loss=final_loss,
        sample_count=len(X_train),
        round_number=1,
        client_id="test_client",
        timestamp=time.time()
    )
    
    # Create witness (private information)
    witness = TrainingWitness(
        initial_weights=initial_weights,
        final_weights=final_weights,
        dataset_samples=X_train.numpy(),
        dataset_labels=y_train.numpy()
    )
    
    print(f"      Statement created: claimed_loss={statement.claimed_loss:.4f}", flush=True)
    print(f"      Witness created: {len(witness.initial_weights)} weight tensors", flush=True)
    print("      [OK] Statement and witness ready\n", flush=True)
    
    print("[6/8] Setting up ZKP protocol (this takes 2-3 minutes)...", flush=True)
    print("      NOTE: Generating 4096 G1 + G2 elliptic curve points", flush=True)
    print("      Progress updates appear every 256 elements", flush=True)
    sys.stdout.flush()
    
    protocol = ProductionProtostar(security_level=128)
    setup_start = time.time()
    setup_params = protocol.setup()
    setup_time = time.time() - setup_start
    
    print(f"\n      [OK] Setup complete in {setup_time:.1f}s", flush=True)
    print(f"      SRS size: {setup_params['srs_size']} elements\n", flush=True)
    
    print("[7/8] Generating cryptographic proof...", flush=True)
    print("      This will generate R1CS constraints from the ML training", flush=True)
    sys.stdout.flush()
    
    proof_start = time.time()
    proof = protocol.generate_proof(statement, witness)
    proof_time = time.time() - proof_start
    
    print(f"      [OK] Proof generated in {proof_time:.1f}s", flush=True)
    print(f"      Proof size: {proof.get_size_bytes()} bytes\n", flush=True)
    
    print("[8/8] Verifying proof WITH PAIRING CHECKS...", flush=True)
    sys.stdout.flush()
    
    verify_start = time.time()
    result = protocol.verify_proof(statement, proof)
    verify_time = time.time() - verify_start
    
    print(f"      [OK] Verification complete in {verify_time:.3f}s\n", flush=True)
    
    # Display results
    print("="*80, flush=True)
    print("VERIFICATION RESULT:", flush=True)
    print("="*80, flush=True)
    print(f"Valid: {result.is_valid}", flush=True)
    print(f"Message: {result.message}", flush=True)
    print(f"Verification time: {result.verification_time:.3f}s", flush=True)
    
    if result.details:
        print("\nDetailed information:", flush=True)
        for key, value in result.details.items():
            if key == 'pairing_checks':
                print(f"  {key}:", flush=True)
                for pk, pv in value.items():
                    print(f"    - {pk}: {pv}", flush=True)
            else:
                print(f"  {key}: {value}", flush=True)
    
    # Check pairing status
    print("\n" + "="*80, flush=True)
    print("PAIRING VERIFICATION STATUS:", flush=True)
    print("="*80, flush=True)
    
    pairing_enabled = False
    if result.details and 'pairing_checks' in result.details:
        pairing_status = result.details['pairing_checks'].get('pairing_verification_status', 'unknown')
        print(f"Status: {pairing_status}", flush=True)
        
        if pairing_status == 'enabled':
            print("\n[SUCCESS] PAIRING VERIFICATION IS ENABLED!", flush=True)
            pairing_enabled = True
        elif pairing_status == 'disabled_for_demo':
            print("\n[FAILURE] PAIRING VERIFICATION IS DISABLED!", flush=True)
        else:
            print(f"\n[UNKNOWN] Status: {pairing_status}", flush=True)
    else:
        print("[ERROR] No pairing check details found!", flush=True)
    
    # Test tampered proof
    print("\n" + "="*80, flush=True)
    print("TESTING TAMPERED PROOF (should be rejected):", flush=True)
    print("="*80, flush=True)
    
    tampered_proof_dict = proof.to_dict()
    if 'witness_commitment' in tampered_proof_dict:
        if 'point_coords' in tampered_proof_dict['witness_commitment']:
            coords = tampered_proof_dict['witness_commitment']['point_coords']
            orig = str(coords[0])
            coords[0] = str((int(coords[0]) + 12345) % curve_order)
            print(f"Tampered commitment: {orig[:20]}... -> {coords[0][:20]}...", flush=True)
    
    from zkp_protocols.base import ZKProof
    tampered_proof = ZKProof.from_dict(tampered_proof_dict)
    
    result_tampered = protocol.verify_proof(statement, tampered_proof)
    
    print(f"\nTampered proof valid: {result_tampered.is_valid}", flush=True)
    print(f"Message: {result_tampered.message}", flush=True)
    
    # Final summary
    print("\n" + "="*80, flush=True)
    print("FINAL TEST SUMMARY:", flush=True)
    print("="*80, flush=True)
    
    tests_passed = 0
    tests_total = 3
    
    if result.is_valid:
        print("[PASS] Test 1: Valid proof accepted", flush=True)
        tests_passed += 1
    else:
        print("[FAIL] Test 1: Valid proof rejected", flush=True)
    
    if pairing_enabled:
        print("[PASS] Test 2: Pairing verification enabled", flush=True)
        tests_passed += 1
    else:
        print("[FAIL] Test 2: Pairing verification not enabled", flush=True)
    
    if not result_tampered.is_valid:
        print("[PASS] Test 3: Tampered proof rejected", flush=True)
        tests_passed += 1
    else:
        print("[FAIL] Test 3: Tampered proof accepted (SECURITY ISSUE!)", flush=True)
    
    print(f"\nScore: {tests_passed}/{tests_total}", flush=True)
    print(f"End time: {time.strftime('%H:%M:%S')}", flush=True)
    
    if tests_passed == tests_total:
        print("\n" + "="*80, flush=True)
        print("[SUCCESS] ALL TESTS PASSED!", flush=True)
        print("THE SYSTEM IS NOW 100% PROPER WITH PAIRING VERIFICATION!", flush=True)
        print("="*80 + "\n", flush=True)
        sys.exit(0)
    else:
        print(f"\n[WARNING] {tests_total - tests_passed} test(s) failed\n", flush=True)
        sys.exit(1)

except KeyboardInterrupt:
    print("\n\n[INTERRUPTED] Test cancelled by user (Ctrl+C)", flush=True)
    sys.exit(1)

except Exception as e:
    print(f"\n[ERROR] Test failed:", flush=True)
    print(f"  {type(e).__name__}: {e}", flush=True)
    
    import traceback
    print("\nFull traceback:", flush=True)
    traceback.print_exc()
    sys.exit(1)
