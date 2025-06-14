# 🔐 TrackShred - Secure File & Metadata Destruction Tool

A Linux CLI tool for securely deleting sensitive files, wiping metadata, and cleaning forensic traces beyond the file itself.

## 🚀 Features

- **Secure File Shredding**: Multiple-pass overwriting using `shred` or Python fallback
- **Metadata Cleaning**: Strip metadata from files using `exiftool` or built-in methods
- **System-wide Privacy Sweep**: Clean thumbnails, recent files, trash, and shell history
- **Flexible Operation Modes**: Target specific files/directories or perform deep system cleaning
- **Safety Features**: Dry-run mode, input validation, graceful shutdown
- **Comprehensive Logging**: Detailed logs and optional JSON reports
- **POSIX Compliant**: Uses standard Linux tools and follows FHS conventions

## 📦 Installation

### Prerequisites

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install coreutils exiftool

# RHEL/CentOS/Fedora
sudo dnf install coreutils perl-Image-ExifTool

# Arch Linux
sudo pacman -S coreutils perl-image-exiftool
```

### Install TrackShred

```bash
# Download the script
curl -O https://raw.githubusercontent.com/yourusername/trackshred/main/trackshred.py

# Make it executable
chmod +x trackshred.py

# Optional: Install system-wide
sudo cp trackshred.py /usr/local/bin/trackshred
```

## 🛠️ Usage

### Basic Examples

```bash
# Shred a single file
./trackshred.py --target ~/secret.pdf

# Shred all files in a directory
./trackshred.py --target ~/Documents/sensitive/

# Perform system-wide privacy cleaning
./trackshred.py --deep

# Combined file shredding and system cleaning
./trackshred.py --target ~/secret.zip --deep

# Clean only metadata (don't delete files)
./trackshred.py --target ~/photos/ --metadata-only

# Dry run (see what would be done)
./trackshred.py --target ~/test.txt --dry-run
```

### Advanced Usage

```bash
# Custom number of shred passes
./trackshred.py --target file.pdf --shred-passes 7

# Verbose output with custom log file
./trackshred.py --target ~/data/ --verbose --log /tmp/my-shred.log

# Generate JSON report
./trackshred.py --deep --report /tmp/cleanup-report.json

# Use custom configuration file
./trackshred.py --target ~/file.txt --config ~/.config/trackshred/custom.json
```

## ⚙️ Configuration

TrackShred uses a JSON configuration file located at `~/.config/trackshred/config.json`:

```json
{
  "shred_passes": 3,
  "log_level": "INFO",
  "log_file": "/tmp/trackshred.log",
  "clean_thumbnails": true,
  "clean_recent_files": true,
  "clean_trash": true,
  "clean_shell_history": false
}
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `shred_passes` | 3 | Number of overwrite passes for file shredding |
| `log_level` | "INFO" | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `log_file` | "/tmp/trackshred.log" | Path to log file |
| `clean_thumbnails` | true | Clean GNOME thumbnail cache during deep clean |
| `clean_recent_files` | true | Clean recent files list during deep clean |
| `clean_trash` | true | Empty trash during deep clean |
| `clean_shell_history` | false | Clear shell history (use with caution!) |

## 📋 Command Line Options

| Option | Description |
|--------|-------------|
| `--target PATH` | Target file or directory to shred |
| `--deep` | Perform aggressive system-wide privacy sweep |
| `--shred-passes N` | Number of overwrite passes (1-10) |
| `--metadata-only` | Only clean metadata without deleting files |
| `--dry-run` | Show what would be deleted without taking action |
| `--config PATH` | Path to configuration file |
| `--log PATH` | Path to log file |
| `--report PATH` | Save operation report to JSON file |
| `--verbose, -v` | Verbose output |
| `--version` | Show version information |

## 🧹 What Gets Cleaned

### File-level Operations
- **File Shredding**: Multiple-pass overwriting with random data
- **Metadata Removal**: EXIF data, document properties, timestamps

### System-level Operations (--deep)
- **Thumbnail Cache**: `~/.cache/thumbnails/`, `~/.thumbnails/`
- **Recent Files**: `~/.local/share/recently-used.xbel`
- **Trash**: `~/.local/share/Trash/`
- **Shell History**: `~/.bash_history`, `~/.zsh_history` (optional)

## 🔒 Security Features

- **Input Validation**: Prevents path traversal and invalid inputs
- **No Root Required**: Runs with user permissions only
- **Graceful Shutdown**: Handles SIGINT/SIGTERM signals properly
- **Error Handling**: Comprehensive error reporting and logging
- **Dry Run Mode**: Preview operations before execution

## 📊 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Permission error |
| 3 | Invalid input |

## 🚨 Important Notes

### Security Considerations
- **SSD Drives**: File shredding may not be fully effective on SSDs due to wear leveling
- **Filesystem**: Results may vary on different filesystems (ext4, btrfs, etc.)
- **Backups**: This tool cannot remove data from backups or snapshots
- **Swap Files**: Consider disabling swap or using encrypted swap

### Limitations
- Requires Linux operating system
- Some features require additional tools (`shred`, `exiftool`)
- Cannot guarantee complete data destruction on all storage types
- Does not handle remote/cloud backups

## 🐛 Troubleshooting

### Common Issues

**Permission Denied Errors**
```bash
# Ensure you have write permissions to target files
ls -la /path/to/file

# For system-wide cleaning, make sure directories exist
mkdir -p ~/.cache ~/.local/share
```

**Missing Dependencies**
```bash
# Check if required tools are installed
which shred exiftool

# Install missing tools
sudo apt install coreutils exiftool  # Ubuntu/Debian
```

**Configuration Issues**
```bash
# Reset configuration to defaults
rm ~/.config/trackshred/config.json

# Check log file for errors
tail -f /tmp/trackshred.log
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ⚠️ Disclaimer

This tool is designed to help protect privacy by securely deleting files and cleaning system traces. However, it cannot guarantee complete data destruction in all scenarios. Use at your own risk and always maintain proper backups of important data.

**Important**: Always test on non-critical data first. The developers are not responsible for any data loss or system damage.

## 📚 Resources

- [Secure File Deletion](https://en.wikipedia.org/wiki/Data_erasure)
- [Linux Filesystem Hierarchy Standard](https://refspecs.linuxfoundation.org/FHS_3.0/fhs/index.html)
- [NIST Guidelines for Media Sanitization](https://csrc.nist.gov/publications/detail/sp/800-88/rev-1/final)
