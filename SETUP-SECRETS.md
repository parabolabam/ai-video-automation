# How to Get GitHub Secrets Values

## Overview

You need to add 3 secrets to GitHub for the deployment to work. Here's how to find each value.

## Step-by-Step Instructions

### 1. DO_DROPLET_IP (Your Droplet's IP Address)

**Option A: From Digital Ocean Dashboard**
1. Log in to https://cloud.digitalocean.com/
2. Go to "Droplets" in the left sidebar
3. Find your droplet name
4. Copy the IP address shown

**Option B: From Terminal (if you know how to SSH to it)**
```bash
# If you have the droplet IP, just use that
# Example: 159.89.123.45
```

**Option C: From your droplet (SSH in and run)**
```bash
curl ifconfig.me
# This will output your droplet's public IP
```

---

### 2. DO_DROPLET_USER (SSH Username)

This is the username you use to SSH into your droplet.

**Common values**:
- `root` (if you haven't created other users)
- `ubuntu` (if you're using Ubuntu)
- Your custom username (if you created one)

**To find out**:
1. Check your Digital Ocean dashboard for the droplet
2. Or check how you normally SSH in:
   ```bash
   # If you SSH like this:
   ssh root@YOUR_IP
   # Then your user is: root

   # If you SSH like this:
   ssh ubuntu@YOUR_IP
   # Then your user is: ubuntu
   ```

---

### 3. DO_SSH_PRIVATE_KEY (SSH Private Key for GitHub Actions)

**You have two SSH keys for Digital Ocean locally**:
- `~/.ssh/digital_ocean` (owned by root)
- `~/.ssh/id_dig_ocean` (owned by you)

**IMPORTANT**: GitHub Actions needs a DEDICATED key, not your existing ones.

**Steps to create GitHub Actions SSH key ON YOUR DROPLET**:

1. **SSH into your droplet**:
   ```bash
   # Use one of your existing keys
   ssh -i ~/.ssh/id_dig_ocean root@YOUR_DROPLET_IP
   # OR
   ssh -i ~/.ssh/id_dig_ocean ubuntu@YOUR_DROPLET_IP
   ```

2. **Once on the droplet, create a new SSH key for GitHub Actions**:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/github_actions -N ''
   ```

3. **Add the public key to authorized_keys**:
   ```bash
   cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

4. **Display the private key** (copy this for GitHub):
   ```bash
   cat ~/.ssh/github_actions
   ```

   **Copy the ENTIRE output**, including:
   ```
   -----BEGIN OPENSSH PRIVATE KEY-----
   ...all the lines...
   -----END OPENSSH PRIVATE KEY-----
   ```

5. **Test the key works** (from your local machine):
   ```bash
   ssh -i /path/to/copied/key YOUR_USER@YOUR_DROPLET_IP
   ```

---

## Quick Helper Script

I've created a script that will gather all these values for you **when run on your droplet**:

```bash
# 1. Copy the script to your droplet
scp -i ~/.ssh/id_dig_ocean scripts/get-github-secrets.sh YOUR_USER@YOUR_DROPLET_IP:~/

# 2. SSH to droplet
ssh -i ~/.ssh/id_dig_ocean YOUR_USER@YOUR_DROPLET_IP

# 3. Run the script
bash ~/get-github-secrets.sh
```

This will output all 3 values ready to copy to GitHub.

---

## Adding Secrets to GitHub

Once you have all 3 values:

1. Go to your GitHub repository
2. Click **Settings** (top menu)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**
5. Add each secret:

| Name | Value | Example |
|------|-------|---------|
| `DO_DROPLET_IP` | Your droplet IP | `159.89.123.45` |
| `DO_DROPLET_USER` | SSH username | `root` or `ubuntu` |
| `DO_SSH_PRIVATE_KEY` | Full private key content | `-----BEGIN OPENSSH...` |

**IMPORTANT for DO_SSH_PRIVATE_KEY**:
- Copy the ENTIRE key including BEGIN/END lines
- Make sure there are no extra spaces or line breaks
- Should look like:
  ```
  -----BEGIN OPENSSH PRIVATE KEY-----
  b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
  ...many more lines...
  -----END OPENSSH PRIVATE KEY-----
  ```

---

## Verification

After adding secrets, you can verify they're set:

1. Go to your repository
2. Settings → Secrets and variables → Actions
3. You should see 3 secrets listed (values are hidden):
   - ✅ DO_DROPLET_IP
   - ✅ DO_DROPLET_USER
   - ✅ DO_SSH_PRIVATE_KEY

---

## What If You Don't Know Your Droplet IP?

If you can't find your droplet IP:

1. **Check Digital Ocean Dashboard**: https://cloud.digitalocean.com/droplets
2. **Check your terminal history**:
   ```bash
   history | grep ssh | grep -E "[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+"
   ```
3. **Check your projects/notes** where you might have saved it

---

## Troubleshooting

**"I can't SSH to my droplet"**
- Make sure your droplet is powered on in Digital Ocean dashboard
- Try using the Digital Ocean console (Droplets → Your Droplet → Access → Launch Droplet Console)
- Check your firewall settings allow SSH (port 22)

**"Permission denied when using SSH key"**
- Make sure you're using the correct username
- Try with `root` user if other users don't work
- Check key permissions: `chmod 600 ~/.ssh/id_dig_ocean`

**"I get timeout when trying to SSH"**
- Check droplet is running in Digital Ocean dashboard
- Check your internet connection
- Try from a different network (some networks block outgoing SSH)

---

## Need Help?

If you're stuck:
1. Log in to Digital Ocean dashboard: https://cloud.digitalocean.com/
2. Find your droplet and note down:
   - Droplet name
   - IP address (shown next to droplet name)
   - Distribution (Ubuntu, Debian, etc.)
3. Use the "Access" → "Launch Droplet Console" to access it directly from browser
