# Libsnark Groth16 Specification
## Reference Implementation Guide

This document specifies the **practical Groth16** variant as implemented in libsnark, which we'll follow for our FL system.

---

## 1. Verification Equation

The libsnark Groth16 uses this verification equation:

```
e(π_A, π_B) = e(α, β) · e(vk_x, γ) · e(π_C, δ)
```

Where:
- `vk_x = IC[0] + Σᵢ public_input[i] · IC[i+1]` (public input commitment)
- `e()` is the pairing function
- All group operations are in appropriate groups (G1, G2, GT)

---

## 2. Common Reference String (CRS) / Trusted Setup

### 2.1 Toxic Waste
Sample random field elements:
- `α, β, γ, δ, τ` ∈ F_p (must be destroyed after setup!)

### 2.2 Proving Key Components

```python
pk = {
    # Basic elements
    'alpha_g1': [α]₁,
    'beta_g1': [β]₁,
    'beta_g2': [β]₂,
    'delta_g1': [δ]₁,
    'delta_g2': [δ]₂,
    
    # A-query: [Aᵢ(τ)]₁ for i ∈ {0...m}
    'A_query': [[A₀(τ)]₁, [A₁(τ)]₁, ..., [Aₘ(τ)]₁],
    
    # B-query: [Bᵢ(τ)]₁ and [Bᵢ(τ)]₂ for i ∈ {0...m}
    'B_query_g1': [[B₀(τ)]₁, [B₁(τ)]₁, ..., [Bₘ(τ)]₁],
    'B_query_g2': [[B₀(τ)]₂, [B₁(τ)]₂, ..., [Bₘ(τ)]₂],
    
    # L-query: [(βAᵢ(τ) + αBᵢ(τ) + Cᵢ(τ)) / δ]₁ for i ∈ {l+1...m}
    # (l = number of public inputs, includes constant 1)
    'L_query': [...],  # Only for PRIVATE witness variables
    
    # H-query: [τⁱ / δ]₁ for i ∈ {0...n-2}
    # (n = number of constraints, degree of target polynomial t(x))
    'H_query': [[τ⁰/δ]₁, [τ¹/δ]₁, ..., [τⁿ⁻²/δ]₁]
}
```

### 2.3 Verification Key Components

```python
vk = {
    'alpha_g1': [α]₁,
    'beta_g2': [β]₂,
    'gamma_g2': [γ]₂,
    'delta_g2': [δ]₂,
    
    # IC-query: [(βAᵢ(τ) + αBᵢ(τ) + Cᵢ(τ)) / γ]₁ for i ∈ {0...l}
    # IC[0] is constant term, IC[1..l] for public inputs
    'IC': [[...]₁, [...]₁, ..., [...]₁]  # l+1 elements
}
```

---

## 3. Proof Generation

### 3.1 Inputs
- Witness: `w = [1, public_input₁, ..., public_inputₗ, private₁, ..., privateₘ₋ₗ]`
- Proving key: `pk`

### 3.2 Algorithm

```python
def prove(pk, witness):
    # 1. Sample random blinding factors
    r, s = random_field_elements()
    
    # 2. Compute π_A = [α]₁ + Σᵢ wᵢ[Aᵢ(τ)]₁ + [rδ]₁
    π_A = pk.alpha_g1
    for i in range(len(witness)):
        π_A += witness[i] * pk.A_query[i]
    π_A += r * pk.delta_g1
    
    # 3. Compute π_B = [β]₂ + Σᵢ wᵢ[Bᵢ(τ)]₂ + [sδ]₂
    π_B = pk.beta_g2
    for i in range(len(witness)):
        π_B += witness[i] * pk.B_query_g2[i]
    π_B += s * pk.delta_g2
    
    # 4. Compute B_g1 = [β]₁ + Σᵢ wᵢ[Bᵢ(τ)]₁ + [sδ]₁
    #    (needed for π_C computation)
    B_g1 = pk.beta_g1
    for i in range(len(witness)):
        B_g1 += witness[i] * pk.B_query_g1[i]
    B_g1 += s * pk.delta_g1
    
    # 5. Compute H(τ) = h(τ)/δ where h(τ) is quotient polynomial
    #    h(x) = [A(x)·B(x) - C(x)] / t(x)
    h_coeffs = compute_quotient_polynomial(witness, R1CS)
    H_at_tau = sum(h_coeffs[i] * pk.H_query[i] for i in range(len(h_coeffs)))
    
    # 6. Compute π_C = H(τ) + Σᵢ₌ₗ₊₁ᵐ wᵢ·L_query[i] + s·π_A + r·B_g1 - rsδ
    π_C = H_at_tau
    for i in range(l+1, m+1):  # Only private witness
        π_C += witness[i] * pk.L_query[i - (l+1)]
    π_C += s * π_A
    π_C += r * B_g1
    π_C -= (r * s) * pk.delta_g1
    
    return (π_A, π_B, π_C)
```

---

## 4. Proof Verification

### 4.1 Inputs
- Proof: `(π_A, π_B, π_C)`
- Public inputs: `[public₁, ..., publicₗ]`
- Verification key: `vk`

### 4.2 Algorithm

```python
def verify(vk, proof, public_inputs):
    # 1. Compute vk_x = IC[0] + Σᵢ publicᵢ·IC[i+1]
    vk_x = vk.IC[0]
    for i in range(len(public_inputs)):
        vk_x += public_inputs[i] * vk.IC[i+1]
    
    # 2. Check pairing equation:
    #    e(π_A, π_B) = e(α, β) · e(vk_x, γ) · e(π_C, δ)
    left = pairing(π_A, π_B)
    right = pairing(vk.alpha_g1, vk.beta_g2) * \
            pairing(vk_x, vk.gamma_g2) * \
            pairing(π_C, vk.delta_g2)
    
    return left == right
```

---

## 5. Key Differences from Original Paper

1. **H-query pre-divided by δ**: Simplifies prover computation
2. **L-query only for private witness**: Public inputs use IC in verification
3. **B-query in both G1 and G2**: Needed for π_C computation
4. **Explicit blinding factor handling**: Clearer separation of randomness

---

## 6. Implementation Notes for FL System

### 6.1 QAP Construction
- Use proper Lagrange interpolation (already implemented in `qap.py`)
- Evaluation points: `r_j = j` for `j ∈ {1, 2, ..., n}`
- Target polynomial: `t(x) = Π(x - r_j)`

### 6.2 Quotient Polynomial
```python
# Compute h(x) such that A(x)·B(x) - C(x) = h(x)·t(x)
# Where A(x) = Σ wᵢ·Aᵢ(x), B(x) = Σ wᵢ·Bᵢ(x), C(x) = Σ wᵢ·Cᵢ(x)
```

### 6.3 Public vs Private Witness Split
```
witness = [
    w₀ = 1,                    # Constant (public)
    w₁...wₗ = public inputs,   # Public
    wₗ₊₁...wₘ = private witness # Private
]
```

---

## 7. Test Vectors

For circuit: `a * b = c` with `a=3, b=5, c=15`

```python
# R1CS
A = [{1: 1}]  # z[1] (variable a)
B = [{2: 1}]  # z[2] (variable b)  
C = [{3: 1}]  # z[3] (variable c)

# Witness
w = [1, 3, 5, 15]  # [1, a, b, c]

# Public inputs: none (only constant 1)
public_inputs = []

# After setup/prove/verify:
# Should return: True
```

---

## 8. Error Checklist

Common implementation errors to avoid:
- ❌ Mixing public/private indices in L-query
- ❌ Forgetting to divide H-query by δ during setup
- ❌ Not computing B_g1 separately for π_C
- ❌ Wrong pairing order (matters for type-3 pairings)
- ❌ Identity element handling (multiply by 0 should give identity)
- ❌ IC[0] being zero (should always be non-zero)

---

This specification matches **libsnark**, **bellman**, and **arkworks** implementations.
