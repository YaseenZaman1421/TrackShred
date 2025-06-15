# 🔐 TrackShred v1.0.1 – Secure File & Metadata Destruction Tool

TrackShred is a Linux-only CLI tool to **securely shred files**, **clean metadata**, and **remove privacy-leaking system traces**. Designed for privacy-conscious users, security researchers, and Linux professionals, it helps you wipe data the right way — safely, efficiently, and completely.

---

## 🚀 Features

- 🧹 **Secure File Shredding** – Multi-pass deletion to prevent recovery
- 🔎 **Metadata Stripping** – EXIF/doc properties wiped clean
- 🧼 **System Hygiene** – Cleans recent files, thumbnails, trash
- ⚙️ **Dry-Run Mode** – Preview before you commit
- 🎯 **Profile System** – Choose "basic", "paranoid", or your own settings
- 📦 **User & System Installation** – Run from anywhere via `trackshred`
- ✨ **Clean UX** – ASCII art, emoji-based status, smart help

---

## 🔧 Installation

### ✅ Recommended: Install globally

```bash
# Make executable
chmod +x Source_Code.py

# System-wide install (requires sudo)
sudo ./Source_Code.py --install

# OR: User-only install (no sudo needed)
./Source_Code.py --install-user
