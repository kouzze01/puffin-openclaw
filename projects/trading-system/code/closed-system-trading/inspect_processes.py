import psutil
import datetime

print(f"{'PID':<10} {'Started':<20} {'CommandLine'}")
print("-" * 100)

for proc in psutil.process_iter(['pid', 'name', 'create_time', 'cmdline']):
    try:
        if 'python' in proc.info['name'].lower():
            started = datetime.datetime.fromtimestamp(proc.info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
            cmdline = " ".join(proc.info['cmdline']) if proc.info['cmdline'] else ""
            print(f"{proc.info['pid']:<10} {started:<20} {cmdline}")
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass
