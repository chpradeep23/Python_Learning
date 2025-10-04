from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os


# Define device parameters

USERNAME = os.environ.get('SSH_USER')
PASSWORD = os.environ.get('SSH_PASSWORD')
device_parameters = {
#    "device_type": "cisco_ios",
    "device_type": "arista_eos",    #Use this if you are connecting to Arista_EOS.
#    "host": "10.155.76.10",  # Replace with your device's IP address if you want to run for device locally rather than from a file.
    "username": USERNAME,  # Replace with your SSH username
    "password": PASSWORD,  # Replace with your SSH password
    "secret": PASSWORD,  # Replace with your enable password if required
#    "port": 22, # Replace with your port that you use for SSH
}


# --- Read IP addresses from the file and build the list of dictionaries ---
device_list = []
commands = ["int et1/2",
            "no des test"
]
try:
    with open("ip_list.txt", "r") as file:
        for ip in file:
            ip = ip.strip() # Strip whitespace (like newlines) from the IP address
            device_info = device_parameters.copy() # Creates a copy of a dictionary called device_parameters # Use .copy() to avoid overwriting
            device_info["host"] = ip #Sets the "host" key in the copied dictionary to the current IP address
            device_list.append(device_info) #Adds the modified dictionary to a list called device_list
except FileNotFoundError:
    print("Error: ip_list.txt not found.")
    exit()

# --- Loop through the device list and connect ---
def connect_and_run(device):
    result = {"host": device["host"], "output": {}, "status": "success"}  #for device in device_list:
    try:
        print(f"Connecting to {device['host']}...")
        connection = ConnectHandler(**device)
        for cmd in commands:
            print(f"{device['host']} Running command: {cmd}")
            output = connection.send_config_set(commands)
            result["output"] = {"all_commands": output}
        connection.disconnect()
        if "% Invalid input" in output:
            result["status"] = "failed"
            result["error"] = "Invalid input detected in command output"
        print(f"{device['host']} Done.")
    except NetmikoTimeoutException:
        result["status"] = "timeout"
        result["error"] = "Connection timed out"
    except NetmikoAuthenticationException:
        result["status"] = "auth_failed"
        result["error"] = "Authentication failed" 
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    return result

# Run all devices in parallel
def main():
    results = []
    start_time = datetime.now()


    max_threads = 5  # Adjust based on your system and network
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(connect_and_run, device) for device in device_list]
        for future in as_completed(futures):
            results.append(future.result())

    # ──────────────────────────────
    # Print summary
    print("\n" + "="*50)
    print("COMMAND EXECUTION SUMMARY".center(50))
    print("="*50)
    successful = [r["host"] for r in results if r["status"] == "success"]
    failed = [r["host"] for r in results if r["status"] != "success"]

    
    print(f"✅ Successful devices ({len(successful)}):")
    for ip in successful:
            print(f"   - {ip}")
    print(f"\n❌ Failed devices ({len(failed)}):")
    for ip in failed:
            print(f"   - {ip}")
    print("=================================================\n")
if __name__ == "__main__":
    main()
