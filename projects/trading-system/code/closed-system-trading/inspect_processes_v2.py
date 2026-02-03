import subprocess
import os

print(f"{'ProcessId':<10} {'CreationDate':<20} {'CommandLine'}")
print("-" * 100)

try:
    # Use wmic to get process details
    cmd = 'wmic process where "name=\'python.exe\'" get ProcessId,CreationDate,CommandLine /format:list'
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    
    procs = output.split('\r\r\n\r\r\n')
    for p in procs:
        lines = p.strip().split('\r\r\n')
        data = {}
        for line in lines:
            if '=' in line:
                k, v = line.split('=', 1)
                data[k.strip()] = v.strip()
        
        if data:
            pid = data.get('ProcessId', 'N/A')
            cdate = data.get('CreationDate', 'N/A')
            cmdline = data.get('CommandLine', 'N/A')
            
            # Format creation date if possible (YYYYMMDDHHMMSS)
            if cdate != 'N/A':
                cdate = f"{cdate[:4]}-{cdate[4:6]}-{cdate[6:8]} {cdate[8:10]}:{cdate[10:12]}:{cdate[12:14]}"
                
            print(f"{pid:<10} {cdate:<20} {cmdline}")

except Exception as e:
    print(f"Error: {e}")
