#!/usr/bin/env python3
"""
Cron Job Setup Script
Creates cron job entries for automated video generation
"""

import os
import sys
import subprocess
from pathlib import Path

def get_project_path():
    """Get the absolute path to the project directory"""
    return Path(__file__).parent.absolute()

def get_python_path():
    """Get the path to the uv-managed Python interpreter"""
    project_path = get_project_path()
    venv_python = project_path / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    else:
        # Fallback to system python if venv not found
        return sys.executable

def create_cron_entry(schedule="0 */6 * * *"):
    """
    Create a cron job entry for the video automation
    Default: Every 6 hours
    """
    project_path = get_project_path()
    python_path = get_python_path()
    script_path = project_path / "main.py"
    
    # Create the cron command
    cron_command = f"{python_path} {script_path}"
    
    # Full cron entry with logging
    log_path = project_path / "cron_video_automation.log"
    cron_entry = f"{schedule} cd {project_path} && {cron_command} >> {log_path} 2>&1"
    
    return cron_entry

def install_cron_job(schedule="0 */6 * * *"):
    """Install the cron job"""
    cron_entry = create_cron_entry(schedule)
    
    try:
        # Get current cron jobs
        result = subprocess.run(
            ["crontab", "-l"], 
            capture_output=True, 
            text=True, 
            check=False
        )
        
        current_crontab = result.stdout if result.returncode == 0 else ""
        
        # Check if our job already exists
        if "main.py" in current_crontab and str(get_project_path()) in current_crontab:
            print("Cron job already exists. Use update_cron_job() to modify it.")
            return False
        
        # Add our job to the existing crontab
        new_crontab = current_crontab + "\n" + cron_entry + "\n"
        
        # Install the new crontab
        process = subprocess.Popen(
            ["crontab", "-"], 
            stdin=subprocess.PIPE, 
            text=True
        )
        process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            print(f"Cron job installed successfully!")
            print(f"Schedule: {schedule}")
            print(f"Command: {cron_entry}")
            return True
        else:
            print("Failed to install cron job")
            return False
            
    except Exception as e:
        print(f"Error installing cron job: {e}")
        return False

def remove_cron_job():
    """Remove the video automation cron job"""
    try:
        # Get current cron jobs
        result = subprocess.run(
            ["crontab", "-l"], 
            capture_output=True, 
            text=True, 
            check=False
        )
        
        if result.returncode != 0:
            print("No cron jobs found")
            return False
        
        current_crontab = result.stdout
        project_path_str = str(get_project_path())
        
        # Filter out our cron job
        lines = current_crontab.split('\n')
        filtered_lines = [
            line for line in lines 
            if not (project_path_str in line and "main.py" in line)
        ]
        
        new_crontab = '\n'.join(filtered_lines)
        
        # Install the filtered crontab
        process = subprocess.Popen(
            ["crontab", "-"], 
            stdin=subprocess.PIPE, 
            text=True
        )
        process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            print("Cron job removed successfully!")
            return True
        else:
            print("Failed to remove cron job")
            return False
            
    except Exception as e:
        print(f"Error removing cron job: {e}")
        return False

def show_cron_schedules():
    """Show common cron schedule examples"""
    schedules = {
        "Every hour": "0 * * * *",
        "Every 2 hours": "0 */2 * * *",
        "Every 6 hours": "0 */6 * * *",
        "Every 12 hours": "0 */12 * * *",
        "Daily at 9 AM": "0 9 * * *",
        "Daily at 6 PM": "0 18 * * *",
        "Twice daily (9 AM and 6 PM)": "0 9,18 * * *",
        "Weekly on Sunday at 9 AM": "0 9 * * 0",
        "Every weekday at 10 AM": "0 10 * * 1-5"
    }
    
    print("\nCommon Cron Schedule Examples:")
    print("=" * 50)
    for description, schedule in schedules.items():
        print(f"{description:30} {schedule}")
    print("\nFormat: minute hour day-of-month month day-of-week")
    print("Use * for 'any value'")

def main():
    """Main function for cron setup"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup cron job for video automation")
    parser.add_argument(
        "--install", 
        action="store_true", 
        help="Install cron job"
    )
    parser.add_argument(
        "--remove", 
        action="store_true", 
        help="Remove cron job"
    )
    parser.add_argument(
        "--schedule", 
        default="0 */6 * * *", 
        help="Cron schedule (default: every 6 hours)"
    )
    parser.add_argument(
        "--show-schedules", 
        action="store_true", 
        help="Show common cron schedule examples"
    )
    
    args = parser.parse_args()
    
    if args.show_schedules:
        show_cron_schedules()
        return
    
    if args.install:
        success = install_cron_job(args.schedule)
        if success:
            print("\n✅ Setup complete!")
            print("\nNext steps:")
            print("1. Make sure your API keys are set in .env file")
            print("2. Test the script manually: uv run main.py")
            print("3. Check cron logs: tail -f cron_video_automation.log")
        sys.exit(0 if success else 1)
    
    elif args.remove:
        success = remove_cron_job()
        sys.exit(0 if success else 1)
    
    else:
        print("Use --install to install cron job or --remove to remove it")
        print("Use --help for more options")
        show_cron_schedules()

if __name__ == "__main__":
    main()