import tkinter as tk
from tkinter import ttk, font, messagebox, scrolledtext
import requests
import threading
import json
import time

class ZucaiOddsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("足彩数据获取器 V5 (精简参数版)")
        self.root.geometry("900x800")

        # --- 设置字体 ---
        self.default_font = font.Font(family="Microsoft YaHei UI", size=12)
        self.bold_font = font.Font(family="Microsoft YaHei UI", size=12, weight="bold")
        self.mono_font = font.Font(family="Consolas", size=11)

        # --- 创建可拖动分隔的窗口 ---
        self.paned_window = tk.PanedWindow(root, orient=tk.VERTICAL, sashrelief=tk.RAISED, bg='#f0f0f0')
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # --- 创建主内容和调试内容的框架 ---
        self.main_frame = ttk.Frame(self.paned_window, padding="10")
        self.debug_frame = ttk.Frame(self.paned_window, padding="10")

        self.paned_window.add(self.main_frame, height=550)
        self.paned_window.add(self.debug_frame)

        self._create_main_widgets()
        self._create_debug_widgets()
        
        self.log_to_debug_window("调试窗口已就绪。")

    def _create_main_widgets(self):
        # 1. 输入和控制区
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill='x', side='top', pady=(0, 10))

        ttk.Label(input_frame, text="输入期号:", font=self.default_font).pack(side='left', padx=5)
        
        self.lottery_no_var = tk.StringVar(value="25134")
        self.lottery_no_entry = ttk.Entry(input_frame, textvariable=self.lottery_no_var, font=self.default_font, width=10)
        self.lottery_no_entry.pack(side='left', padx=5)
        self.lottery_no_entry.bind("<Return>", lambda event: self.start_fetch_data())

        self.fetch_button = ttk.Button(input_frame, text="获取数据", command=self.start_fetch_data)
        self.fetch_button.pack(side='left', padx=10)
        
        self.status_label = ttk.Label(input_frame, text="准备就绪", font=self.default_font, foreground="blue")
        self.status_label.pack(side='left', padx=10)

        # 2. 信息展示区
        info_frame = ttk.Frame(self.main_frame)
        info_frame.pack(fill='x', side='top', pady=(0, 10))
        
        self.info_label = ttk.Label(info_frame, text="", font=self.bold_font, foreground="darkred")
        self.info_label.pack(anchor='w')

        # 3. 数据表格区
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(fill='both', expand=True)

        columns = ('match_no', 'league', 'home', 'away', 'sp_win', 'sp_draw', 'sp_loss')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

        self.tree.heading('match_no', text='场次'); self.tree.column('match_no', width=50, anchor='center')
        self.tree.heading('league', text='联赛'); self.tree.column('league', width=120, anchor='center')
        self.tree.heading('home', text='主队'); self.tree.column('home', width=120, anchor='w')
        self.tree.heading('away', text='客队'); self.tree.column('away', width=120, anchor='w')
        self.tree.heading('sp_win', text='胜'); self.tree.column('sp_win', width=80, anchor='center')
        self.tree.heading('sp_draw', text='平'); self.tree.column('sp_draw', width=80, anchor='center')
        self.tree.heading('sp_loss', text='负'); self.tree.column('sp_loss', width=80, anchor='center')
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def _create_debug_widgets(self):
        ttk.Label(self.debug_frame, text="调试信息窗口", font=self.bold_font).pack(anchor='w')
        self.debug_text = scrolledtext.ScrolledText(self.debug_frame, height=10, font=self.mono_font, wrap=tk.WORD, relief='solid', borderwidth=1)
        self.debug_text.pack(fill='both', expand=True, pady=5)
        self.debug_text.config(state='disabled')

    def log_to_debug_window(self, message):
        self.debug_text.config(state='normal')
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.debug_text.insert(tk.END, f"[{timestamp}] {message}\n\n")
        self.debug_text.see(tk.END)
        self.debug_text.config(state='disabled')

    def start_fetch_data(self):
        lottery_no = self.lottery_no_var.get().strip()
        if not lottery_no.isdigit():
            messagebox.showerror("输入错误", "请输入纯数字的期号。"); return
            
        self.fetch_button.config(state="disabled"); self.tree.delete(*self.tree.get_children())
        self.status_label.config(text=f"正在获取第 {lottery_no} 期...", foreground="blue"); self.info_label.config(text="")
        
        self.debug_text.config(state='normal'); self.debug_text.delete('1.0', tk.END); self.debug_text.config(state='disabled')
        self.log_to_debug_window(f"开始请求期号: {lottery_no}")
        threading.Thread(target=self._fetch_data_worker, args=(lottery_no,), daemon=True).start()

    def _fetch_data_worker(self, lottery_no):
        base_url = "https://apic.51honghuodian.com/api/zucai/selectlist"
        
        # --- 根据您的发现，注释掉非必需参数 ---
        params = {
            # 'platform': 'hhjdc_other',
            # '_prt': 'https',
            # 'ver': '20180101000000',
            'lottery_type': 'ToTo',       # 核心参数
            'lottery_no': lottery_no,     # 核心参数
            # 'station_user_id': '1162017'
        }
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            
            self.root.after(0, self.log_to_debug_window, f"请求的URL (精简版):\n{response.url}")
            self.root.after(0, self.log_to_debug_window, f"服务器响应状态码: {response.status_code}")
            response.raise_for_status()
            self.root.after(0, self.log_to_debug_window, f"服务器返回的原始数据:\n{response.text}")
            
            data = response.json()
            
            if data.get("errcode") == 0 and "data" in data and "match_list" in data["data"]:
                self.root.after(0, self.update_ui, True, data['data'])
            else:
                error_msg = data.get("msg", "API返回未知错误")
                self.root.after(0, self.update_ui, False, error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"网络错误: {e}"; self.root.after(0, self.log_to_debug_window, error_msg)
            self.root.after(0, self.update_ui, False, error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析错误: 服务器返回的不是有效的JSON格式。({e})"; self.root.after(0, self.log_to_debug_window, error_msg)
            self.root.after(0, self.update_ui, False, error_msg)
        except Exception as e:
            error_msg = f"处理数据时发生未知错误: {e}"; self.root.after(0, self.log_to_debug_window, error_msg)
            self.root.after(0, self.update_ui, False, error_msg)

    def update_ui(self, success, data_or_error):
        self.fetch_button.config(state="normal")
        
        if success:
            self.status_label.config(text="数据获取成功！", foreground="green")
            
            match_list_dict = data_or_error.get('match_list', {})
            
            if match_list_dict:
                first_match = next(iter(match_list_dict.values()))
                lottery_no = first_match.get('lottery_no', 'N/A')
                info_text = f"足球胜负彩 | 期号: {lottery_no}"
                self.info_label.config(text=info_text)

            for match_no_key, match_data in sorted(match_list_dict.items(), key=lambda item: int(item[0])):
                odds = match_data.get('odds', {})
                sp_win = odds.get('3', 'N/A')
                sp_draw = odds.get('1', 'N/A')
                sp_loss = odds.get('0', 'N/A')
                
                self.tree.insert('', 'end', values=(
                    match_data.get('serial_no', 'N/A'),
                    match_data.get('league_name', 'N/A'),
                    match_data.get('host_name_s', 'N/A'),
                    match_data.get('guest_name_s', 'N/A'),
                    sp_win,
                    sp_draw,
                    sp_loss
                ))
        else:
            self.status_label.config(text="获取失败", foreground="red")
            messagebox.showerror("错误", str(data_or_error))

if __name__ == "__main__":
    root = tk.Tk()
    app = ZucaiOddsApp(root)
    root.mainloop()
