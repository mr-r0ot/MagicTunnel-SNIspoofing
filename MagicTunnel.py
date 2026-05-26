import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
import threading
import time
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
if os.name=='nt':import ctypes

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DEFAULT_DOMAINS = [
    "hcaptcha.com", "newassets.hcaptcha.com", "js.hcaptcha.com",
    "imgs.hcaptcha.com", "imgs2.hcaptcha.com", "imgs3.hcaptcha.com",
    "assets.hcaptcha.com", "api.hcaptcha.com", "analytics.hcaptcha.com",
    "stats.hcaptcha.com", "three-cust.hcaptcha.com", "tg.hcaptcha.com",
    "primary.hcaptcha.com", "dashboard.hcaptcha.com", "billing.hcaptcha.com",
    "accounts.hcaptcha.com", "proxy.hcaptcha.com", "loader.hcaptcha.com",
    "challenge-tasks.hcaptcha.com", "serverless.hcaptcha.com",
    "health-check.hcaptcha.com", "email.hcaptcha.com","cdnjs.com",
"jquery.com",
"stackoverflow.com",
"superuser.com",
"askubuntu.com",
"unpkg.com",
"archive.org",
"contextweb.com",
"chatgpt.com",
"openai.com",
"cdn.jsdelivr.net",
"fontawesome.com",
"trello.com",
"microsoft.com",
"windows.com",
"update.microsoft.com",
"windowsupdate.com",
"msftncsi.com",
"dl.delivery.mp.microsoft.com"
]





def run_as_admin(file_path, args=""):
    """اجرای فایل با دسترسی ادمین (درخواست UAC می‌دهد)"""
    try:
        # برای ویندوز
        if os.name == 'nt':
            # اگر فایل پایتون است، باید python.exe را با اسکریپت اجرا کنیم
            if file_path.endswith('.py'):
                # مسیر python.exe و اسکریپت را به عنوان آرگومان می‌دهیم
                result = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, f'"{file_path}"', None, 1  # 1 = SW_SHOWNORMAL
                )
            else:
                # برای exe مستقیم
                result = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", file_path, args, None, 1
                )
            # اگر نتیجه کمتر از 32 باشد یعنی خطا رخ داده
            if result <= 32:
                raise ctypes.WinError()
            return True
        else:
            # برای لینوکس/مک از sudo استفاده می‌شود (اما نیاز به ترمینال دارد)
            # اینجا فقط یک نمونه ساده
            if file_path.endswith('.py'):
                subprocess.Popen(['sudo', sys.executable, file_path])
            else:
                subprocess.Popen(['sudo', file_path])
            return True
    except Exception as e:
        messagebox.showerror("Elevation Error", f"خطا در اجرا با دسترسی ادمین:\n{str(e)}")
        return False

class MagicTunnelApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("✨ MagicTunnel - Clear Domain Checker ✨ By https://Github.com/mr-r0ot/MagicTunnel")
        self.app.geometry("1200x800")
        self.app.minsize(1000, 700)
        self.valid_domains = []
        self.domains = []
        self.check_active = False
        self._setup_ui()
        self._load_initial_domains()
    
    def _setup_ui(self):
        top_frame = ctk.CTkFrame(self.app, corner_radius=15, fg_color=("gray85", "gray12"))
        top_frame.pack(pady=15, padx=15, fill="x")

        btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10, padx=10)

        self.import_btn = ctk.CTkButton(btn_frame, text="📂 Import File", command=self.import_domains, width=130, height=40, corner_radius=12, font=("Segoe UI", 12, "bold"))
        self.import_btn.grid(row=0, column=0, padx=8)

        self.export_btn = ctk.CTkButton(btn_frame, text="💾 Export Results", command=self.export_results, width=140, height=40, corner_radius=12, font=("Segoe UI", 12, "bold"))
        self.export_btn.grid(row=0, column=1, padx=8)

        self.reset_btn = ctk.CTkButton(btn_frame, text="🔄 Reset to Default", command=self.reset_domains, width=150, height=40, corner_radius=12, font=("Segoe UI", 12, "bold"))
        self.reset_btn.grid(row=0, column=2, padx=8)

        self.check_btn = ctk.CTkButton(btn_frame, text="🚀 START CHECK", command=self.start_check, width=160, height=48, corner_radius=16, fg_color="#f77f00", hover_color="#e66700", font=("Segoe UI", 14, "bold"), border_width=2, border_color="#ffb347")
        self.check_btn.grid(row=0, column=3, padx=8, pady=4)

        self.save_list_btn = ctk.CTkButton(btn_frame, text="📥 Save Domain List", command=self.save_domain_list, width=150, height=40, corner_radius=12, font=("Segoe UI", 12, "bold"))
        self.save_list_btn.grid(row=0, column=4, padx=8)

        # Add domain manually
        add_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        add_frame.pack(fill="x", pady=(0,10), padx=10)
        self.domain_entry = ctk.CTkEntry(add_frame, placeholder_text="e.g., example.com", width=300, height=38, corner_radius=12, font=("Segoe UI", 11))
        self.domain_entry.pack(side="left", padx=5)
        self.add_btn = ctk.CTkButton(add_frame, text="➕ Add Domain", command=self.add_domain, width=120, height=38, corner_radius=12, font=("Segoe UI", 12))
        self.add_btn.pack(side="left", padx=8)

        # Domain list
        self.domains_container = ctk.CTkScrollableFrame(self.app, label_text="📋 Domain List", corner_radius=15, fg_color=("gray80", "gray17"), height=200)
        self.domains_container.pack(pady=8, padx=15, fill="x")

        # Results table
        results_frame = ctk.CTkFrame(self.app, corner_radius=15, fg_color=("gray85", "gray12"))
        results_frame.pack(pady=8, padx=15, fill="both", expand=True)

        ctk.CTkLabel(results_frame, text="📊 Latency Test Results (sorted by response time)", font=("Segoe UI", 13, "bold"), anchor="w").pack(pady=(8,0), padx=10, anchor="w")

        tree_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(tree_frame, columns=("Domain", "Latency (ms)", "Status"), show="headings", height=12, selectmode="extended")
        self.tree.heading("Domain", text="🌐 Domain")
        self.tree.heading("Latency (ms)", text="⏱️ Latency (ms)")
        self.tree.heading("Status", text="📡 Status")
        self.tree.column("Domain", width=400, anchor="w")
        self.tree.column("Latency (ms)", width=120, anchor="center")
        self.tree.column("Status", width=200, anchor="w")

        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")

        self.progress = ctk.CTkProgressBar(self.app, width=500, height=12, corner_radius=8)
        self.progress.pack(pady=(5,2))
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(self.app, text="✅ Ready | Domains: 0", font=("Segoe UI", 11), text_color=("gray20", "gray70"))
        self.status_label.pack(pady=2)

        # Styling
        style = ttk.Style()
        style.theme_use("clam")
        bg = "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#f0f0f0"
        fg = "white" if ctk.get_appearance_mode() == "Dark" else "black"
        style.configure("Treeview", background=bg, foreground=fg, rowheight=32, fieldbackground=bg, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#3a3a3a" if ctk.get_appearance_mode() == "Dark" else "#d9d9d9", foreground="white" if ctk.get_appearance_mode() == "Dark" else "black", font=("Segoe UI", 11, "bold"))
        style.map("Treeview", background=[("selected", "#2c7da0")])
        self.tree.tag_configure("fast", background="#1e5631", foreground="#ccffcc")
        self.tree.tag_configure("slow", background="#8a5a2a", foreground="#ffffcc")
        self.tree.tag_configure("failed", background="#6b2e2e", foreground="#ffcccc")

    def _load_initial_domains(self):
        if os.path.exists("domains.txt"):
            with open("domains.txt", "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            self.domains = lines if lines else DEFAULT_DOMAINS.copy()
        else:
            self.domains = DEFAULT_DOMAINS.copy()
            self._save_domains_file()
        self._refresh_domains_display()
        self.status_label.configure(text=f"✅ Ready | Domains: {len(self.domains)}")
    
    def _save_domains_file(self, filename="domains.txt"):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(self.domains))
    
    def _refresh_domains_display(self):
        for w in self.domains_container.winfo_children():
            w.destroy()
        for domain in self.domains:
            row = ctk.CTkFrame(self.domains_container, fg_color="transparent")
            row.pack(fill="x", pady=3, padx=5)
            ctk.CTkLabel(row, text=domain, font=("Segoe UI", 11), anchor="w").pack(side="left", fill="x", expand=True, padx=10)
            del_btn = ctk.CTkButton(row, text="🗑️", width=40, height=30, corner_radius=8, fg_color="#a33", hover_color="#822", command=lambda d=domain: self._remove_domain(d))
            del_btn.pack(side="right", padx=5)
    
    def _remove_domain(self, domain):
        if domain in self.domains:
            self.domains.remove(domain)
            self._refresh_domains_display()
            self._save_domains_file()
            self.status_label.configure(text=f"✅ Removed | Domains: {len(self.domains)}")
    
    def add_domain(self):
        new = self.domain_entry.get().strip()
        if not new:
            messagebox.showwarning("Warning", "Enter a valid domain")
            return
        if new in self.domains:
            messagebox.showinfo("Duplicate", "Domain already in list")
            return
        self.domains.append(new)
        self._refresh_domains_display()
        self._save_domains_file()
        self.domain_entry.delete(0, "end")
        self.status_label.configure(text=f"➕ Added | Total: {len(self.domains)}")
    
    def import_domains(self):
        fp = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not fp:
            return
        try:
            with open(fp, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
            if not lines:
                messagebox.showwarning("Error", "No domains found")
                return
            self.domains = lines
            self._refresh_domains_display()
            self._save_domains_file()
            self.status_label.configure(text=f"📂 Imported | Domains: {len(self.domains)}")
            messagebox.showinfo("Success", f"{len(lines)} domains imported")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def reset_domains(self):
        self.domains = DEFAULT_DOMAINS.copy()
        self._refresh_domains_display()
        self._save_domains_file()
        self.status_label.configure(text=f"🔄 Reset to default | Domains: {len(self.domains)}")
    
    def save_domain_list(self):
        fp = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if fp:
            self._save_domains_file(fp)
            messagebox.showinfo("Success", f"Saved to {fp}")
    
    def export_results(self):
        if not self.tree.get_children():
            messagebox.showwarning("Warning", "No results to export")
            return
        fp = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if fp:
            with open(fp, "w", encoding="utf-8") as f:
                f.write("Domain,Latency (ms),Status\n")
                for row in self.tree.get_children():
                    d, lat, stat = self.tree.item(row, "values")
                    f.write(f"{d},{lat},{stat}\n")
            messagebox.showinfo("Success", f"Saved to {fp}")
    
    def _check_single_domain(self, domain):
        start = time.perf_counter()
        try:
            r = requests.get(f"https://{domain}", timeout=5, stream=False)
            elapsed = (time.perf_counter() - start) * 1000
            r.close()
            return (domain, elapsed, "Connected")
        except:
            return (domain, float('inf'), "Failed")
    
    def start_check(self):
        if self.check_active:
            messagebox.showinfo("Info", "Check already running")
            return
        if not self.domains:
            messagebox.showwarning("Warning", "No domains to check")
            return
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.valid_domains = []
        self.completed = 0
        self.total_domains = len(self.domains)
        self.progress.set(0)
        self.status_label.configure(text=f"🚀 Checking... 0/{self.total_domains}")
        self.check_active = True
        self._set_buttons_state("disabled")
        threading.Thread(target=self._worker_check, daemon=True).start()
        self.app.after(100, self._poll_progress)
    
    def _worker_check(self):
        results = []
        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = {ex.submit(self._check_single_domain, d): d for d in self.domains}
            for fut in as_completed(futures):
                d, lat, stat = fut.result()
                results.append((d, lat, stat))
                self.completed += 1
                self.app.after(0, self._update_progress, self.completed)
        results.sort(key=lambda x: (x[1] == float('inf'), x[1]))
        self.app.after(0, self._display_results, results)
        self.valid_domains = [(d, lat) for d, lat, st in results if st == "Connected"]
        self.app.after(0, self._finish_check)
    
    def _update_progress(self, completed):
        self.progress.set(completed / self.total_domains)
        self.status_label.configure(text=f"📡 Checking... {completed}/{self.total_domains}")
    
    def _display_results(self, results):
        for dom, lat, stat in results:
            if stat == "Connected":
                tag = "fast" if lat < 200 else "slow"
                lat_str = f"{lat:.1f}"
            else:
                tag = "failed"
                lat_str = "N/A"
            self.tree.insert("", "end", values=(dom, lat_str, stat), tags=(tag,))
    
    def _finish_check(self):
        self.check_active = False
        self._set_buttons_state("normal")
        self.progress.set(1)
        self.status_label.configure(text=f"✅ Check finished | Connected: {len(self.valid_domains)}/{self.total_domains}")
        
        # ذخیره دامنه‌های متصل در فایل CheckedOk.txt
        if self.valid_domains:
            with open("CheckedOk.txt", "w+", encoding="utf-8") as f:
                for dom, lat in self.valid_domains:
                    f.write(f"{dom}  {lat:.1f}ms\n")
            self.status_label.configure(text=f"✅ Saved {len(self.valid_domains)} connected domains to CheckedOk.txt")
        else:
            self.status_label.configure(text="⚠️ No connected domains found, CheckedOk.txt not created")
        
        # اجرای خودکار step2
        self.app.after(1000, self.launch_step2)  # یک ثانیه صبر کن بعد اجرا کن
    
    def _set_buttons_state(self, state):
        for btn in [self.import_btn, self.export_btn, self.reset_btn, self.add_btn, self.save_list_btn, self.check_btn]:
            btn.configure(state=state)
    
    def _poll_progress(self):
        if self.check_active:
            self.app.after(200, self._poll_progress)
    
    def launch_step2(self):
        exe_path = "step2.exe"
        py_path = "step2.py"
        if os.path.exists(exe_path):
            try:
                subprocess.Popen([exe_path], cwd=os.getcwd(), creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
                self.status_label.configure(text="🚀 Launched step2.exe")
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch step2.exe:\n{str(e)}")
        elif os.path.exists(py_path):
            try:
                subprocess.Popen([sys.executable, py_path], cwd=os.getcwd(), creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
                self.status_label.configure(text="🚀 Launched step2.py")
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch step2.py:\n{str(e)}")
        else:
            messagebox.showerror("File Not Found", "Neither step2.exe nor step2.py found in current directory.")
        

        if os.path.exists(exe_path):
            try:
                if run_as_admin(exe_path):
                    self.status_label.configure(text="🚀 اجرا شد step2.exe (با دسترسی ادمین)")
                else:
                    self.status_label.configure(text="❌ اجرا نشد - مجوز ادمین دریافت نشد")
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch step2.exe:\n{str(e)}")
        elif os.path.exists(py_path):
            try:
                if run_as_admin(py_path):
                    self.status_label.configure(text="🚀 اجرا شد step2.py (با دسترسی ادمین)")
                else:
                    self.status_label.configure(text="❌ اجرا نشد - مجوز ادمین دریافت نشد")
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch step2.py:\n{str(e)}")
        else:
            messagebox.showerror("File Not Found", "Neither step2.exe nor step2.py found in current directory.")
    
    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    app = MagicTunnelApp()
    app.run()