import tkinter as tk
from tkinter import ttk, font, messagebox, scrolledtext
import requests
import threading
import time
import json

# --- 通用的请求头 ---
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://s.51honghuodian.com/',
    'Origin': 'https://s.51honghuodian.com'
}

# --- 分析窗口类 (已集成500.com) ---
class AnalysisWindow(tk.Toplevel):
    def __init__(self, parent, match_data):
        super().__init__(parent)
        self.match_data = match_data
        host = match_data.get('host_name_s') or match_data.get('host_name', '主队')
        guest = match_data.get('guest_name_s') or match_data.get('guest_name', '客队')
        team_name = f"{host} vs {guest}"
        self.title(f"深度分析: {team_name}")
        self.geometry("1100x800"); self.grab_set() # 窗口调高一点以容纳新控件
        
        # --- 字体和样式 ---
        self.bold_font = font.Font(family="Microsoft YaHei UI", size=12, weight="bold")
        self.default_font = font.Font(family="Microsoft YaHei UI", size=10)
        style = ttk.Style(self)
        style.configure("Analysis.Treeview", rowheight=26, font=self.default_font)
        style.configure("Analysis.Treeview.Heading", font=self.bold_font)
        
        main_frame = ttk.Frame(self, padding="10"); main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 【新增】500.com 控制面板 ---
        w500_frame = ttk.LabelFrame(main_frame, text=" 500.com 数据源 ", labelwidget=tk.Label(main_frame, text=" 500.com 数据源 ", font=self.bold_font, foreground="#E53935"))
        w500_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(w500_frame, text="比赛ID:", font=self.default_font).pack(side=tk.LEFT, padx=(10, 5), pady=10)
        self.w500_id_entry = ttk.Entry(w500_frame, font=self.default_font, width=20)
        self.w500_id_entry.pack(side=tk.LEFT, padx=5, pady=10)
        self.w500_fetch_button = ttk.Button(w500_frame, text="加载 500.com 欧赔", command=self.fetch_500_data)
        self.w500_fetch_button.pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Label(w500_frame, text="(请在500.com网站的赔率分析URL中找到比赛ID, 如 ozzhi-1278736.shtml 中的 1278736)", foreground="gray").pack(side=tk.LEFT, padx=10)

        # --- 数据表格 ---
        euro_frame = ttk.LabelFrame(main_frame, text=" 欧赔数据 (胜平负) ", labelwidget=tk.Label(main_frame, text=" 欧赔数据 (胜平负) ", font=self.bold_font, foreground="#0078D7")); euro_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10)); self.euro_tree = self._create_treeview(euro_frame, self._get_euro_columns())
        asia_frame = ttk.LabelFrame(main_frame, text=" 亚盘数据 (让球) ", labelwidget=tk.Label(main_frame, text=" 亚盘数据 (让球) ", font=self.bold_font, foreground="#4CAF50")); asia_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0)); self.asia_tree = self._create_treeview(asia_frame, self._get_asia_columns())
        
        self.status_label = ttk.Label(main_frame, text="正在加载默认数据...", font=self.default_font, foreground="orange"); self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(10,0))
        
        # 启动时自动加载默认数据源
        self.fetch_default_analysis_data()
        
    def _create_treeview(self, parent, columns_config):
        tree = ttk.Treeview(parent, columns=list(columns_config.keys()), show='headings', style="Analysis.Treeview")
        for col, (text, width, anchor) in columns_config.items():
            tree.heading(col, text=text); tree.column(col, width=width, anchor=anchor)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return tree

    def _get_euro_columns(self): return {'company': ('公司', 100, 'w'),'init_w': ('初盘-胜', 70, 'center'), 'init_d': ('初盘-平', 70, 'center'), 'init_l': ('初盘-负', 70, 'center'),'live_w': ('即时-胜', 70, 'center'), 'live_d': ('即时-平', 70, 'center'), 'live_l': ('即时-负', 70, 'center'),'payout': ('返还率', 80, 'center'),'kelly_w': ('凯利-胜', 70, 'center'), 'kelly_d': ('凯利-平', 70, 'center'), 'kelly_l': ('凯利-负', 70, 'center'),}
    def _get_asia_columns(self): return {'company': ('公司', 120, 'w'),'init_h': ('初盘-主', 80, 'center'), 'init_p': ('初盘-盘', 120, 'center'), 'init_a': ('初盘-客', 80, 'center'),'live_h': ('即时-主', 80, 'center'), 'live_p': ('即时-盘', 120, 'center'), 'live_a': ('即时-客', 80, 'center'),}
    
    # --- 默认数据源 (honghuodian) ---
    def fetch_default_analysis_data(self):
        analysis_id = self.match_data.get('match_id2') or self.match_data.get('match_id_2')
        if not analysis_id: self.status_label.config(text="错误: 缺少默认分析ID (match_id2)", foreground="red"); return
        threading.Thread(target=self._worker_fetch_default, args=(analysis_id,), daemon=True).start()
        
    def _worker_fetch_default(self, analysis_id):
        api_url = "https://apic.51honghuodian.com/api/match/analysis_v3"; params = {'platform': 'hhjdc_other', 'match_id': analysis_id}
        try:
            res = requests.get(api_url, params=params, headers=BROWSER_HEADERS, timeout=15)
            res.raise_for_status(); data = res.json()
            if data.get('errcode') != 0: raise Exception(data.get('msg', 'API返回错误'))
            odds_data = data.get('data', {}).get('odds', {}); euro_data = odds_data.get('euro', []); asia_data = odds_data.get('asia', [])
            self.after(0, self.populate_default_tables, euro_data, asia_data)
        except Exception as e:
            self.after(0, lambda err=e: self.status_label.config(text=f"默认数据加载失败: {err}", foreground="red"))
            
    def populate_default_tables(self, euro_data, asia_data):
        self._clear_all_tables()
        for company_data in euro_data:
            init = company_data.get('init', {}); live = company_data.get('live', {}); kelly = company_data.get('kelly', {})
            payout_rate = live.get('payout_rate'); payout_str = f"{payout_rate:.2%}" if isinstance(payout_rate, (int, float)) else ''
            values = (company_data.get('provider_name', ''), init.get('w', ''), init.get('d', ''), init.get('l', ''), live.get('w', ''), live.get('d', ''), live.get('l', ''), payout_str, kelly.get('w', ''), kelly.get('d', ''), kelly.get('l', ''))
            self.euro_tree.insert('', 'end', values=values)
        for company_data in asia_data:
            init = company_data.get('init', {}); live = company_data.get('live', {})
            values = (company_data.get('provider_name', ''), init.get('h', ''), init.get('p', ''), init.get('a', ''), live.get('h', ''), live.get('p', ''), live.get('a', ''))
            self.asia_tree.insert('', 'end', values=values)
        self.status_label.config(text=f"默认数据加载完成！共 {len(euro_data)} 家欧赔, {len(asia_data)} 家亚盘数据。", foreground="green")

    # --- 【新增】500.com 数据源 ---
    def fetch_500_data(self):
        match_id_500 = self.w500_id_entry.get().strip()
        if not match_id_500.isdigit():
            messagebox.showerror("输入错误", "请输入一个纯数字的比赛ID。")
            return
        self.status_label.config(text=f"正在从 500.com 加载比赛ID: {match_id_500} 的数据...", foreground="blue")
        self.w500_fetch_button.config(state="disabled")
        threading.Thread(target=self._worker_fetch_500, args=(match_id_500,), daemon=True).start()

    def _worker_fetch_500(self, match_id):
        api_url = f"https://odds.500.com/fenxi1/ouzhi.php?id={match_id}&ctype=1&start=0&end=500"
        headers_500 = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': f'https://odds.500.com/fenxi/ouzhi-{match_id}.shtml'
        }
        try:
            res = requests.get(api_url, headers=headers_500, timeout=15)
            res.raise_for_status()
            data = res.json()
            self.after(0, self.populate_500_table, data)
        except Exception as e:
            self.after(0, lambda err=e: self.status_label.config(text=f"500.com 数据加载失败: {err}", foreground="red"))
        finally:
            self.after(0, lambda: self.w500_fetch_button.config(state="normal"))

    def populate_500_table(self, odds_data):
        self._clear_all_tables()
        # 500.com 的数据格式是列表: [公司ID, 公司名, 初盘胜, 初盘平, 初盘负, 即时胜, 即时平, 即时负, ...]
        # 注意: 此API不直接提供返还率和凯利指数，因此我们留空
        for company_data in odds_data:
            values = (
                company_data[1], # 公司名
                company_data[2], company_data[3], company_data[4], # 初盘
                company_data[5], company_data[6], company_data[7], # 即时盘
                '', '', '', '' # 返还率和凯利指数留空
            )
            self.euro_tree.insert('', 'end', values=values)
        self.status_label.config(text=f"500.com 数据加载完成！共 {len(odds_data)} 家欧赔数据。(此源无亚盘)", foreground="#E53935")

    def _clear_all_tables(self):
        for item in self.euro_tree.get_children(): self.euro_tree.delete(item)
        for item in self.asia_tree.get_children(): self.asia_tree.delete(item)

# --- 主应用 (已更新标题) ---
class MegaFetcherApp:
    def __init__(self, root):
        self.root = root; self.root.title("MegaFetcher V4.5 - 500.com集成版"); self.root.geometry("1400x800")
        self.api_config = {"竞彩足球": {"style": "jczq", "api": "https://apic.51honghuodian.com/api/match/selectlist", "params": {'platform': 'hhjdc_other', '_prt': 'https', 'ver': '20180101000000', 'hide_more': '1'}}, "胜负彩14场": {"style": "sfc", "api": "https://apic.51honghuodian.com/api/toto/matchlist", "params": {'platform': 'hhjdc_other', 'lottery_type': 'ToTo-14'}}, "任选九场": {"style": "sfc", "api": "https://apic.51honghuodian.com/api/toto/matchlist", "params": {'platform': 'hhjdc_other', 'lottery_type': 'ToTo-R9'}},}
        self.cached_jczq_data = None; self.item_data_map = {}
        self.default_font = font.Font(family="Microsoft YaHei UI", size=11); self.bold_font = font.Font(family="Microsoft YaHei UI", size=12, weight="bold"); self.mono_font = font.Font(family="Consolas", size=11)
        style = ttk.Style(); style.configure("Treeview", rowheight=28, font=self.default_font); style.configure("Treeview.Heading", font=self.bold_font); style.map('Treeview', background=[('selected', '#0078D7')]); style.configure("Bold.TLabel", font=self.bold_font)
        self.paned_window = tk.PanedWindow(root, orient=tk.VERTICAL, sashrelief=tk.RAISED); self.paned_window.pack(fill=tk.BOTH, expand=True); self.main_frame = ttk.Frame(self.paned_window, padding="10"); self.debug_frame = ttk.Frame(self.paned_window, padding="10"); self.paned_window.add(self.main_frame, height=550); self.paned_window.add(self.debug_frame)
        self._create_main_widgets(); self._create_debug_widgets()
        self.root.after(100, lambda: self.on_game_type_select(None))

    def _create_main_widgets(self):
        parent = self.main_frame
        control_frame = ttk.Frame(parent); control_frame.pack(fill='x', side='top', pady=(0, 10))
        ttk.Label(control_frame, text="玩法:", font=self.bold_font).pack(side='left', padx=(0, 5))
        self.game_type_combo = ttk.Combobox(control_frame, state="readonly", font=self.default_font, width=15); self.game_type_combo['values'] = list(self.api_config.keys()); self.game_type_combo.current(0); self.game_type_combo.pack(side='left', padx=5); self.game_type_combo.bind("<<ComboboxSelected>>", self.on_game_type_select)
        ttk.Label(control_frame, text="期号/日期:", font=self.bold_font).pack(side='left', padx=(10, 5))
        self.issue_combo = ttk.Combobox(control_frame, state="disabled", font=self.default_font, width=20); self.issue_combo.pack(side='left', padx=5)
        self.fetch_button = ttk.Button(control_frame, text="  获 取  ", command=self.start_fetch_data); self.fetch_button.pack(side='left', padx=20)
        self.status_label = ttk.Label(control_frame, text="请选择玩法和期号", font=self.default_font, foreground="blue"); self.status_label.pack(side='left', padx=10)
        tree_frame = ttk.Frame(parent); tree_frame.pack(fill='both', expand=True)
        self.columns = ('seq', 'league', 'teams', 'time', 'match_id', 'odds1', 'odds2', 'odds3')
        self.tree = ttk.Treeview(tree_frame, columns=self.columns, show='headings')
        self.tree.bind("<Double-1>", self.on_double_click)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview); self.tree.configure(yscrollcommand=scrollbar.set); self.tree.pack(side='left', fill='both', expand=True); scrollbar.pack(side='right', fill='y')

    def on_double_click(self, event):
        item_id = self.tree.focus()
        if not item_id: return
        match_data = self.item_data_map.get(item_id)
        if not match_data: return
        # 即使没有默认ID，也允许打开窗口，因为用户可以手动输入500.com的ID
        AnalysisWindow(self.root, match_data)

    def clear_data(self): self.tree.delete(*self.tree.get_children()); self.item_data_map.clear()

    def on_game_type_select(self, event):
        game_type = self.game_type_combo.get()
        self.issue_combo.set(''); self.issue_combo.config(state="disabled"); self.fetch_button.config(state="disabled")
        self.clear_data(); self._setup_columns(game_type)
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
            res = requests.get(config['api'], params=config['params'], headers=BROWSER_HEADERS, timeout=15)
            res.raise_for_status(); data = res.json()
            if data.get('errcode') != 0: raise Exception(data.get('msg', 'API返回错误'))
            if game_type == "竞彩足球":
                self.cached_jczq_data = data['data']; issues = sorted(list(self.cached_jczq_data.keys()), reverse=True)
            else: issues = [item['lottery_no'] for item in data.get('data', {}).get('lottery_list', [])]
            self.root.after(0, self.update_issue_dropdown, game_type, issues)
        except Exception as e: self.root.after(0, lambda err=e: self.status_label.config(text=f"获取期号失败: {err}", foreground="red"))

    def start_fetch_data(self):
        game_type = self.game_type_combo.get(); issue = self.issue_combo.get()
        if not game_type or not issue: return
        self.fetch_button.config(state="disabled"); self.clear_data()
        self.status_label.config(text=f"正在获取<{issue}>的数据...", foreground="blue")
        if game_type == "竞彩足球": self.update_ui_jczq(issue)
        else: threading.Thread(target=self._fetch_match_data_worker, args=(game_type, issue), daemon=True).start()

    def _fetch_match_data_worker(self, game_type, issue):
        config = self.api_config[game_type]; params = config['params'].copy(); params['lottery_no'] = issue
        try:
            res = requests.get(config['api'], params=params, headers=BROWSER_HEADERS, timeout=15)
            res.raise_for_status(); data = res.json()
            if data.get('errcode') != 0: raise Exception(data.get('msg', 'API返回数据错误'))
            self.root.after(0, self.update_ui_sfc, data.get('data', {}).get('match', {}).get('list', []))
        except Exception as e: self.root.after(0, lambda err=e: self.status_label.config(text=f"获取对阵数据失败: {err}", foreground="red"))
        finally: self.root.after(0, lambda: self.fetch_button.config(state="normal"))

    def update_ui_jczq(self, date_key):
        matches_on_date = self.cached_jczq_data.get(date_key, {})
        match_list = sorted(matches_on_date.values(), key=lambda x: x.get('sort', 0))
        for match in match_list:
            had_odds = match.get('list', {}).get('SportteryNWDL', {}).get('odds', {})
            hhad_odds = match.get('list', {}).get('SportteryWDL', {}).get('odds', {})
            had_str = f"{had_odds.get('3', '-')} / {had_odds.get('1', '-')} / {had_odds.get('0', '-')}"
            hhad_str = f"{hhad_odds.get('3', '-')} / {hhad_odds.get('1', '-')} / {hhad_odds.get('0', '-')}"
            values = (match.get('serial_no', ''), match.get('league_name', ''), f"{match.get('host_name_s', '')} vs {match.get('guest_name_s', '')}", match.get('match_time', ''), match.get('match_id', ''), had_str, hhad_str, '')
            item_id = self.tree.insert('', 'end', values=values)
            self.item_data_map[item_id] = match
        self.status_label.config(text="数据显示完毕！双击行可弹出深度分析。", foreground="green"); self.fetch_button.config(state="normal")
    
    def update_ui_sfc(self, match_list):
        def safe_sort_key(match):
            try: return int(match.get('seq'))
            except (ValueError, TypeError): return 999
        for match in sorted(match_list, key=safe_sort_key):
            odds = match.get('odds', {})
            values = (match.get('seq', ''), match.get('league_name', ''), f"{match.get('host_name', '')} vs {match.get('guest_name', '')}", match.get('match_time', ''), match.get('match_id', ''), odds.get('3', '-'), odds.get('1', '-'), odds.get('0', '-'))
            item_id = self.tree.insert('', 'end', values=values)
            self.item_data_map[item_id] = match
        self.status_label.config(text="数据显示完毕！双击行可弹出深度分析。", foreground="green")
        
    def _setup_columns(self, game_type):
        for col in self.columns: self.tree.heading(col, text='')
        if game_type == "竞彩足球":
            headings, widths = ({'seq': '序号', 'league': '联赛', 'teams': '主队 vs 客队', 'time': '时间', 'match_id': '比赛ID', 'odds1': '胜平负 赔率', 'odds2': '让球(0) 赔率', 'odds3': ''}, {'seq': 60, 'league': 120, 'teams': 250, 'time': 160, 'match_id': 120, 'odds1': 200, 'odds2': 200, 'odds3': 0})
        else:
            headings, widths = ({'seq': '序号', 'league': '联赛', 'teams': '主队 vs 客队', 'time': '时间', 'match_id': '比赛ID', 'odds1': '胜赔(3)', 'odds2': '平赔(1)', 'odds3': '负赔(0)'}, {'seq': 60, 'league': 120, 'teams': 250, 'time': 160, 'match_id': 120, 'odds1': 100, 'odds2': 100, 'odds3': 100})
        for col, text in headings.items():
            self.tree.heading(col, text=text); self.tree.column(col, width=widths[col], anchor='w' if col == 'teams' else 'center')

    def update_issue_dropdown(self, game_type, issues):
        if not issues: self.status_label.config(text=f"未找到<{game_type}>的可用期号/日期", foreground="red"); return
        self.issue_combo['values'] = issues; self.issue_combo.current(0); self.issue_combo.config(state="readonly")
        self.fetch_button.config(state="normal"); self.status_label.config(text="准备就绪，请点击获取", foreground="green")

    def _create_debug_widgets(self): ttk.Label(self.debug_frame, text="调试信息窗口", style="Bold.TLabel").pack(anchor='w'); self.debug_text = scrolledtext.ScrolledText(self.debug_frame, height=10, font=self.mono_font, wrap=tk.WORD, relief='solid', borderwidth=1); self.debug_text.pack(fill='both', expand=True, pady=5); self.debug_text.config(state='disabled')
    def log_to_debug_window(self, message): pass

if __name__ == "__main__":
    root = tk.Tk()
    app = MegaFetcherApp(root)
    root.mainloop()

