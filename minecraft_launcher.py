import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import minecraft_launcher_lib as mclib
import subprocess
import threading
import json
from functools import partial

class MinecraftLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Minecraft Launcher")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        # Minecraft directory
        self.minecraft_dir = os.path.join(os.getenv('APPDATA'), '.minecraft')
        if not os.path.exists(self.minecraft_dir):
            os.makedirs(self.minecraft_dir)
        
        # Variables
        self.username_var = tk.StringVar(value="Player")
        self.version_var = tk.StringVar()
        self.ram_var = tk.StringVar(value="4")
        self.java_path_var = tk.StringVar(value=self.find_java())
        
        # Setup UI
        self.setup_ui()
        
        # Load versions
        self.load_versions()
    
    def find_java(self):
        try:
            java_path = mclib.utils.get_java_executable()
            return java_path
        except:
            return "java"  # Fallback to system PATH
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel (version selection)
        left_frame = ttk.Frame(main_frame, padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Version list
        ttk.Label(left_frame, text="Available Versions:").pack(anchor=tk.W)
        self.version_listbox = tk.Listbox(left_frame, width=30, height=20)
        self.version_listbox.pack(fill=tk.Y, expand=True)
        
        # Right panel (settings)
        right_frame = ttk.Frame(main_frame, padding="5")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Username
        ttk.Label(right_frame, text="Username:").pack(anchor=tk.W)
        ttk.Entry(right_frame, textvariable=self.username_var).pack(fill=tk.X)
        
        # RAM allocation
        ttk.Label(right_frame, text="RAM (GB):").pack(anchor=tk.W)
        ttk.Combobox(right_frame, textvariable=self.ram_var, values=["1", "2", "3", "4", "6", "8", "12", "16"]).pack(fill=tk.X)
        
        # Java path
        ttk.Label(right_frame, text="Java Path:").pack(anchor=tk.W)
        java_frame = ttk.Frame(right_frame)
        java_frame.pack(fill=tk.X)
        ttk.Entry(java_frame, textvariable=self.java_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(java_frame, text="Browse", command=self.browse_java).pack(side=tk.RIGHT)
        
        # Launch button
        ttk.Button(right_frame, text="Launch Minecraft", command=self.launch_minecraft).pack(pady=10)
        
        # Version info
        self.version_info = ttk.Label(right_frame, text="", wraplength=400)
        self.version_info.pack(fill=tk.X, pady=10)
        
        # Bind version selection
        self.version_listbox.bind('<<ListboxSelect>>', self.show_version_info)
    
    def browse_java(self):
        path = filedialog.askopenfilename(
            title="Select Java Executable",
            filetypes=(("Java Executable", "java.exe javaw.exe"), ("All Files", "*.*"))
        )
        if path:
            self.java_path_var.set(path)
    
    def load_versions(self):
        try:
            # Get all version types
            vanilla_versions = mclib.utils.get_version_list()
            forge_versions = mclib.forge.list_forge_versions()
            fabric_versions = mclib.fabric.get_all_minecraft_versions()
            
            # Add vanilla versions
            for version in vanilla_versions:
                self.version_listbox.insert(tk.END, f"Vanilla {version['id']}")
                if version['type'] == 'old_alpha':
                    self.version_listbox.insert(tk.END, f"Alpha {version['id']}")
                elif version['type'] == 'old_beta':
                    self.version_listbox.insert(tk.END, f"Beta {version['id']}")
            
            # Add Forge versions
            for version in forge_versions:
                self.version_listbox.insert(tk.END, f"Forge {version}")
            
            # Add Fabric versions
            for version in fabric_versions:
                self.version_listbox.insert(tk.END, f"Fabric {version}")
            
            # OptiFine versions currently not supported in the latest minecraft-launcher-lib
            # You would need to implement custom support for OptiFine
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load versions: {str(e)}")
    
    def show_version_info(self, event):
        try:
            selection = self.version_listbox.get(self.version_listbox.curselection())
            version_type, version_id = selection.split(" ", 1)
            
            info = f"Version: {version_id}\nType: {version_type}\n"
            
            if version_type == "Vanilla":
                version_data = mclib.utils.get_version_list()
                for v in version_data:
                    if v['id'] == version_id:
                        info += f"Release date: {v['releaseTime']}\n"
                        info += f"Type: {v['type']}\n"
                        break
            elif version_type == "Forge":
                info += "Forge is a modding platform that provides compatibility between mods.\n"
            elif version_type == "Fabric":
                info += "Fabric is a lightweight modding toolchain for Minecraft.\n"
            elif version_type in ["Alpha", "Beta"]:
                info += f"Old {version_type} version of Minecraft\n"
            
            self.version_info.config(text=info)
            self.version_var.set(version_id)
        except:
            pass
    
    def launch_minecraft(self):
        try:
            version = self.version_listbox.get(self.version_listbox.curselection())
            version_type, version_id = version.split(" ", 1)
            
            username = self.username_var.get()
            if not username:
                messagebox.showerror("Error", "Please enter a username")
                return
            
            ram = self.ram_var.get()
            if not ram.isdigit() or int(ram) < 1:
                messagebox.showerror("Error", "Please enter a valid RAM amount")
                return
            
            java_path = self.java_path_var.get()
            if not java_path or not os.path.exists(java_path):
                messagebox.showerror("Error", "Java path is invalid")
                return
            
            # Prepare launch options
            options = {
                'username': username,
                'uuid': '',
                'token': '',
                'jvmArguments': [f"-Xmx{ram}G", f"-Xms{ram}G"],
                'launcherName': "Python Minecraft Launcher",
                'launcherVersion': "1.0",
                'javaExecutable': java_path
            }
            
            # Install version if needed
            if not mclib.utils.is_version_valid(version_id, self.minecraft_dir):
                threading.Thread(target=self.install_version, args=(version_type, version_id, options)).start()
            else:
                threading.Thread(target=self.run_minecraft, args=(version_id, options)).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Minecraft: {str(e)}")
    
    def install_version(self, version_type, version_id, options):
        try:
            if version_type == "Vanilla":
                mclib.install.install_minecraft_version(version_id, self.minecraft_dir)
            elif version_type == "Forge":
                mclib.forge.install_forge_version(version_id, self.minecraft_dir)
            elif version_type == "Fabric":
                mclib.fabric.install_minecraft_version(version_id, self.minecraft_dir)
                mclib.fabric.install_fabric(version_id, self.minecraft_dir)
            
            self.run_minecraft(version_id, options)
        except Exception as e:
            messagebox.showerror("Error", f"Installation failed: {str(e)}")
    
    def run_minecraft(self, version_id, options):
        try:
            command = mclib.command.get_minecraft_command(version_id, self.minecraft_dir, options)
            subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Minecraft: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    launcher = MinecraftLauncher(root)
    root.mainloop()