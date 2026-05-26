import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import subprocess
import webbrowser
import sys

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DEFAULT_CONFIG = {
    "LISTEN_HOST": "0.0.0.0",
    "LISTEN_PORT": 40442,
    "CONNECT_IP": "104.19.229.21",
    "CONNECT_PORT": 443,
    "FAKE_SNI": "",
    "QUEUE_NUM": 1000,
    "HANDSHAKE_TIMEOUT_MS": 2000
}

class SNISpoofingWindow:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("🔒 SNI Spoofing Tunnel - MagicTunnel")
        self.window.geometry("1100x750")
        self.window.minsize(900, 600)
        self.domains_from_check = []  # list of (domain, latency)
        self._load_checked_ok()
        self._setup_ui()
    
    def _load_checked_ok(self):
        """خواندن دامنه‌های متصل از فایل CheckedOk.txt که توسط برنامه اصلی ساخته شده"""
        if os.path.exists("CheckedOk.txt"):
            try:
                with open("CheckedOk.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            parts = line.split()
                            if len(parts) >= 2:
                                domain = parts[0]
                                latency_str = parts[1].replace("ms", "")
                                try:
                                    latency = float(latency_str)
                                    self.domains_from_check.append((domain, latency))
                                except:
                                    self.domains_from_check.append((domain, 0))
            except:
                pass
        # مرتب‌سازی بر اساس کمترین پینگ
        self.domains_from_check.sort(key=lambda x: x[1])
    
    def _setup_ui(self):
        main_frame = ctk.CTkFrame(self.window, corner_radius=15, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left panel: configuration
        left = ctk.CTkFrame(main_frame, corner_radius=15, fg_color=("gray85", "gray12"))
        left.pack(side="left", fill="both", expand=True, padx=(0,10))
        
        ctk.CTkLabel(left, text="⚙️ Tunnel Configuration", font=("Segoe UI", 18, "bold")).pack(pady=(20,15))
        
        # FAKE_SNI selection
        sni_frame = ctk.CTkFrame(left, fg_color="transparent")
        sni_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(sni_frame, text="🎭 FAKE_SNI (select from checked domains):", font=("Segoe UI", 12)).pack(anchor="w")
        
        if self.domains_from_check:
            domain_list = [f"{dom} ({lat:.1f} ms)" for dom, lat in self.domains_from_check]
            self.fake_sni_combo = ctk.CTkComboBox(sni_frame, values=domain_list, width=400, state="readonly")
            self.fake_sni_combo.pack(fill="x", pady=5)
            self.fake_sni_combo.set(domain_list[0])
        else:
            self.fake_sni_entry = ctk.CTkEntry(sni_frame, width=400, placeholder_text="No domains found in CheckedOk.txt, enter manually")
            self.fake_sni_entry.pack(fill="x", pady=5)
            self.fake_sni_entry.insert(0, "www.example.com")
        
        # Other fields
        fields = [
            ("LISTEN_HOST", "0.0.0.0"),
            ("LISTEN_PORT", "40442"),
            ("CONNECT_IP", "104.19.229.21"),
            ("CONNECT_PORT", "443"),
            ("QUEUE_NUM", "1000"),
            ("HANDSHAKE_TIMEOUT_MS", "2000")
        ]
        self.entries = {}
        for label, default in fields:
            row = ctk.CTkFrame(left, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=8)
            ctk.CTkLabel(row, text=f"{label}:", width=180, anchor="w", font=("Segoe UI", 12)).pack(side="left")
            entry = ctk.CTkEntry(row, width=200, placeholder_text=default)
            entry.insert(0, default)
            entry.pack(side="right", expand=True, fill="x", padx=(10,0))
            self.entries[label] = entry
        
        # Right panel: Info, Help button and Start
        right = ctk.CTkFrame(main_frame, corner_radius=15, fg_color=("gray85", "gray12"))
        right.pack(side="right", fill="both", expand=True, padx=(10,0))
        
        ctk.CTkLabel(right, text="📖 How to Use", font=("Segoe UI", 18, "bold")).pack(pady=(20,15))
        
        info = ctk.CTkTextbox(right, wrap="word", font=("Segoe UI", 11), corner_radius=10, height=300)
        info.pack(fill="both", expand=True, padx=15, pady=10)
        
        help_text = """
🔰 این ابزار برای شرایط قطعی اینترنت و مسدودیت کلودفلر طراحی شده.
مراحل استفاده:
1. در برنامه اصلی (MagicTunnel) دامنه‌ها را اسکن کنید تا فایل CheckedOk.txt ساخته شود.
2. در این پنجره، از لیست کشویی دامنه با کمترین پینگ را انتخاب کنید (یا دستی وارد کنید).
3. تنظیمات تونل (پورت، آیپی و ...) را بررسی کنید.
4. دکمه Start را بزنید تا config.json ساخته شود و SNI.exe اجرا گردد.
5. در v2rayNG/NekoBox کانفیگ Worker را ادیت کرده و آدرس را 127.0.0.1 و پورت را همان LISTEN_PORT قرار دهید.

📌 نکته: فایل SNI.exe باید کنار این برنامه باشد.

توسط https://Github.com/mr-r0ot/MagicTunnel
        """
        info.insert("0.0", help_text)
        info.configure(state="disabled")
        
        # دکمه Help me
        help_btn = ctk.CTkButton(right, text="❓ Help me", command=self.open_help,
                                 width=150, height=40, corner_radius=12,
                                 fg_color="#2c7da0", hover_color="#1f5e7a",
                                 font=("Segoe UI", 12, "bold"))
        help_btn.pack(pady=10)
        
        self.start_btn = ctk.CTkButton(right, text="🚀 START SNI SPOOFING 🚀",
                                       command=self.start_tunnel,
                                       width=300, height=55, corner_radius=16,
                                       fg_color="#2e7d32", hover_color="#1b5e20",
                                       font=("Segoe UI", 15, "bold"))
        self.start_btn.pack(pady=10)
        
        self.status = ctk.CTkLabel(right, text="⏳ Ready", font=("Segoe UI", 11))
        self.status.pack(pady=5)
    
    def open_help(self):
        """باز کردن فایل helpme.html در مرورگر پیش‌فرض"""
        help_file = "helpme.html"
        if os.path.exists(help_file):
            webbrowser.open(help_file)
            self.status.configure(text="📖 Opened helpme.html in browser")
        else:
            messagebox.showerror("File Not Found", f"helpme.html not found in current directory.\nPlease create this file.")
            self.status.configure(text="❌ helpme.html not found")
    
    def get_fake_sni(self):
        if hasattr(self, 'fake_sni_combo'):
            selected = self.fake_sni_combo.get()
            # استخراج دامنه از رشته "domain (xx.x ms)"
            if " (" in selected:
                return selected.split(" (")[0]
            return selected
        else:
            return self.fake_sni_entry.get().strip()
    
    def start_tunnel(self):
        fake_sni = self.get_fake_sni()
        if not fake_sni:
            messagebox.showerror("Error", "Please select or enter a FAKE_SNI domain")
            return
        
        try:
            config = {
                "FAKE_SNI": fake_sni,
                "LISTEN_HOST": self.entries["LISTEN_HOST"].get().strip(),
                "LISTEN_PORT": int(self.entries["LISTEN_PORT"].get().strip()),
                "CONNECT_IP": self.entries["CONNECT_IP"].get().strip(),
                "CONNECT_PORT": int(self.entries["CONNECT_PORT"].get().strip()),
                "QUEUE_NUM": int(self.entries["QUEUE_NUM"].get().strip()),
                "HANDSHAKE_TIMEOUT_MS": int(self.entries["HANDSHAKE_TIMEOUT_MS"].get().strip())
            }
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            self.status.configure(text="✅ config.json saved")
        except Exception as e:
            messagebox.showerror("Error", f"Config save failed:\n{str(e)}")
            return
        
        if not os.path.exists("SNI.exe") and not os.path.exists("SNI.py"):
            messagebox.showerror("File Not Found", "SNI.exe not found in current directory.")
            return
        
        try:
            if os.path.exists("SNI.exe"):
                if os.name == 'nt':
                    subprocess.Popen(["SNI.exe"], cwd=os.getcwd(), creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    subprocess.Popen(["./SNI.exe"], cwd=os.getcwd())
            else:
                subprocess.Popen([sys.executable, "SNI.py"], cwd=os.getcwd(), creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)

            self.status.configure(text="🚀 SNI.exe launched! Configure v2rayNG now.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch SNI.exe:\n{str(e)}")
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = SNISpoofingWindow()
    app.run()