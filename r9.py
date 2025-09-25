import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import itertools
import threading
import math
import random

class RenjiuProAppV11_2(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("足彩任九专业缩水工具 V11.2 (稳定版)")
        self.geometry("1450x950")
        
        # State Variables
        self.original_r9_bets = []
        self.filtered_r9_bets = []

        # UI Variables
        self.match_vars = [[tk.IntVar(value=0) for _ in range(3)] for _ in range(14)]
        self.odds_entries = [[tk.StringVar() for _ in range(3)] for _ in range(14)]
        self.banker_vars = [tk.IntVar(value=0) for _ in range(14)]
        self.filters = {}
        self.total_tolerance_var = tk.StringVar(value='0')
        
        self._create_widgets()
        self._prefill_example_data()
        self._set_ui_state('initial')

    def _create_widgets(self):
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_pane, width=450)
        main_pane.add(left_frame, weight=1)
        
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=2)
        
        input_frame = ttk.LabelFrame(left_frame, text=" ① 选择场次与赛果 ", padding=10)
        input_frame.pack(fill=tk.Y, expand=True, padx=5, pady=5)
        headers = ["场", "3", "赔率", "1", "赔率", "0", "赔率", "胆"]; [ttk.Label(input_frame, text=h, font=("", 9, "bold")).grid(row=0, column=col, padx=3, pady=5) for col, h in enumerate(headers)]
        for i in range(14):
            ttk.Label(input_frame, text=f"{i+1:02d}").grid(row=i+1, column=0); ttk.Checkbutton(input_frame, variable=self.match_vars[i][0]).grid(row=i+1, column=1)
            ttk.Entry(input_frame, textvariable=self.odds_entries[i][0], width=5).grid(row=i+1, column=2); ttk.Checkbutton(input_frame, variable=self.match_vars[i][1]).grid(row=i+1, column=3)
            ttk.Entry(input_frame, textvariable=self.odds_entries[i][1], width=5).grid(row=i+1, column=4); ttk.Checkbutton(input_frame, variable=self.match_vars[i][2]).grid(row=i+1, column=5)
            ttk.Entry(input_frame, textvariable=self.odds_entries[i][2], width=5).grid(row=i+1, column=6); ttk.Checkbutton(input_frame, variable=self.banker_vars[i]).grid(row=i+1, column=7)
        self.bet_info_label = ttk.Label(input_frame, text="", font=("", 10, "bold"), foreground="blue"); self.bet_info_label.grid(row=15, column=0, columnspan=8, pady=(10, 5), sticky='w')

        filter_area = ttk.Frame(right_frame); filter_area.pack(fill='x')
        notebook_filters = ttk.Notebook(filter_area); notebook_filters.pack(fill="x", expand=True, pady=5)
        tab_common, tab_advanced, tab_odds = ttk.Frame(notebook_filters, padding=10), ttk.Frame(notebook_filters, padding=10), ttk.Frame(notebook_filters, padding=10)
        notebook_filters.add(tab_common, text="常用过滤"); notebook_filters.add(tab_advanced, text="高级指标"); notebook_filters.add(tab_odds, text="赔率指标")
        self._populate_filters(tab_common, tab_advanced, tab_odds)
        
        output_area = ttk.Frame(right_frame); output_area.pack(fill='both', expand=True, pady=10)
        control_frame = ttk.Frame(output_area); control_frame.pack(fill='x', pady=5)
        
        tolerance_frame = ttk.Frame(control_frame); tolerance_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(tolerance_frame, text="总容错数 ≤").pack(side=tk.LEFT); ttk.Entry(tolerance_frame, textvariable=self.total_tolerance_var, width=5).pack(side=tk.LEFT, padx=5)

        button_frame = ttk.Frame(control_frame); button_frame.pack(side=tk.LEFT, padx=20)
        self.calc_button = ttk.Button(button_frame, text="① 计算投注", command=self.start_calculation_thread, style="Accent.TButton")
        self.calc_button.pack(side=tk.LEFT, padx=5, ipady=5)
        self.filter_button = ttk.Button(button_frame, text="② 开始过滤", command=self.start_filter_thread)
        self.filter_button.pack(side=tk.LEFT, padx=5, ipady=5)
        self.wheel_button = ttk.Button(button_frame, text="③ 旋转矩阵(保8)", command=self.start_wheeling_thread)
        self.wheel_button.pack(side=tk.LEFT, padx=5, ipady=5)
        self.clear_button = ttk.Button(button_frame, text="清空所有", command=self.clear_all)
        self.clear_button.pack(side=tk.LEFT, padx=5, ipady=5)

        self.progress_bar = ttk.Progressbar(output_area, orient='horizontal', mode='determinate'); self.progress_bar.pack(fill=tk.X, pady=5)
        self.status_label = ttk.Label(output_area, text="欢迎使用专业版缩水工具 V11.2。请先选择场次，然后点击 [计算投注]。"); self.status_label.pack(fill=tk.X, pady=5)
        
        result_frame_container = ttk.Frame(output_area); result_frame_container.pack(fill=tk.BOTH, expand=True)
        self.result_text = scrolledtext.ScrolledText(result_frame_container, wrap=tk.WORD, state='disabled', height=10, font=("Courier New", 10))
        self.result_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.copy_button = ttk.Button(result_frame_container, text="复制结果到剪贴板", command=self.copy_results)
        self.copy_button.pack(side=tk.BOTTOM, fill=tk.X, pady=(5,0))
    
    # --- UI STATE MAnAGEMENT ---
    def _set_ui_state(self, state):
        states = {
            'calculating': ('disabled', 'disabled', 'disabled', 'disabled'),
            'calculated': ('normal', 'normal', 'disabled', 'normal'),
            'filtering': ('disabled', 'disabled', 'disabled', 'disabled'),
            'filtered': ('normal', 'normal', 'normal', 'normal'),
            'wheeling': ('disabled', 'disabled', 'disabled', 'disabled'),
            'wheeled': ('normal', 'normal', 'normal', 'normal'),
            'initial': ('normal', 'disabled', 'disabled', 'normal')
        }
        c, f, w, cl = states.get(state, states['initial'])
        self.calc_button.config(state=c)
        self.filter_button.config(state=f)
        self.wheel_button.config(state=w)
        self.clear_button.config(state=cl)
    
    # --- WORKFLOW STEPS ---
    def start_calculation_thread(self):
        self._set_ui_state('calculating'); self.original_r9_bets.clear()
        threading.Thread(target=self.run_calculation_logic, daemon=True).start()

    def run_calculation_logic(self):
        try:
            base_selections = {i: [k for j, k in enumerate('310') if self.match_vars[i][j].get()] for i in range(14)}
            selected_indices = [i for i, opts in base_selections.items() if opts]
            banker_indices = {i for i, v in enumerate(self.banker_vars) if v.get()}
            if len(selected_indices) < 9 or len(banker_indices) > 9 or not banker_indices.issubset(set(selected_indices)):
                self.after(0, lambda: messagebox.showerror("选择错误", "场次选择需>=9场, 胆码需<=9个且在所选场次中。"))
                return
            
            dynamic_indices = [i for i in selected_indices if i not in banker_indices]
            num_to_choose = 9 - len(banker_indices)
            
            self.after(0, self.status_label.config, {'text': "正在生成所有任九组合..."})
            self.after(0, self.progress_bar.config, {'mode': 'indeterminate'}); self.after(0, self.progress_bar.start)
            
            for dynamic_combo in itertools.combinations(dynamic_indices, num_to_choose):
                r9_indices = tuple(sorted(list(banker_indices) + list(dynamic_combo)))
                r9_options = [base_selections[idx] for idx in r9_indices]
                for r9_outcomes in itertools.product(*r9_options):
                    bet_list = ['*'] * 14
                    for match_idx, outcome in zip(r9_indices, r9_outcomes): bet_list[match_idx] = outcome
                    self.original_r9_bets.append("".join(bet_list))

            msg = f"计算完成: 原始任九投注共 {len(self.original_r9_bets):,} 注。"
            self.after(0, self.bet_info_label.config, {'text': msg, 'foreground': 'green'})
            self.after(0, self.status_label.config, {'text': "原始投注计算完毕，可以开始过滤。"})
        finally:
            self.after(0, self.progress_bar.stop); self.after(0, self.progress_bar.config, {'mode': 'determinate', 'value': 0})
            self.after(0, self._set_ui_state, 'calculated')

    def start_filter_thread(self):
        if not self.original_r9_bets: messagebox.showwarning("提示", "请先点击 [计算投注] 生成原始方案。"); return
        self._set_ui_state('filtering'); self.filtered_r9_bets.clear()
        threading.Thread(target=self.run_filter_logic, daemon=True).start()
    
    def run_filter_logic(self):
        try:
            active_filters = self._get_active_filters()
            if active_filters is None: return

            if not active_filters: 
                self.filtered_r9_bets = self.original_r9_bets.copy()
            else:
                try: total_tolerance = int(self.total_tolerance_var.get())
                except ValueError: self.after(0, lambda: messagebox.showerror("输入错误", "总容错数必须是整数。")); return
                
                self.after(0, self.progress_bar.config, {'maximum': len(self.original_r9_bets), 'value': 0})
                
                for i, bet_str in enumerate(self.original_r9_bets):
                    if i % 500 == 0: self.after(0, lambda i=i: self.progress_bar.config(value=i) or self.status_label.config(text=f"正在过滤 {i}/{len(self.original_r9_bets)}..."))
                    
                    bet_tuple = tuple(int(c) if c != '*' else -1 for c in bet_str); errors = 0; failed = False
                    for key, config in active_filters:
                        val = config["fn"](bet_str, bet_tuple)
                        if not (config['min'] <= val <= config['max']):
                            if config['tolerance']: errors += 1
                            else: failed = True; break
                    if not failed and errors > total_tolerance: failed = True
                    if not failed: self.filtered_r9_bets.append(bet_str)
            
            self.after(0, self.display_results, "【过滤完成】", len(self.original_r9_bets), len(self.filtered_r9_bets), self.filtered_r9_bets)
        finally:
            self.after(0, self._set_ui_state, 'filtered' if self.filtered_r9_bets else 'calculated')

    def start_wheeling_thread(self):
        if not self.filtered_r9_bets: messagebox.showwarning("提示", "没有可供旋转的结果，请先进行过滤。"); return
        self._set_ui_state('wheeling')
        threading.Thread(target=self.run_wheeling_logic, daemon=True).start()

    def run_wheeling_logic(self):
        try:
            tickets_to_cover = set(self.filtered_r9_bets); num_tickets = len(tickets_to_cover); wheeled_tickets = []
            self.after(0, self.progress_bar.config, {'maximum': num_tickets, 'value': 0})
            
            while tickets_to_cover:
                progress = num_tickets - len(tickets_to_cover)
                if progress % 50 == 0: self.after(0, lambda p=progress: self.status_label.config(text=f"旋转中...已覆盖 {p}/{num_tickets}") or self.progress_bar.config(value=p))
                
                best_ticket, max_coverage = None, -1
                potential_best = random.sample(list(tickets_to_cover), min(len(tickets_to_cover), 100))
                for ticket in potential_best:
                    neighbors = self._get_8_of_9_neighbors(ticket); neighbors.add(ticket)
                    coverage = len(tickets_to_cover.intersection(neighbors))
                    if coverage > max_coverage: max_coverage, best_ticket = coverage, ticket
                
                if best_ticket is None: best_ticket = tickets_to_cover.pop()
                    
                wheeled_tickets.append(best_ticket)
                neighbors_of_best = self._get_8_of_9_neighbors(best_ticket); neighbors_of_best.add(best_ticket)
                tickets_to_cover -= neighbors_of_best

            self.after(0, self.display_results, "【旋转(保8)完成】", len(self.filtered_r9_bets), len(wheeled_tickets), wheeled_tickets)
        finally:
            self.after(0, self._set_ui_state, 'wheeled')
    
    # --- HELPER & UTILITY FUNCTIONS ---
    def _get_8_of_9_neighbors(self, r9_ticket):
        neighbors, indices, options = set(), [i for i, char in enumerate(r9_ticket) if char != '*'], ['3', '1', '0']
        for i in indices:
            original_char = r9_ticket[i]
            for new_char in options:
                if new_char != original_char:
                    neighbor_list = list(r9_ticket); neighbor_list[i] = new_char; neighbors.add("".join(neighbor_list))
        return neighbors

    def copy_results(self):
        content = self.result_text.get("1.0", tk.END).strip()
        if content: self.clipboard_clear(); self.clipboard_append(content); self.status_label.config(text=f"已复制 {len(content.splitlines())} 注结果到剪贴板。")

    def display_results(self, prefix, c1, c2, final_list):
        msg = f"{prefix} 原始: {c1:,} 注 -> 结果: {c2:,} 注"
        self.status_label.config(text=msg)
        self.result_text.config(state='normal'); self.result_text.delete('1.0', tk.END)
        final_list.sort()
        limit = 20000
        if len(final_list) > limit: self.result_text.insert(tk.END, f"结果超过 {limit:,} 注，仅显示前 {limit:,} 注。\n\n"); final_list = final_list[:limit]
        self.result_text.insert(tk.END, "\n".join(final_list)); self.result_text.config(state='disabled')
        self.progress_bar.config(value=self.progress_bar['maximum'])
    
    def clear_all(self):
        self.original_r9_bets.clear(); self.filtered_r9_bets.clear()
        for row in self.match_vars: [v.set(0) for v in row]
        for v in self.banker_vars: v.set(0)
        for config in self.filters.values(): config["is_active_var"].set(0); config["min_var"].set(''); config["max_var"].set(''); config["tolerance_var"].set(0)
        self.result_text.config(state='normal'); self.result_text.delete('1.0', tk.END); self.result_text.config(state='disabled')
        self.status_label.config(text="已清空所有选项。请重新选择并计算投注。")
        self.progress_bar.config(value=0); self.total_tolerance_var.set("0"); self.bet_info_label.config(text="")
        self._set_ui_state('initial')

    # --- FILTERING LOGIC (REWRITTEN IN V11.2 FOR STABILITY) ---
    def _calculate_breaks(self, bet_str, *args):
        eb = [c for c in bet_str if c != '*']
        if len(eb) < 2: return 0
        return sum(1 for i in range(len(eb) - 1) if eb[i] != eb[i+1])

    def _calculate_blocks(self, bet_str, *args):
        eb = [c for c in bet_str if c != '*']
        if not eb: return 0
        return len(list(itertools.groupby(eb)))
        
    def _calculate_max_consecutive(self, bet_str, targets, *args):
        eb = [c for c in bet_str if c != '*']
        max_len, current_len = 0, 0
        for result in eb:
            if result in targets: current_len += 1
            else: max_len = max(max_len, current_len); current_len = 0
        return max(max_len, current_len)

    def _get_metric_function(self, key):
        if 'count_3' == key: return lambda b, bt: b.count('3')
        if 'count_1' == key: return lambda b, bt: b.count('1')
        if 'count_0' == key: return lambda b, bt: b.count('0')
        if 'sum' == key: return lambda b, bt: sum(n for n in bt if n != -1)
        if 'breaks' == key: return self._calculate_breaks
        if 'blocks' == key: return self._calculate_blocks
        if key.startswith('consecutive'):
            targets = {'3'}
            if '1' in key and '0' not in key: targets = {'1'}
            if '0' in key and '1' not in key: targets = {'0'}
            if '31' in key: targets = {'3', '1'}
            if '10' in key: targets = {'1', '0'}
            return lambda b, bt: self._calculate_max_consecutive(b, targets)
        return lambda *a: 0

    def _get_active_filters(self):
        filters = []
        for key, config in self.filters.items():
            if config["is_active_var"].get():
                try:
                    min_s, max_s = config['min_var'].get(), config['max_var'].get()
                    if not min_s and not max_s: continue
                    min_v = float(min_s) if min_s else -float('inf')
                    max_v = float(max_s) if max_s else float('inf')
                    filters.append((key, {"fn": config["fn"], "min": min_v, "max": max_v, "tolerance": config['tolerance_var'].get() == 1}))
                except ValueError: messagebox.showerror("输入错误", f"条件 '{config['name']}' 的值不是有效的数字。"); return None
        return filters

    def _populate_filters(self,tab_common,tab_advanced,tab_odds):
        h=["选择"," ","","过滤条件",""," ","容错"];[ttk.Label(t,text=x,font=("",9,"bold")).grid(row=0,column=i,padx=2,pady=(0,10))for t in [tab_common,tab_advanced,tab_odds] for i,x in enumerate(h)]
        f_list=[('count_3','胜场数',0,9),('count_1','平场数',0,9),('count_0','负场数',0,9),('sum','积分和',0,27),('breaks','断点数',0,8),('blocks','连号个数',0,9),('consecutive_3','主胜连号',0,9),('consecutive_1','连平',0,9),('consecutive_0','主负连号',0,9),('consecutive_31','不败连号',0,9),('consecutive_10','不胜连号',0,9)];[self._create_filter_row(tab_common,*f) for f in f_list]

    def _create_filter_row(self,parent,key,name,r_from,r_to):
        row=len(parent.winfo_children());is_active,min_v,max_v,tol=tk.IntVar(),tk.StringVar(),tk.StringVar(),tk.IntVar()
        self.filters[key]={"name":name,"is_active_var":is_active,"min_var":min_v,"max_var":max_v,"tolerance_var":tol,"fn":self._get_metric_function(key)}
        ttk.Checkbutton(parent,variable=is_active).grid(row=row,column=0);ttk.Spinbox(parent,from_=r_from,to=r_to,textvariable=min_v,width=6).grid(row=row,column=1);ttk.Label(parent,text=" ≤ ").grid(row=row,column=2)
        ttk.Label(parent,text=name,width=12,anchor='w').grid(row=row,column=3,sticky='w');ttk.Label(parent,text=" ≤ ").grid(row=row,column=4);ttk.Spinbox(parent,from_=r_from,to=r_to,textvariable=max_v,width=6).grid(row=row,column=5)
        ttk.Checkbutton(parent,variable=tol).grid(row=row,column=6,padx=(15,0))

    def _prefill_example_data(self):
        s=[[1,1,0],[1,0,0],[1,1,0],[0,1,1],[1,0,0],[1,1,1],[1,1,0],[0,0,1],[1,1,0],[0,1,1],[1,0,1],[1,1,0],[0,0,1],[1,1,0]]; o=[[1.8,3.5,4.0],[1.5,4.0,5.5],[2.1,3.3,3.1],[3.5,3.4,2.0],[1.9,3.2,3.8],[2.5,3.0,2.8],[1.7,3.6,4.5],[4.2,3.8,1.8],[2.2,3.3,2.9],[3.0,3.1,2.3],[1.6,3.7,5.0],[2.0,3.2,3.6],[5.5,4.0,1.5],[1.9,3.4,3.9]]
        for i in range(14): [self.match_vars[i][j].set(s[i][j]) for j in range(3)]; [self.odds_entries[i][j].set(str(o[i][j])) for j in range(3)]
        self.filters['count_3']['is_active_var'].set(1);self.filters['count_3']['min_var'].set('3');self.filters['count_3']['max_var'].set('6');self.filters['sum']['is_active_var'].set(1);self.filters['sum']['min_var'].set('15');self.filters['sum']['max_var'].set('22')

if __name__ == "__main__":
    app = RenjiuProAppV11_2()
    app.mainloop()

