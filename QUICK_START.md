# 🚀 Quick Start Guide - Security Testing UI

## ✅ Current Status

Both servers are now running:

- **Backend**: http://localhost:8000 (FastAPI + WebSocket)
- **Frontend**: http://localhost:5173 (Vite + React)

## 🎯 Access the Security Testing Page

1. Open your browser and go to: **http://localhost:5173**

2. Click **"Security Tests"** in the sidebar (shield with warning icon: 🛡️⚠️)

3. Click **"Run All Security Tests"** button

4. Watch as tests execute showing:
   - ✅ **Green (Defended)**: Attack cryptographically rejected
   - ⚠️ **Yellow (Requires Mitigation)**: Needs protocol-level handling
   - 🔵 **Blue (Running)**: Currently executing
   - ⚪ **Gray (Pending)**: Not yet run

5. Click any test card to expand and see:
   - Attack scenario details
   - Defense mechanism explanation
   - Test execution results
   - Honest vs malicious behavior comparison

## 📊 What You'll See

### Statistics Dashboard (Top)
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ 🛡️ Total    │ ✅ Defended │ ⚠️ Vulnerable│ ✓ Coverage  │
│    Tests    │             │             │             │
│      5      │      4      │      1      │     80%     │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

### Test Results

1. **✅ Freeloading Attack - DEFENDED**
   - Attack: Client submits unchanged weights
   - Defense: R1CS constraint fails (0 ≠ 1)
   - Status: Proof generation REJECTED

2. **⚠️ Weight Manipulation - REQUIRES MITIGATION**
   - Attack: Large malicious weight changes (7.8x normal)
   - Defense: Computation correct but magnitude unconstrained
   - Status: Needs server-side outlier detection

3. **✅ Gradient Bypass - DEFENDED**
   - Attack: Fake gradients instead of backprop
   - Defense: Gradients computed inside circuit
   - Status: Cannot skip computation

4. **✅ Commitment Tampering - DEFENDED**
   - Attack: Claim different weights than used
   - Defense: Commitment binding enforced
   - Status: Proof generation REJECTED

5. **✅ Replay Attack - DEFENDED**
   - Attack: Reuse old proof in new round
   - Defense: Unique nonces tracked
   - Status: Server rejects duplicates

## 🎨 UI Features

- **Dark theme** with indigo/violet gradients
- **Expandable cards** for detailed results
- **Real-time progress** indicators
- **Color-coded status** badges
- **Execution time** tracking
- **Summary dashboard** at bottom

## 🔧 If You Need to Restart

### Backend
```bash
cd /home/atharva/Work/FIZKfinal/Fizk/dashboard/backend
source ../../.venv/bin/activate
python main.py
```

### Frontend
```bash
cd /home/atharva/Work/FIZKfinal/Fizk/dashboard/frontend
npm run dev
```

### Stop Servers
```bash
# Stop backend (Ctrl+C in backend terminal)
# Or: pkill -f "uvicorn"

# Stop frontend (Ctrl+C in frontend terminal)
# Or: pkill -f "vite"
```

## 🔍 Testing the API Directly

You can also test the backend API directly:

```bash
# Test security endpoint
curl -X POST http://localhost:8000/api/security/test/freeloading

# Expected response:
{
  "honest_accepted": true,
  "attack_rejected": true,
  "details": "Anti-freeloading constraint failed...",
  "execution_time": 2.3
}
```

## 📝 Navigation

The Security Tests page is accessible via:
- **Route**: `/security`
- **Sidebar**: Last item in navigation
- **Icon**: Shield with alert (🛡️⚠️)
- **Label**: "Security Tests"

## 🎯 Network Admin Use Cases

1. **Periodic Audits**: Run weekly to verify security
2. **Post-Update Validation**: Ensure changes didn't break security
3. **Compliance Reporting**: Visual proof for auditors
4. **Incident Investigation**: Check which attacks are blocked
5. **Demo to Stakeholders**: Show security guarantees

## 🛡️ Security Guarantees

The UI demonstrates:
- ✅ Freeloading is cryptographically impossible
- ✅ Gradient computation is enforced
- ✅ Commitment tampering is detected
- ✅ Replay attacks are prevented
- ⚠️ Large updates need server-side checks

## 🚀 You're All Set!

Navigate to http://localhost:5173 and explore the Security Testing page!
