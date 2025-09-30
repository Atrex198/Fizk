#!/bin/bash

# GitHub Upload Helper Script for ZK-FL System
# This script helps you upload the repository to GitHub

echo "🚀 ZK-FL System - GitHub Upload Helper"
echo "======================================"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Error: Git repository not initialized"
    echo "Please run 'git init' first"
    exit 1
fi

# Check if we have commits
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    echo "❌ Error: No commits found"
    echo "Please commit your changes first"
    exit 1
fi

echo "✅ Git repository is ready"
echo ""

echo "📋 Instructions to upload to GitHub:"
echo ""
echo "1. Create a new repository on GitHub:"
echo "   - Go to https://github.com/new"
echo "   - Repository name: zk-fl-system (or your preferred name)"
echo "   - Description: Zero-Knowledge Federated Learning System with Advanced Optimizations"
echo "   - Keep it Public or Private (your choice)"
echo "   - DO NOT initialize with README, .gitignore, or license (we already have them)"
echo ""

echo "2. Copy and run these commands (replace YOUR_USERNAME and REPO_NAME):"
echo ""
echo "   git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git"
echo "   git push -u origin main"
echo ""

echo "3. Alternative: If you prefer SSH (recommended for frequent commits):"
echo ""
echo "   git remote add origin git@github.com:YOUR_USERNAME/REPO_NAME.git"
echo "   git push -u origin main"
echo ""

echo "🔍 Repository Information:"
echo "   Total files committed: $(git ls-files | wc -l)"
echo "   Total lines of code: $(git ls-files | xargs wc -l | tail -1 | awk '{print $1}')"
echo "   Current branch: $(git branch --show-current)"
echo "   Latest commit: $(git log -1 --oneline)"
echo ""

echo "📂 Key files included:"
echo "   ✅ .gitignore (excludes venv, generated files)"
echo "   ✅ README.md (comprehensive project documentation)"
echo "   ✅ requirements.txt (Python dependencies)"
echo "   ✅ All ZK-FL system modules (1-7)"
echo "   ✅ Test files and demonstrations"
echo "   ✅ Rust ZKP implementation"
echo ""

echo "🚫 Files properly excluded:"
echo "   • venv/ directory"
echo "   • __pycache__/ directories"
echo "   • Generated .json files"
echo "   • Model weights (.pth, .joblib)"
echo "   • Dataset files (.csv)"
echo "   • Generated reports (.html, .png)"
echo ""

echo "💡 Pro Tips:"
echo "   • After uploading, add topics/tags: federated-learning, zero-knowledge, privacy, cryptography"
echo "   • Consider enabling GitHub Pages for the dashboard demo HTML"
echo "   • Add a license file if you want to specify terms"
echo "   • Star the repository to bookmark it! ⭐"
echo ""

echo "🎯 Ready to upload! Follow the instructions above."