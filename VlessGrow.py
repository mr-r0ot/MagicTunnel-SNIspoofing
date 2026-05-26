import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import requests
import json
import os
import re
import urllib.parse

# ---------- Appearance ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------- Config File -------------
CONFIG_FILE = "config.json"
DEFAULT_PORT = 40442

def get_listen_port():
    """Read LISTEN_PORT from config.json or return default"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("LISTEN_PORT", DEFAULT_PORT)
        except:
            pass
    return DEFAULT_PORT

def modify_vless_config(vless_link: str, new_address: str, new_port: int, remark_suffix: str = "MagicTunnel") -> str:
    """
    Modify a vless:// link: change address, port, and add suffix to remark.
    Example: vless://uuid@oldhost:port?params#oldremark
    """
    if not vless_link.startswith("vless://"):
        return vless_link  # not a vless link, return unchanged
    
    try:
        # Split into parts
        # Format: vless://uuid@host:port?params#remark
        # Remove prefix
        content = vless_link[8:]  # after "vless://"
        
        # Find the '@' separator
        at_index = content.find('@')
        if at_index == -1:
            return vless_link
        
        uuid_part = content[:at_index]
        rest = content[at_index+1:]  # host:port?params#remark
        
        # Extract host:port part (before '?' or '#')
        # Find '?' or '#'
        q_pos = rest.find('?')
        hash_pos = rest.find('#')
        
        # Determine the end of host:port
        end_pos = len(rest)
        if q_pos != -1 and q_pos < end_pos:
            end_pos = q_pos
        if hash_pos != -1 and hash_pos < end_pos:
            end_pos = hash_pos
        
        host_port = rest[:end_pos]
        # Split host and port
        if ':' in host_port:
            old_host, old_port = host_port.split(':', 1)
        else:
            old_host = host_port
            old_port = None
        
        # Build new host:port
        new_host_port = f"{new_address}:{new_port}"
        
        # Reconstruct the URL
        new_rest = new_host_port + rest[end_pos:]
        
        # Now handle remark (# part)
        remark = ""
        hash_index = new_rest.find('#')
        if hash_index != -1:
            remark = new_rest[hash_index+1:]
            new_rest = new_rest[:hash_index]
        
        # Add suffix to remark
        if remark:
            new_remark = f"{remark} - {remark_suffix}"
        else:
            new_remark = remark_suffix
        
        new_link = f"vless://{uuid_part}@{new_rest}#{new_remark}"
        return new_link
    except Exception as e:
        # If any error, return original
        return vless_link

class VlessGrowApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("✨ VlessGrow - MagicTunnel Config Manager ✨")
        self.app.geometry("1100x750")
        self.app.minsize(900, 600)
        
        self.links_used = False  # to prevent duplicate fetch
        self.configs_modified = False  # track if conversion done (for color change)
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Main container
        main_frame = ctk.CTkFrame(self.app, corner_radius=15, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(main_frame, text="Vless Config Manager for MagicTunnel",
                             font=("Segoe UI", 20, "bold"))
        title.pack(pady=(0, 15))
        
        # Textbox area (large) - red border initially
        self.textbox = ctk.CTkTextbox(main_frame, wrap="none", font=("Consolas", 11),
                                      corner_radius=12, border_width=2, border_color="#cc3333")
        self.textbox.pack(fill="both", expand=True, pady=10)
        
        # Button frame
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        # Fetch Configs button
        self.fetch_btn = ctk.CTkButton(btn_frame, text="🌐 دریافت کانفیگ‌های رایگان",
                                       command=self.fetch_configs,
                                       width=200, height=45, corner_radius=12,
                                       fg_color="#2c7da0", hover_color="#1f5e7a",
                                       font=("Segoe UI", 13, "bold"))
        self.fetch_btn.pack(side="left", padx=10)
        
        # Convert Configs button
        self.convert_btn = ctk.CTkButton(btn_frame, text="🔄 تبدیل کانفیگ‌ها برای MagicTunnel",
                                         command=self.convert_configs,
                                         width=250, height=45, corner_radius=12,
                                         fg_color="#f77f00", hover_color="#e66700",
                                         font=("Segoe UI", 13, "bold"))
        self.convert_btn.pack(side="left", padx=10)
        
        # Copy button
        self.copy_btn = ctk.CTkButton(btn_frame, text="📋 کپی همه کانفیگ‌ها",
                                      command=self.copy_all,
                                      width=180, height=45, corner_radius=12,
                                      fg_color="#2e7d32", hover_color="#1b5e20",
                                      font=("Segoe UI", 13, "bold"))
        self.copy_btn.pack(side="left", padx=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(main_frame, text="✅ آماده | کانفیگ‌ها را دریافت یا وارد کنید",
                                         font=("Segoe UI", 11))
        self.status_label.pack(pady=5)
        
        # Initial textbox hint
        self.textbox.insert("0.0", "// لطفاً کانفیگ‌های vless خود را در اینجا قرار دهید یا دکمه دریافت را بزنید\n")
        self.textbox.configure(state="normal")
        
    def fetch_configs(self):
        """Fetch vless configs from multiple URLs and append to textbox"""
        if self.links_used:
            messagebox.showinfo("تکرار", "شما قبلاً کانفیگ‌ها را دریافت کرده‌اید. در صورت نیاز دستی اضافه کنید.")
            return
        
        urls = [
            "https://raw.githubusercontent.com/barry-far/V2ray-config/main/Splitted-By-Protocol/vless.txt",
            "https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/vless.txt",
            "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/super-sub.txt",
            "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/Protocols/vless.txt"
        ]
        
        all_configs = []
        self.status_label.configure(text="⏳ در حال دریافت کانفیگ‌ها...")
        self.app.update()
        
        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    content = response.text
                    # Split by lines, each line might be a vless link or base64? Usually plain text with one link per line.
                    lines = content.strip().splitlines()
                    for line in lines:
                        line = line.strip()
                        if line and line.startswith("vless://"):
                            all_configs.append(line)
                else:
                    self.status_label.configure(text=f"⚠️ خطا در دریافت از {url}")
            except Exception as e:
                self.status_label.configure(text=f"⚠️ خطا: {str(e)[:50]}")
        
        if all_configs:
            # Clear existing content? Better to append at the end
            current = self.textbox.get("0.0", "end-1c")
            # Remove hint if it's the default
            if current.strip() == "// لطفاً کانفیگ‌های vless خود را در اینجا قرار دهید یا دکمه دریافت را بزنید":
                self.textbox.delete("0.0", "end")
            else:
                # Add newline if not empty
                if current and not current.endswith("\n"):
                    self.textbox.insert("end", "\n")
            
            for cfg in all_configs:
                self.textbox.insert("end", cfg + "\n")
            
            self.links_used = True
            self.status_label.configure(text=f"✅ دریافت شد {len(all_configs)} کانفیگ از منابع آنلاین")
        else:
            self.status_label.configure(text="❌ هیچ کانفیگی دریافت نشد. لطفاً بعداً تلاش کنید.")
    
    def convert_configs(self):
        """Modify all vless links: change address to 127.0.0.1, port from config.json, add suffix to remark"""
        content = self.textbox.get("0.0", "end-1c")
        if not content.strip():
            messagebox.showwarning("هشدار", "هیچ کانفیگی برای تبدیل وجود ندارد.")
            return
        
        # Get port from config.json
        port = get_listen_port()
        new_address = "127.0.0.1"
        
        lines = content.splitlines()
        new_lines = []
        modified_count = 0
        
        for line in lines:
            if line.strip().startswith("vless://"):
                new_line = modify_vless_config(line, new_address, port, "MagicTunnel")
                new_lines.append(new_line)
                modified_count += 1
            else:
                new_lines.append(line)  # keep non-vless lines as is
        
        new_content = "\n".join(new_lines)
        self.textbox.delete("0.0", "end")
        self.textbox.insert("0.0", new_content)
        
        # Change border color to green
        self.textbox.configure(border_color="#33cc33")
        self.status_label.configure(text=f"✅ تبدیل انجام شد! {modified_count} کانفیگ به 127.0.0.1:{port} و MagicTunnel اختصاص یافت.")
        self.configs_modified = True
        messagebox.showinfo("موفق", f"{modified_count} کانفیگ با موفقیت تبدیل شد.\nآدرس: 127.0.0.1\nپورت: {port}\nنام: MagicTunnel اضافه شد.")
    
    def copy_all(self):
        """Copy all configs to clipboard"""
        content = self.textbox.get("0.0", "end-1c")
        if content.strip():
            self.app.clipboard_clear()
            self.app.clipboard_append(content)
            self.status_label.configure(text="📋 کانفیگ‌ها در کلیپبورد کپی شدند.")
        else:
            messagebox.showwarning("هشدار", "هیچ متنی برای کپی وجود ندارد.")
    
    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    app = VlessGrowApp()
    app.run()