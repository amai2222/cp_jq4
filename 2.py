import tkinter as tk
from tkinter import ttk, font, messagebox, scrolledtext
import requests
import threading
import json
import time

class MegaFetcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MegaFetcher V2 - 全功能获取器 (API修正版)")
        self.root.geometry("1300x800")

        # --- 数据存储与API配置 (已修正!) ---
        self.api_config = {
            "竞彩足球": {
                "issue_api": "https://apic.51honghuodian.com/api/match/selectlist",
                "params": {'platform': 'hhjdc_other', '_prt': 'https', 'ver': '20180101000000', 'hide_more': '1'}
            },
            "胜负彩14场": {
                "issue_api": "https://apic.51honghuodian.com/api/toto/matchlist",
                "data_api": "https://apic.51honghuodian.com/api/toto/matchlist",
                "params": {'platform': 'hhjdc_other', 'lottery_type': 'ToTo-14'}
            },
            "任选九场": {
                "issue_api": "https://apic.51honghuodian.com/api/toto/matchlist",
                "data_api": "https://apic.51honghuodian.com/api/toto/matchlist",
                "params": {'platform': 'hhjdc_other', 'lottery_type': 'ToTo-R9'}
            }
        }
        self.cached_jczq_data = None # 缓存竞彩数据，避免重复请求
        
        # --- 字体和样式 ---
        self.default_font = font.Font(family="Microsoft YaHei UI", size=11)
        self.bold_font = font.Font(family="Microsoft YaHei UI", size=12, weight="bold")
        self.mono_font = font.Font(family="Consolas", size=11)
        
        style = ttk.Style()
        style.configure("Treeview", rowheight=28, font=self.default_font)
        style.configure("Treeview.Heading", font=self.bold_font)
        style.map('Treeview', background=[('selected', '#0078D7')])
        style.configure("Bold.TLabel", font=self.bold_font)

        # --- 创建主界面 ---
        self.paned_window = tk.PanedWindow(root, orient=tk.VERTICAL, sashrelief=tk.RAISED)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        self.main_frame = ttk.Frame(self.paned_window, padding="10")
        self.debug_frame = ttk.Frame(self.paned_window, padding="10")
        self.paned_window.add(self.main_frame, height=550)
        self.paned_window.add(self.debug_frame)

        self._create_main_widgets()
        self._create_debug_widgets()
        
        # 初始化时自动加载第一个玩法的期号
        self.root.after(100, lambda: self.on_game_type_select(None))

    def _create_main_widgets(self):
        parent = self.main_frame
        # 1. 控制区
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', side='top', pady=(0, 10))

        ttk.Label(control_frame, text="玩法:", font=self.bold_font).pack(side='left', padx=(0, 5))
        self.game_type_combo = ttk.Combobox(control_frame, state="readonly", font=self.default_font, width=15)
        self.game_type_combo['values'] = list(self.api_config.keys())
        self.game_type_combo.current(0)
        self.game_type_combo.pack(side='left', padx=5)
        self.game_type_combo.bind("<<ComboboxSelected>>", self.on_game_type_select)

        ttk.Label(control_frame, text="期号/日期:", font=self.bold_font).pack(side='left', padx=(10, 5))
        self.issue_combo = ttk.Combobox(control_frame, state="disabled", font=self.default_font, width=20)
        self.issue_combo.pack(side='left', padx=5)

        self.fetch_button = ttk.Button(control_frame, text="  获 取  ", command=self.start_fetch_data)
        self.fetch_button.pack(side='left', padx=20)
        
        self.status_label = ttk.Label(control_frame, text="请选择玩法和期号", font=self.default_font, foreground="blue")
        self.status_label.pack(side='left', padx=10)

        # 2. 数据表格区
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True)

        self.columns = ('seq', 'league', 'teams', 'time', 'odds1', 'odds2', 'odds3')
        self.tree = ttk.Treeview(tree_frame, columns=self.columns, show='headings')
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def _setup_columns(self, game_type):
        """动态设置表格列标题和宽度"""
        for col in self.columns:
            self.tree.heading(col, text='') # Clear old headings
        
        if game_type == "竞彩足球":
            headings = {
                'seq': '序号', 'league': '联赛', 'teams': '主队 vs 客队', 'time': '时间',
                'odds1': '胜平负 赔率', 'odds2': '让球(-1) 赔率', 'odds3': ''
            }
            widths = {'seq': 60, 'league': 120, 'teams': 250, 'time': 160, 'odds1': 200, 'odds2': 200, 'odds3': 0}
        else: # 胜负彩或任九
            headings = {
                'seq': '序号', 'league': '联赛', 'teams': '主队 vs 客队', 'time': '时间',
                'odds1': '胜赔(3)', 'odds2': '平赔(1)', 'odds3': '负赔(0)'
            }
            widths = {'seq': 60, 'league': 120, 'teams': 250, 'time': 160, 'odds1': 100, 'odds2': 100, 'odds3': 100}

        for col, text in headings.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=widths[col], anchor='center' if col != 'teams' else 'w')

    def on_game_type_select(self, event):
        game_type = self.game_type_combo.get()
        self.issue_combo.set('')
        self.issue_combo.config(state="disabled")
        self.fetch_button.config(state="disabled")
        self.tree.delete(*self.tree.get_children())
        self._setup_columns(game_type)
        
        # 如果是竞彩且已有缓存，直接使用缓存，不重新请求
        if game_type == "竞彩足球" and self.cached_jczq_data:
            self.status_label.config(text="竞彩数据已缓存，请选择日期", foreground="blue")
            issues = sorted(list(self.cached_jczq_data.keys()), reverse=True)
            self.update_issue_dropdown(game_type, issues)
            return

        self.status_label.config(text=f"正在获取<{game_type}>的期号列表...", foreground="orange")
        threading.Thread(target=self._fetch_issue_list_worker, args=(game_type,), daemon=True).start()

    def _fetch_issue_list_worker(self, game_type):
        config = self.api_config[game_type]
        try:
            self.log_to_debug_window(f"请求期号列表: {config['issue_api']} with params: {config['params']}")
            res = requests.get(config['issue_api'], params=config['params'], timeout=15)
            res.raise_for_status()
            data = res.json()
            if data.get('errcode') != 0: raise Exception(data.get('msg', 'API返回错误'))

            issues = []
            if game_type == "竞彩足球":
                self.cached_jczq_data = data['data']
                issues = sorted(list(self.cached_jczq_data.keys()), reverse=True)
            else:
                issues = [item['lottery_no'] for item in data['data']['lottery_list']]
            
            self.root.after(0, self.update_issue_dropdown, game_type, issues)
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"获取期号失败: {e}", foreground="red"))

    def update_issue_dropdown(self, game_type, issues):
        if not issues:
            self.status_label.config(text=f"未找到<{game_type}>的可用期号/日期", foreground="red")
            return
        
        self.issue_combo['values'] = issues
        self.issue_combo.current(0)
        self.issue_combo.config(state="readonly")
        self.fetch_button.config(state="normal")
        self.status_label.config(text="准备就绪，请点击获取", foreground="green")

    def start_fetch_data(self):
        game_type = self.game_type_combo.get()
        issue = self.issue_combo.get()
        if not game_type or not issue: return

        self.fetch_button.config(state="disabled")
        self.tree.delete(*self.tree.get_children())
        self.status_label.config(text=f"正在获取<{issue}>的数据...", foreground="blue")
        
        if game_type == "竞彩足球":
            self.update_ui_jczq(issue)
        else:
            threading.Thread(target=self._fetch_match_data_worker, args=(game_type, issue), daemon=True).start()

    def _fetch_match_data_worker(self, game_type, issue):
        config = self.api_config[game_type]
        params = config['params'].copy()
        params['lottery_no'] = issue
        
        try:
            self.log_to_debug_window(f"请求对阵数据: {config['data_api']} with params: {params}")
            res = requests.get(config['data_api'], params=params, timeout=15)
            res.raise_for_status()
            data = res.json()
            if data.get('errcode') != 0: raise Exception(data.get('msg', 'API返回数据错误'))
            
            self.root.after(0, self.update_ui_sfc, data['data']['match']['list'])

        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"获取对阵数据失败: {e}", foreground="red"))
        finally:
            self.root.after(0, lambda: self.fetch_button.config(state="normal"))

    def update_ui_jczq(self, date_key):
        matches_on_date = self.cached_jczq_data.get(date_key, {})
        match_list = sorted(matches_on_date.values(), key=lambda x: x.get('sort', 0))

        for match in match_list:
            odds_list = match.get('list', {})
            had = odds_list.get('SportteryNWDL', {}).get('odds', {})
            hhad = odds_list.get('SportteryWDL', {}).get('odds', {})
            
            had_str = f"{had.get('3', '-')} / {had.get('1', '-')} / {had.get('0', '-')}"
            hhad_str = f"{hhad.get('3', '-')} / {hhad.get('1', '-')} / {hhad.get('0', '-')}"
            
            self.tree.insert('', 'end', values=(
                match.get('serial_no', ''), match.get('league_name', ''),
                f"{match.get('host_name_s', '')} vs {match.get('guest_name_s', '')}",
                match.get('match_time', ''), had_str, hhad_str, ''
            ))
        self.status_label.config(text="数据显示完毕！", foreground="green")
        self.fetch_button.config(state="normal")

    def update_ui_sfc(self, match_list):
        for match in sorted(match_list, key=lambda x: int(x.get('seq', 0))):
            odds = match.get('odds', {})
            self.tree.insert('', 'end', values=(
                match.get('seq', ''), match.get('league_name', ''),
                f"{match.get('host_name', '')} vs {match.get('guest_name', '')}",
                match.get('match_time', ''),
                odds.get('3', '-'), odds.get('1', '-'), odds.get('0', '-')
            ))
        self.status_label.config(text="数据显示完毕！", foreground="green")

    # --- 调试窗口相关代码 ---
    def _create_debug_widgets(self):
        ttk.Label(self.debug_frame, text="调试信息窗口", style="Bold.TLabel").pack(anchor='w')
        self.debug_text = scrolledtext.ScrolledText(self.debug_frame, height=10, font=self.mono_font, wrap=tk.WORD, relief='solid', borderwidth=1)
        self.debug_text.pack(fill='both', expand=True, pady=5)
        self.debug_text.config(state='disabled')
        
    def log_to_debug_window(self, message):
        try:
            self.debug_text.config(state='normal')
            timestamp = time.strftime("%H:%M:%S", time.localtime())
            self.debug_text.insert(tk.END, f"[{timestamp}] {message}\n\n")
            self.debug_text.see(tk.END)
            self.debug_text.config(state='disabled')
        except tk.TclError:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = MegaFetcherApp(root)
    root.mainloop()

