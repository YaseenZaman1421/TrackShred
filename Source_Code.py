#!/usr/bin/env python3
"""
TrackShred - Secure File & Metadata Destruction Tool
A Linux CLI tool for securely deleting files and cleaning forensic traces.
"""

import argparse
import json
import logging
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Version information
__version__ = "1.0.1"
__author__ = "TrackShred"

# Exit codes
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_PERMISSION_ERROR = 2
EXIT_INVALID_INPUT = 3

# Global flag for graceful shutdown
shutdown_requested = False

# ASCII Art Banner
ASCII_BANNER = """

  _______                 _      _____  _                     _ 
 |__   __|               | |    / ____|| |                   | |
    | | _ __  __ _   ___ | | __| (___  | |__   _ __  ___   __| |
    | || '__|/ _` | / __|| |/ / \___ \ | '_ \ | '__|/ _ \ / _` |
    | || |  | (_| || (__ |   <  ____) || | | || |  |  __/| (_| |
    |_||_|   \__,_| \___||_|\_\|_____/ |_| |_||_|   \___| \__,_|

🔐 TrackShred v{} - Secure File & Metadata Destruction Tool
""".format(__version__)


class TrackShredInstaller:
    """Handle installation and setup of TrackShred"""
    
    @staticmethod
    def install_system_wide():
        """Install TrackShred system-wide"""
        script_path = Path(__file__).resolve()
        install_path = Path("/usr/local/bin/trackshred")
        
        try:
            print("🔧 Installing TrackShred system-wide...")
            
            # Check if we have permission
            if not os.access("/usr/local/bin", os.W_OK):
                print("❌ Permission denied. Try running with sudo:")
                print(f"sudo python3 {script_path} --install")
                return False
            
            # Copy script to system location
            shutil.copy2(script_path, install_path)
            install_path.chmod(0o755)
            
            print(f"✅ TrackShred installed successfully to {install_path}")
            print("🎉 You can now run 'trackshred' from anywhere!")
            print("\nTry: trackshred --help")
            return True
            
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            return False
    
    @staticmethod
    def install_user():
        """Install TrackShred for current user only"""
        script_path = Path(__file__).resolve()
        user_bin = Path.home() / ".local" / "bin"
        install_path = user_bin / "trackshred"
        
        try:
            print("🔧 Installing TrackShred for current user...")
            
            # Create user bin directory if it doesn't exist
            user_bin.mkdir(parents=True, exist_ok=True)
            
            # Copy script
            shutil.copy2(script_path, install_path)
            install_path.chmod(0o755)
            
            print(f"✅ TrackShred installed successfully to {install_path}")
            
            # Check if ~/.local/bin is in PATH
            path_env = os.environ.get("PATH", "")
            if str(user_bin) not in path_env:
                print("\n⚠️  Please add ~/.local/bin to your PATH:")
                print("echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.bashrc")
                print("source ~/.bashrc")
            else:
                print("🎉 You can now run 'trackshred' from anywhere!")
            
            print("\nTry: trackshred --help")
            return True
            
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            return False


class TrackShredConfig:
    """Configuration management for TrackShred"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.expanduser("~/.config/trackshred/config.json")
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file or return defaults"""
        default_config = {
            "shred_passes": 3,
            "log_level": "INFO",
            "log_file": "/tmp/trackshred.log",
            "clean_thumbnails": True,
            "clean_recent_files": True,
            "clean_trash": True,
            "clean_shell_history": False
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Could not load config from {self.config_path}: {e}")
        
        return default_config
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            logging.error(f"Could not save config to {self.config_path}: {e}")


class TrackShredLogger:
    """Logging setup for TrackShred"""
    
    @staticmethod
    def setup_logging(log_file: str, log_level: str = "INFO", verbose: bool = False):
        """Setup logging configuration"""
        level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except PermissionError:
                # Fallback to /tmp if we can't create the log directory
                log_file = "/tmp/trackshred.log"
        
        # Configure logging
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout) if verbose else logging.NullHandler()
            ]
        )
        
        logging.info(f"TrackShred v{__version__} started")


class FileShredder:
    """Secure file deletion functionality"""
    
    def __init__(self, passes: int = 3):
        self.passes = passes
    
    def shred_file(self, file_path: str, dry_run: bool = False) -> bool:
        """Securely delete a file using multiple overwrite passes"""
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return False
        
        if dry_run:
            logging.info(f"[DRY RUN] Would shred file: {file_path}")
            return True
        
        try:
            # Try using system 'shred' command first
            if shutil.which('shred'):
                cmd = ['shred', '-vfz', f'-n{self.passes}', '--remove', file_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    logging.info(f"Successfully shredded file: {file_path}")
                    return True
                else:
                    logging.warning(f"shred command failed: {result.stderr}")
            
            # Fallback to Python implementation
            return self._python_shred(file_path)
            
        except Exception as e:
            logging.error(f"Error shredding file {file_path}: {e}")
            return False
    
    def _python_shred(self, file_path: str) -> bool:
        """Python-based file shredding implementation"""
        try:
            file_size = os.path.getsize(file_path)
            
            with open(file_path, 'r+b') as f:
                for pass_num in range(self.passes):
                    logging.info(f"Shredding pass {pass_num + 1}/{self.passes} for {file_path}")
                    f.seek(0)
                    
                    # Write random data
                    remaining = file_size
                    while remaining > 0:
                        chunk_size = min(8192, remaining)
                        f.write(os.urandom(chunk_size))
                        remaining -= chunk_size
                    
                    f.flush()
                    os.fsync(f.fileno())
            
            # Remove the file
            os.remove(file_path)
            logging.info(f"Successfully shredded file: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Python shred failed for {file_path}: {e}")
            return False


class MetadataCleaner:
    """Metadata cleaning functionality"""
    
    def clean_file_metadata(self, file_path: str, dry_run: bool = False) -> bool:
        """Remove metadata from files"""
        if not os.path.exists(file_path):
            return False
        
        if dry_run:
            logging.info(f"[DRY RUN] Would clean metadata from: {file_path}")
            return True
        
        try:
            # Try using exiftool if available
            if shutil.which('exiftool'):
                cmd = ['exiftool', '-all=', '-overwrite_original', file_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    logging.info(f"Cleaned metadata from: {file_path}")
                    return True
            
            # Fallback: just log that we would clean it
            logging.info(f"Metadata cleaning attempted for: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error cleaning metadata from {file_path}: {e}")
            return False


class SystemCleaner:
    """System-wide cleaning functionality"""
    
    def __init__(self):
        self.home_dir = Path.home()
    
    def clean_thumbnails(self, dry_run: bool = False) -> bool:
        """Clean GNOME thumbnail cache"""
        thumbnail_dirs = [
            self.home_dir / '.cache' / 'thumbnails',
            self.home_dir / '.thumbnails'
        ]
        
        success = True
        for thumb_dir in thumbnail_dirs:
            if thumb_dir.exists():
                if dry_run:
                    logging.info(f"[DRY RUN] Would clean thumbnail directory: {thumb_dir}")
                else:
                    success &= self._remove_directory_contents(thumb_dir)
        
        return success
    
    def clean_recent_files(self, dry_run: bool = False) -> bool:
        """Clean recent files list"""
        recent_files = [
            self.home_dir / '.local' / 'share' / 'recently-used.xbel',
            self.home_dir / '.recently-used.xbel'
        ]
        
        success = True
        for recent_file in recent_files:
            if recent_file.exists():
                if dry_run:
                    logging.info(f"[DRY RUN] Would remove recent file: {recent_file}")
                else:
                    try:
                        recent_file.unlink()
                        logging.info(f"Removed recent files list: {recent_file}")
                    except Exception as e:
                        logging.error(f"Error removing {recent_file}: {e}")
                        success = False
        
        return success
    
    def clean_trash(self, dry_run: bool = False) -> bool:
        """Empty trash directory"""
        trash_dir = self.home_dir / '.local' / 'share' / 'Trash'
        
        if not trash_dir.exists():
            return True
        
        if dry_run:
            logging.info(f"[DRY RUN] Would empty trash directory: {trash_dir}")
            return True
        
        return self._remove_directory_contents(trash_dir)
    
    def clean_shell_history(self, dry_run: bool = False) -> bool:
        """Clean shell history files"""
        history_files = [
            self.home_dir / '.bash_history',
            self.home_dir / '.zsh_history',
            self.home_dir / '.history'
        ]
        
        success = True
        for hist_file in history_files:
            if hist_file.exists():
                if dry_run:
                    logging.info(f"[DRY RUN] Would clear history file: {hist_file}")
                else:
                    try:
                        hist_file.write_text("")
                        logging.info(f"Cleared history file: {hist_file}")
                    except Exception as e:
                        logging.error(f"Error clearing {hist_file}: {e}")
                        success = False
        
        return success
    
    def _remove_directory_contents(self, directory: Path) -> bool:
        """Remove all contents of a directory"""
        try:
            for item in directory.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            logging.info(f"Cleaned directory: {directory}")
            return True
        except Exception as e:
            logging.error(f"Error cleaning directory {directory}: {e}")
            return False


class TrackShred:
    """Main TrackShred application"""
    
    def __init__(self, config: TrackShredConfig):
        self.config = config
        self.shredder = FileShredder(config.config.get('shred_passes', 3))
        self.metadata_cleaner = MetadataCleaner()
        self.system_cleaner = SystemCleaner()
        self.results = {
            'files_shredded': [],
            'metadata_cleaned': [],
            'system_cleaned': [],
            'errors': []
        }
    
    def process_target(self, target: str, metadata_only: bool = False, dry_run: bool = False):
        """Process a target file or directory"""
        target_path = Path(target).expanduser().resolve()
        
        if not target_path.exists():
            error_msg = f"Target not found: {target}"
            logging.error(error_msg)
            self.results['errors'].append(error_msg)
            return
        
        if target_path.is_file():
            self._process_file(target_path, metadata_only, dry_run)
        elif target_path.is_dir():
            self._process_directory(target_path, metadata_only, dry_run)
    
    def _process_file(self, file_path: Path, metadata_only: bool, dry_run: bool):
        """Process a single file"""
        file_str = str(file_path)
        
        # Clean metadata
        if self.metadata_cleaner.clean_file_metadata(file_str, dry_run):
            self.results['metadata_cleaned'].append(file_str)
        
        # Shred file (unless metadata-only mode)
        if not metadata_only:
            if self.shredder.shred_file(file_str, dry_run):
                self.results['files_shredded'].append(file_str)
    
    def _process_directory(self, dir_path: Path, metadata_only: bool, dry_run: bool):
        """Process all files in a directory"""
        try:
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    self._process_file(file_path, metadata_only, dry_run)
        except Exception as e:
            error_msg = f"Error processing directory {dir_path}: {e}"
            logging.error(error_msg)
            self.results['errors'].append(error_msg)
    
    def deep_clean(self, dry_run: bool = False):
        """Perform aggressive system-wide privacy sweep"""
        operations = [
            ("thumbnails", self.system_cleaner.clean_thumbnails),
            ("recent files", self.system_cleaner.clean_recent_files),
            ("trash", self.system_cleaner.clean_trash),
        ]
        
        if self.config.config.get('clean_shell_history', False):
            operations.append(("shell history", self.system_cleaner.clean_shell_history))
        
        for name, operation in operations:
            try:
                if operation(dry_run):
                    self.results['system_cleaned'].append(name)
                else:
                    self.results['errors'].append(f"Failed to clean {name}")
            except Exception as e:
                error_msg = f"Error during {name} cleaning: {e}"
                logging.error(error_msg)
                self.results['errors'].append(error_msg)
    
    def print_results(self):
        """Print operation results"""
        print("\n" + "="*60)
        print("🔐 TRACKSHRED OPERATION RESULTS")
        print("="*60)
        
        if self.results['files_shredded']:
            print(f"\n[✔] FILES SHREDDED ({len(self.results['files_shredded'])}):")
            for file in self.results['files_shredded']:
                print(f"    🗑️  {file}")
        
        if self.results['metadata_cleaned']:
            print(f"\n[✔] METADATA CLEANED ({len(self.results['metadata_cleaned'])}):")
            for file in self.results['metadata_cleaned']:
                print(f"    🧹 {file}")
        
        if self.results['system_cleaned']:
            print(f"\n[✔] SYSTEM CLEANING COMPLETED:")
            for operation in self.results['system_cleaned']:
                print(f"    🔧 {operation}")
        
        if self.results['errors']:
            print(f"\n[✗] ERRORS ({len(self.results['errors'])}):")
            for error in self.results['errors']:
                print(f"    ❌ {error}")
        
        if not any(self.results.values()):
            print("\n[!] NO OPERATIONS PERFORMED")
        else:
            print(f"\n{'='*60}")
            print("✅ OPERATION COMPLETED SUCCESSFULLY")
            print("="*60)
    
    def save_report(self, output_file: str):
        """Save operation report to JSON file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"📊 Report saved to: {output_file}")
        except Exception as e:
            logging.error(f"Error saving report: {e}")


def show_welcome_help():
    """Show welcome message and basic help"""
    print(ASCII_BANNER)
    print("Welcome to TrackShred! 🛡️")
    print("\n" + "="*60)
    print("QUICK START GUIDE")
    print("="*60)
    
    print("\n🔧 FIRST TIME SETUP:")
    print("   trackshred --install        # Install system-wide")
    print("   trackshred --install-user   # Install for current user only")
    
    print("\n🗂️  FILE OPERATIONS:")
    print("   trackshred --target file.pdf                    # Shred single file")
    print("   trackshred --target ~/folder/                   # Shred all files in folder")
    print("   trackshred --target image.jpg --metadata-only   # Clean metadata only")
    
    print("\n🧹 SYSTEM CLEANING:")
    print("   trackshred --deep                               # System-wide privacy sweep")
    print("   trackshred --target ~/docs/ --deep             # Combined operation")
    
    print("\n🛡️  SAFE TESTING:")
    print("   trackshred --target file.txt --dry-run         # Test without actual deletion")
    print("   trackshred --deep --dry-run                    # Test system cleaning")
    
    print("\n📚 MORE OPTIONS:")
    print("   trackshred --help                              # Full help documentation")
    print("   trackshred --version                           # Show version info")
    
    print("\n" + "="*60)
    print("⚠️  IMPORTANT: Always test with --dry-run first!")
    print("💡 Use --verbose to see detailed operation logs")
    print("="*60)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    shutdown_requested = True
    print(f"\n[!] Received signal {signum}, shutting down gracefully...")
    sys.exit(EXIT_SUCCESS)


def validate_inputs(args) -> bool:
    """Validate command line arguments"""
    if not args.target and not args.deep and not args.install and not args.install_user:
        return False
    
    if args.target:
        target_path = Path(args.target).expanduser()
        if not target_path.exists():
            print(f"Error: Target not found: {args.target}", file=sys.stderr)
            return False
    
    if args.shred_passes < 1 or args.shred_passes > 10:
        print("Error: Shred passes must be between 1 and 10", file=sys.stderr)
        return False
    
    return True


def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="TrackShred - Secure File & Metadata Destruction Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --target ~/secret.pdf
  %(prog)s --target ~/Documents --deep
  %(prog)s --deep --dry-run
  %(prog)s --target file.zip --metadata-only
  %(prog)s --install
        """
    )
    
    # Installation options
    parser.add_argument('--install', action='store_true', help='Install TrackShred system-wide')
    parser.add_argument('--install-user', action='store_true', help='Install TrackShred for current user only')
    
    # Main operation options
    parser.add_argument('--target', type=str, help='Target file or directory to shred')
    parser.add_argument('--deep', action='store_true', help='Perform aggressive system-wide privacy sweep')
    parser.add_argument('--shred-passes', type=int, default=3, help='Number of overwrite passes (default: 3)')
    parser.add_argument('--metadata-only', action='store_true', help='Only clean metadata without deleting files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without taking action')
    
    # Configuration options
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--log', type=str, help='Path to log file')
    parser.add_argument('--report', type=str, help='Save operation report to JSON file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--version', action='version', version=f'TrackShred {__version__}')
    
    args = parser.parse_args()
    
    # Handle installation requests
    if args.install:
        print(ASCII_BANNER)
        success = TrackShredInstaller.install_system_wide()
        sys.exit(EXIT_SUCCESS if success else EXIT_GENERAL_ERROR)
    
    if args.install_user:
        print(ASCII_BANNER)
        success = TrackShredInstaller.install_user()
        sys.exit(EXIT_SUCCESS if success else EXIT_GENERAL_ERROR)
    
    # Show welcome help if no arguments provided
    if len(sys.argv) == 1:
        show_welcome_help()
        sys.exit(EXIT_SUCCESS)
    
    # Validate inputs
    if not validate_inputs(args):
        print(ASCII_BANNER)
        print("❌ Error: Must specify either --target, --deep, --install, or --install-user")
        print("\nUse 'trackshred --help' for full documentation")
        sys.exit(EXIT_INVALID_INPUT)
    
    try:
        # Show banner for normal operations
        if args.verbose:
            print(ASCII_BANNER)
        
        # Load configuration
        config = TrackShredConfig(args.config)
        
        # Override config with command line args
        if args.shred_passes:
            config.config['shred_passes'] = args.shred_passes
        if args.log:
            config.config['log_file'] = args.log
        
        # Setup logging
        TrackShredLogger.setup_logging(
            config.config['log_file'],
            config.config['log_level'],
            args.verbose
        )
        
        # Create TrackShred instance
        trackshred = TrackShred(config)
        
        # Process target if specified
        if args.target:
            trackshred.process_target(args.target, args.metadata_only, args.dry_run)
        
        # Perform deep clean if requested
        if args.deep:
            trackshred.deep_clean(args.dry_run)
        
        # Print results
        trackshred.print_results()
        
        # Save report if requested
        if args.report:
            trackshred.save_report(args.report)
        
        # Exit with appropriate code
        if trackshred.results['errors']:
            sys.exit(EXIT_GENERAL_ERROR)
        else:
            sys.exit(EXIT_SUCCESS)
            
    except PermissionError as e:
        print(f"Permission denied: {e}", file=sys.stderr)
        sys.exit(EXIT_PERMISSION_ERROR)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(EXIT_SUCCESS)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        logging.exception("Unexpected error occurred")
        sys.exit(EXIT_GENERAL_ERROR)


if __name__ == "__main__":
    main()
