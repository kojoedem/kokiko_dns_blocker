import tkinter as tk
from tkinter import messagebox, ttk
from netmiko import ConnectHandler

def connect_to_router(host, username, password):
    """Establish connection to the MikroTik router."""
    return ConnectHandler(
        device_type="mikrotik_routeros",
        host=host,
        username=username,
        password=password
    )

def block_website():
    """Block the specified website."""
    website = block_entry.get()
    if not website:
        messagebox.showerror("Error", "Please enter a website address to block.")
        return

    try:
        # Remove any existing DNS entry or NAT rules for the website
        net_connect.send_command(f"ip dns static remove [find name={website}]")
        net_connect.send_command(f"ip firewall nat remove [find comment={website}]")
        
        # Add static DNS entry
        dns_command = f"ip dns static add name={website} address=127.0.0.1"
        net_connect.send_config_set([dns_command])
        
        # Add NAT rules with a comment referencing the website
        nat_commands = [
            f"ip firewall nat add chain=dstnat dst-port=53 action=redirect to-ports=53 protocol=tcp comment={website}",
            f"ip firewall nat add chain=dstnat dst-port=53 action=redirect to-ports=53 protocol=udp comment={website}"
        ]
        net_connect.send_config_set(nat_commands)
        
        messagebox.showinfo("Success", f"Website '{website}' has been blocked.")
        refresh_blocked_websites()
    except Exception as e:
        messagebox.showerror("Error", str(e))


def refresh_blocked_websites():
    """Refresh the list of blocked websites."""
    try:
        # Fetch the static DNS entries
        output = net_connect.send_command("ip dns static print detail")
        blocked_list.delete(0, tk.END)  # Clear the listbox
        # print(output)
        # Parse output to find blocked websites
        for line in output.splitlines():
            if "name=" in line:
                # Extract the 'name' field value
                parts = line.split()
                for part in parts:
                    if part.startswith("name="):
                        website = part.split("=", 1)[1]  # Get the value after "name="
                    
                        blocked_list.insert(tk.END, website)
                        break
    except Exception as e:
        messagebox.showerror("Error", str(e))

def unblock_website():
    """Unblock the selected website and remove associated NAT rules."""
    selected = blocked_list.curselection()
    if not selected:
        messagebox.showerror("Error", "Please select a website to unblock.")
        return
    
    website = blocked_list.get(selected)
    try:
        # Remove the static DNS entry
        dns_remove_command = f"ip dns static remove [find name={website}]"
        net_connect.send_command(dns_remove_command)
        
        # Find and remove associated NAT rules by comment
        nat_find_command = f"ip firewall nat remove [find comment={website}]"
        net_connect.send_command(nat_find_command)
        
        messagebox.showinfo("Success", f"Website '{website}' and its NAT rules have been unblocked.")
        refresh_blocked_websites()
    except Exception as e:
        messagebox.showerror("Error", str(e))


def login():
    """Login to the router and initialize the session."""
    global net_connect
    host = host_entry.get()
    username = username_entry.get()
    password = password_entry.get()
    
    try:
        net_connect = connect_to_router(host, username, password)
        messagebox.showinfo("Success", "Connected to the MikroTik router.")
        refresh_blocked_websites()
    except Exception as e:
        messagebox.showerror("Connection Error", str(e))
       

# GUI
root = tk.Tk()
root.title("KOLIKO DNS BLOCKER")

# Router Credentials
tk.Label(root, text="Router IP:").grid(row=0, column=0, padx=10, pady=5)
host_entry = tk.Entry(root)
host_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Username:").grid(row=1, column=0, padx=10, pady=5)
username_entry = tk.Entry(root)
username_entry.grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="Password:").grid(row=2, column=0, padx=10, pady=5)
password_entry = tk.Entry(root, show="*")
password_entry.grid(row=2, column=1, padx=10, pady=5)

login_button = tk.Button(root, text="Login", command=login)
login_button.grid(row=3, column=0, columnspan=2, pady=10)

# Block Website
tk.Label(root, text="Website to Block:").grid(row=4, column=0, padx=10, pady=5)
block_entry = tk.Entry(root)
block_entry.grid(row=4, column=1, padx=10, pady=5)

block_button = tk.Button(root, text="Block Website", command=block_website)
block_button.grid(row=5, column=0, columnspan=2, pady=10)

# Blocked Websites List
tk.Label(root, text="Blocked Websites:").grid(row=6, column=0, padx=10, pady=5)
blocked_list = tk.Listbox(root, height=10, width=40)
blocked_list.grid(row=6, column=1, padx=10, pady=5)

unblock_button = tk.Button(root, text="Unblock Website", command=unblock_website)
unblock_button.grid(row=7, column=0, columnspan=2, pady=10)

root.mainloop()
