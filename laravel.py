import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import datetime
import re

# Define a filename to store project paths and logs
CONFIG_FILE = 'laravel_projects.json'
LOG_FILE = 'command_log.txt'

class LaravelGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Laravel Command Runner')
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Main tab
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text='Commands')
        
        # Routes tab
        self.routes_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.routes_frame, text='Routes')
        
        self.project_paths = self.load_paths()
        self.process = None
        self.server_url = None
        
        # Create main tab elements
        self.create_main_tab()
        
        # Create routes tab elements
        self.create_routes_tab()
        
        # Server URL Frame
        self.create_server_url_frame()
        style = ttk.Style()
        # برای ویندوز
        style.configure('Danger.TButton', 
                       padding=5,
                       background='#ff4444',
                       foreground='white')
        # برای macOS و Linux
        style.map('Danger.TButton',
                 background=[('active', '#ff6666')],
                 foreground=[('active', 'white')])

    def create_server_url_frame(self):
        """Create a frame to display the server URL when 'serve' command is running"""
        self.url_frame = ttk.LabelFrame(self.main_frame, text="Server URL")
        self.url_frame.pack(fill='x', padx=10, pady=5)
        
        self.url_label = ttk.Label(self.url_frame, text="Not running", font=('Arial', 10))
        self.url_label.pack(pady=5)
        
        self.copy_url_button = ttk.Button(self.url_frame, text="Copy URL", command=self.copy_url_to_clipboard)
        self.copy_url_button.pack(pady=5)
        self.copy_url_button.config(state='disabled')

    def copy_url_to_clipboard(self):
        """Copy the server URL to clipboard"""
        if self.server_url:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.server_url)
            messagebox.showinfo("Success", "URL copied to clipboard!")

    def create_main_tab(self):
        """Create elements for the main commands tab"""
        self.path_label = ttk.Label(self.main_frame, text="Select Laravel Project Path:")
        self.path_label.pack(pady=10)

        self.path_entry = ttk.Entry(self.main_frame, width=50)
        self.path_entry.pack(padx=10)

        self.browse_button = ttk.Button(self.main_frame, text="Browse", command=self.browse_project)
        self.browse_button.pack(pady=5)

        self.save_button = ttk.Button(self.main_frame, text="Save Project Path", command=self.save_project_path)
        self.save_button.pack(pady=5)

        self.command_label = ttk.Label(self.main_frame, text="Choose Laravel or Composer Command:")
        self.command_label.pack(pady=10)

        self.commands = [
        "serve",
        "migrate",
        "migrate:rollback",
        "make:controller",
        "make:model",
        "make:migration",
        "make:seeder",
        "make:request",
        "make:middleware",
        "make:event",
        "route:list",
        "cache:clear",
        "config:clear",
        "view:clear",
        "optimize",
        "composer install",
        "composer update",
        "composer require",
        "composer dump-autoload"
    ]

        self.command_var = tk.StringVar()
        self.command_menu = ttk.Combobox(self.main_frame, textvariable=self.command_var, values=self.commands, width=47)
        self.command_menu.pack(pady=5)

        self.param_label = ttk.Label(self.main_frame, text="Enter Parameters (optional):")
        self.param_label.pack(pady=5)

        self.param_entry = ttk.Entry(self.main_frame, width=50)
        self.param_entry.pack(pady=5)

        self.run_button = ttk.Button(self.main_frame, text="Run Command", command=self.run_laravel_command)
        self.run_button.pack(pady=5)

        self.stop_button = ttk.Button(self.main_frame, text="Stop Command", command=self.stop_command, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.saved_paths_label = ttk.Label(self.main_frame, text="Saved Projects:")
        self.saved_paths_label.pack(pady=10)

        self.paths_listbox = tk.Listbox(self.main_frame, height=6, width=50)
        self.paths_listbox.pack(padx=10, pady=5)
        self.update_paths_listbox()

        self.paths_listbox.bind('<<ListboxSelect>>', self.on_path_selected)

        self.delete_button = ttk.Button(self.main_frame, text="Delete Selected Path", command=self.delete_selected_path)
        self.delete_button.pack(pady=5)

        self.log_label = ttk.Label(self.main_frame, text="Command Logs:")
        self.log_label.pack(pady=10)

    # Create frame for log area and clear button
        log_frame = ttk.Frame(self.main_frame)
        log_frame.pack(fill='both', expand=True, padx=10)

    # Add Text widget for logs with scrollbar
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side='right', fill='y')

        self.log_text = tk.Text(log_frame, height=10, width=50, yscrollcommand=log_scroll.set)
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scroll.config(command=self.log_text.yview)

    # Add "Clear Logs" button below the log section
        self.clear_logs_button = ttk.Button(self.main_frame, text="Clear Logs", command=self.clear_logs)
        self.clear_logs_button.pack(pady=5)

       
    def clear_logs(self):
        """Clear the log file and text box."""
        try:
            result = messagebox.askyesno(
                "Confirm",
                "Are you sure you want to clear all logs?",
                icon='warning'
            )
            
            if result:
                # Clear log file
                with open(LOG_FILE, 'w', encoding='utf-8') as log_file:
                    log_file.write('')
                
                # Clear log display
                self.log_text.delete(1.0, tk.END)
                
                # Add initial message
                clear_message = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Logs cleared.\n"
                self.log_text.insert(tk.END, clear_message)
                
                # Also write this message to log file
                with open(LOG_FILE, 'w', encoding='utf-8') as log_file:
                    log_file.write(clear_message)
                
                messagebox.showinfo("Success", "Logs cleared successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear logs: {e}")
        

    def create_routes_tab(self):
        """Create elements for the routes tab"""
        # Search frame
        search_frame = ttk.Frame(self.routes_frame)
        search_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(search_frame, text="Search Routes:").pack(side='left', padx=5)
        self.route_search_var = tk.StringVar()
        self.route_search_var.trace('w', self.filter_routes)
        self.route_search_entry = ttk.Entry(search_frame, textvariable=self.route_search_var, width=40)
        self.route_search_entry.pack(side='left', padx=5)
        
        ttk.Button(search_frame, text="Refresh Routes", command=self.refresh_routes).pack(side='left', padx=5)
        
        # Create Treeview for routes
        self.routes_tree = ttk.Treeview(self.routes_frame, columns=('Method', 'URI', 'Name', 'Action'), show='headings')
        
        # Configure columns
        self.routes_tree.heading('Method', text='Method')
        self.routes_tree.heading('URI', text='URI')
        self.routes_tree.heading('Name', text='Name')
        self.routes_tree.heading('Action', text='Action')
        
        self.routes_tree.column('Method', width=100)
        self.routes_tree.column('URI', width=200)
        self.routes_tree.column('Name', width=150)
        self.routes_tree.column('Action', width=300)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.routes_frame, orient='vertical', command=self.routes_tree.yview)
        self.routes_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack elements
        self.routes_tree.pack(side='left', fill='both', expand=True, padx=10, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)

    def filter_routes(self, *args):
        """Filter routes based on search text"""
        search_text = self.route_search_var.get().lower()
        
        # Clear current items
        for item in self.routes_tree.get_children():
            self.routes_tree.delete(item)
        
        # Add filtered items
        for route in self.routes_data:
            if (search_text in route['uri'].lower() or 
                search_text in route['method'].lower() or 
                search_text in (route['name'] or '').lower() or 
                search_text in route['action'].lower()):
                self.routes_tree.insert('', 'end', values=(
                    route['method'],
                    route['uri'],
                    route['name'] or '',
                    route['action']
                ))

    def refresh_routes(self):
        """Refresh the routes list"""
        project_path = self.path_entry.get()
        if not os.path.isdir(project_path):
            messagebox.showerror("Error", "Please select a valid Laravel project path first.")
            return
            
        try:
            # اجرای دستور با پارامترهای اضافی برای جلوگیری از نوشتن در فایل لاگ
            process = subprocess.Popen(
                ['php', '-d', 'xdebug.mode=off', 'artisan', 'route:list', '--json', '--no-ansi'],
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            output, error = process.communicate()
            
            if error and not output:
                messagebox.showerror("Error", f"Failed to get routes: {error}")
                return
                
            try:
                # Parse JSON output
                self.routes_data = json.loads(output)
                
                # Clear current items
                for item in self.routes_tree.get_children():
                    self.routes_tree.delete(item)
                
                # Add routes to treeview
                for route in self.routes_data:
                    self.routes_tree.insert('', 'end', values=(
                        route['method'],
                        route['uri'],
                        route['name'] or '',
                        route['action']
                    ))
                    
            except json.JSONDecodeError:
                # اگر خروجی JSON نبود، سعی می‌کنیم خروجی معمولی را پردازش کنیم
                # Clear current items
                for item in self.routes_tree.get_children():
                    self.routes_tree.delete(item)
                
                # Split output into lines and parse
                lines = output.strip().split('\n')
                if len(lines) > 1:  # Skip header row
                    for line in lines[1:]:
                        # Split line and clean up values
                        parts = line.strip().split()
                        if len(parts) >= 3:
                            method = parts[0]
                            uri = parts[1]
                            # Join remaining parts as action
                            action = ' '.join(parts[2:])
                            name = ''  # Default empty name
                            
                            self.routes_tree.insert('', 'end', values=(
                                method,
                                uri,
                                name,
                                action
                            ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh routes: {str(e)}")
            print(f"Error details: {str(e)}")  # برای دیباگ

    def run_laravel_command(self):
        project_path = self.path_entry.get()
        command = self.command_var.get()
        params = self.param_entry.get()

        if os.path.isdir(project_path):
            try:
                # Split command and parameters into a list for subprocess
                full_command = ['php', 'artisan', command] + params.split() if 'composer' not in command else ['composer'] + command.split() + params.split()

                self.stop_button.config(state=tk.NORMAL)
                self.run_in_thread(project_path, full_command)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to run command: {e}")
        else:
            messagebox.showerror("Error", "Invalid project path.")

    def run_in_thread(self, project_path, cmd_list):
        def target():
            try:
                with subprocess.Popen(cmd_list, cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False) as process:
                    self.process = process
                    self.log_command(f"Started: {' '.join(cmd_list)}")
                    
                    # Reset server URL if this is not a serve command
                    if 'serve' not in cmd_list:
                        self.server_url = None
                        self.url_label.config(text="Not running")
                        self.copy_url_button.config(state='disabled')
                    
                    while True:
                        output = process.stdout.readline()
                        if output:
                            self.log_text.insert(tk.END, output)
                            self.log_text.see(tk.END)
                            
                            # Check for server URL in output
                            if 'serve' in cmd_list:
                                url_match = re.search(r'Server running on \[([^\]]+)\]', output)
                                if url_match:
                                    self.server_url = url_match.group(1)
                                    self.url_label.config(text=self.server_url)
                                    self.copy_url_button.config(state='normal')
                            
                        if process.poll() is not None:
                            break
                    
                    self.process = None
                    self.stop_button.config(state=tk.DISABLED)
                    self.log_command(f"Finished: {' '.join(cmd_list)}")
                    
                    # Reset server URL if serve command ended
                    if 'serve' in cmd_list:
                        self.server_url = None
                        self.url_label.config(text="Not running")
                        self.copy_url_button.config(state='disabled')
                        
            except Exception as e:
                self.log_command(f"Error: {e}")
                messagebox.showerror("Error", f"Failed to execute command: {e}")

        thread = threading.Thread(target=target)
        thread.start()

    def browse_project(self):
        path = filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def save_project_path(self):
        path = self.path_entry.get()
        if os.path.isdir(path):
            if path not in self.project_paths:
                self.project_paths.append(path)
                self.save_paths()
                self.update_paths_listbox()
                messagebox.showinfo("Success", "Project path saved successfully.")
            else:
                messagebox.showinfo("Info", "Project path already exists.")
        else:
            messagebox.showerror("Error", "Invalid project path.")

    def stop_command(self):
        if self.process:
            self.process.terminate()
            self.process = None
            self.stop_button.config(state=tk.DISABLED)
            self.log_command("Command stopped by user.")
            messagebox.showinfo("Stopped", "The command has been stopped.")
            
            # Reset server URL if it was running
            if self.server_url:
                self.server_url = None
                self.url_label.config(text="Not running")
                self.copy_url_button.config(state='disabled')

    def load_paths(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return []

    def save_paths(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.project_paths, f)

    def update_paths_listbox(self):
        self.paths_listbox.delete(0, tk.END)
        for path in self.project_paths:
            self.paths_listbox.insert(tk.END, path)

    def on_path_selected(self, event):
        selected_index = self.paths_listbox.curselection()
        if selected_index:
            selected_path = self.paths_listbox.get(selected_index)
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, selected_path)

    def delete_selected_path(self):
        selected_index = self.paths_listbox.curselection()
        if selected_index:
            selected_path = self.paths_listbox.get(selected_index)
            self.project_paths.remove(selected_path)
            self.save_paths()
            self.update_paths_listbox()
            messagebox.showinfo("Success", "Project path deleted successfully.")

    def log_command(self, command):
        """Log the executed command with timestamp."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {command}\n"
        
        # Write to log file
        with open(LOG_FILE, 'a', encoding='utf-8') as log_file:
            log_file.write(log_entry)
        
        # Update log display
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)

    def load_logs(self):
        """Load the log file content into the text box."""
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as log_file:
                    self.log_text.delete(1.0, tk.END)
                    self.log_text.insert(tk.END, log_file.read())
                self.log_text.see(tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load logs: {e}")

    def clear_logs(self):
        """Clear the log file and text box."""
        try:
            # Clear log file
            with open(LOG_FILE, 'w', encoding='utf-8') as log_file:
                log_file.write('')
            
            # Clear log display
            self.log_text.delete(1.0, tk.END)
            messagebox.showinfo("Success", "Logs cleared successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear logs: {e}")

def create_menu(self):
    """Create menu bar with additional options"""
    menubar = tk.Menu(self.root)
    self.root.config(menu=menubar)
    
    # File menu
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Clear Logs", command=self.clear_logs)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=self.root.quit)
    
    # View menu
    view_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="View", menu=view_menu)
    view_menu.add_command(label="Refresh Routes", command=self.refresh_routes)
    
    # Help menu
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="About", command=self.show_about)

def show_about(self):
    """Show about dialog"""
    about_text = """Laravel Command Runner
Version 1.0

A GUI tool for managing Laravel projects and running artisan commands.
Features:
- Run Laravel artisan commands
- View and search routes
- Monitor server status
- Save project paths
- Command logging
    """
    messagebox.showinfo("About Laravel Command Runner", about_text)

def export_routes(self):
    """Export routes to a text file"""
    if not hasattr(self, 'routes_data') or not self.routes_data:
        messagebox.showerror("Error", "No routes data available. Please refresh routes first.")
        return
        
    try:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"{'Method':<10} {'URI':<50} {'Name':<30} {'Action'}\n")
                f.write("-" * 100 + "\n")
                
                # Write routes
                for route in self.routes_data:
                    f.write(f"{route['method']:<10} {route['uri']:<50} {(route['name'] or ''):<30} {route['action']}\n")
                    
            messagebox.showinfo("Success", "Routes exported successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export routes: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    
    # Set window size and position
    window_width = 800
    window_height = 900
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    root.minsize(600, 700)
    
    # Apply a theme (you can choose different themes)
    style = ttk.Style()
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')
    
    app = LaravelGUI(root)
    root.mainloop()