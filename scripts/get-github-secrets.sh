#!/bin/bash

# Helper script to gather GitHub Secrets values for deployment
# Run this script ON YOUR DIGITAL OCEAN DROPLET

echo "========================================="
echo "GitHub Secrets Values"
echo "========================================="
echo ""
echo "Copy these values to your GitHub repository secrets:"
echo "Go to: Settings → Secrets and variables → Actions"
echo ""
echo "========================================="
echo ""

# DO_DROPLET_IP
echo "1. DO_DROPLET_IP"
echo "   Value:"
DROPLET_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || echo "UNABLE_TO_DETECT")
echo "   $DROPLET_IP"
echo ""

# DO_DROPLET_USER
echo "2. DO_DROPLET_USER"
echo "   Value:"
echo "   $USER"
echo ""

# DO_SSH_PRIVATE_KEY
echo "3. DO_SSH_PRIVATE_KEY"
echo ""
if [ -f ~/.ssh/github_actions ]; then
    echo "   ✅ SSH key exists at ~/.ssh/github_actions"
    echo ""
    echo "   Copy the ENTIRE content below (including BEGIN/END lines):"
    echo "   ================================================"
    cat ~/.ssh/github_actions
    echo "   ================================================"
else
    echo "   ❌ SSH key NOT found at ~/.ssh/github_actions"
    echo ""
    echo "   Generate it with:"
    echo "   ssh-keygen -t ed25519 -f ~/.ssh/github_actions -N ''"
    echo "   cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys"
    echo "   chmod 600 ~/.ssh/authorized_keys"
    echo ""
    echo "   Then run this script again."
fi

echo ""
echo "========================================="
echo "Summary"
echo "========================================="
echo ""
echo "Add these 3 secrets to GitHub:"
echo "https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions"
echo ""
echo "Secret Name: DO_DROPLET_IP"
echo "Value: $DROPLET_IP"
echo ""
echo "Secret Name: DO_DROPLET_USER"
echo "Value: $USER"
echo ""
echo "Secret Name: DO_SSH_PRIVATE_KEY"
echo "Value: (content of ~/.ssh/github_actions shown above)"
echo ""
