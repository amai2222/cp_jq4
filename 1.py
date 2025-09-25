import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import itertools
import threading
import operator

class LotteryFilterAppPro(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("足彩缩水工具 (专业版)")
        self.geometry("1100x800")

        # --- Data Variables ---
        self.match_vars = []
        self.odds_entries = [] # To store odds entry widgets
        for i in range(14):
            self.match_vars.append([tk.IntVar(value=0) for _ in range(3)])
            self.odds_entries.append([tk.StringVar() for _ in range(3)])

        self._create_widgets()
        self._prefill_example_data() # Add example data for quick testing

    def _create_widgets(self):
        # --- Main Layout ---
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        input_frame = ttk.LabelFrame(main_frame, text=" ① 基准方案与赔率输入 ", padding=10)
        input_frame.grid(row=0, column=0, sticky="ns", pady=5)
        
        filter_notebook_frame = ttk.Frame(main_frame)
        filter_notebook_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)
        main_frame.grid_columnconfigure(1, weight=1)

        output_frame = ttk.LabelFrame(self, text=" ③ 缩水结果 ", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Input Widgets (Left Side) ---
        headers = ["场次", "主胜(3)", "赔率", "平局(1)", "赔率", "客胜(0)", "赔率"]
        for col, header in enumerate(headers):
            ttk.Label(input_frame, text=header, font=("", 9, "bold")).grid(row=0, column=col, padx=4, pady=5)

        for i in range(14):
            ttk.Label(input_frame, text=f"第 {i+1:02d} 場").grid(row=i+1, column=0, sticky="w")
            ttk.Checkbutton(input_frame, variable=self.match_vars[i][0]).grid(row=i+1, column=1)
            ttk.Entry(input_frame, textvariable=self.odds_entries[i][0], width=6).grid(row=i+1, column=2, padx=(0,5))
            ttk.Checkbutton(input_frame, variable=self.match_vars[i][1]).grid(row=i+1, column=3)
            ttk.Entry(input_frame, textvariable=self.odds_entries[i][1], width=6).grid(row=i+1, column=4, padx=(0,5))
            ttk.Checkbutton(input_frame, variable=self.match_vars[i][2]).grid(row=i+1, column=5)
            ttk.Entry(input_frame, textvariable=self.odds_entries[i][2], width=6).grid(row=i+1, column=6)

        # --- Filter Widgets (Right Side using Notebook) ---
        notebook = ttk.Notebook(filter_notebook_frame)
        notebook.pack(fill="both", expand=True)
        
        tab1 = ttk.Frame(notebook, padding=10)
        tab2 = ttk.Frame(notebook, padding=10)
        tab3 = ttk.Frame(notebook, padding=10)
        
        notebook.add(tab1, text="基本指标")
        notebook.add(tab2, text="赔率指标")
        notebook.add(tab3, text="形态指标")

        self.filters = {}

        # --- Tab 1: Basic Filters ---
        self._create_basic_filters_tab(tab1)
        
        # --- Tab 2: Odds Filters ---
        self._create_odds_filters_tab(tab2)
        
        # --- Tab 3: Pattern Filters ---
        self._create_pattern_filters_tab(tab3)

        # --- Control Buttons ---
        control_frame = ttk.Frame(filter_notebook_frame)
        control_frame.pack(pady=20)
        self.start_button = ttk.Button(control_frame, text="开始缩水", command=self.start_filtering_thread, style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=10, ipady=5)
        self.clear_button = ttk.Button(control_frame, text="清空所有", command=self.clear_all)
        self.clear_button.pack(side=tk.LEFT, padx=10, ipady=5)

        # --- Output Widgets (Bottom) ---
        self.status_label = ttk.Label(output_frame, text="请在左侧选择投注并输入赔率，然后在右侧设置条件。")
        self.status_label.pack(fill=tk.X, pady=5)
        
        self.progress_bar = ttk.Progressbar(output_frame, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.result_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, state='disabled', height=15)
        self.result_text.pack(fill=tk.BOTH, expand=True)

    def _create_filter_entry_group(self, parent, text, min_key, max_key):
        ttk.Label(parent, text=text).pack(side=tk.LEFT, padx=(0, 5))
        min_entry = ttk.Entry(parent, width=6, textvariable=tk.StringVar())
        min_entry.pack(side=tk.LEFT)
        self.filters[min_key] = min_entry
        ttk.Label(parent, text="—").pack(side=tk.LEFT, padx=3)
        max_entry = ttk.Entry(parent, width=6, textvariable=tk.StringVar())
        max_entry.pack(side=tk.LEFT, padx=(0, 15))
        self.filters[max_key] = max_entry

    def _create_basic_filters_tab(self, tab):
        frm = ttk.LabelFrame(tab, text="赛果个数范围", padding=10)
        frm.pack(fill=tk.X, pady=5)
        f1 = ttk.Frame(frm); f1.pack(fill=tk.X, pady=3)
        self._create_filter_entry_group(f1, "主胜(3)个数:", "min_count_3", "max_count_3")
        f2 = ttk.Frame(frm); f2.pack(fill=tk.X, pady=3)
        self._create_filter_entry_group(f2, "平局(1)个数:", "min_count_1", "max_count_1")
        f3 = ttk.Frame(frm); f3.pack(fill=tk.X, pady=3)
        self._create_filter_entry_group(f3, "客胜(0)个数:", "min_count_0", "max_count_0")

        frm = ttk.LabelFrame(tab, text="14场赛果累加和", padding=10)
        frm.pack(fill=tk.X, pady=10)
        f4 = ttk.Frame(frm); f4.pack(fill=tk.X, pady=3)
        self._create_filter_entry_group(f4, "累加和范围:", "min_sum", "max_sum")

    def _create_odds_filters_tab(self, tab):
        ttk.Label(tab, text="注意：使用本页功能必须在左侧输入对应赔率！", foreground="red").pack(pady=5)
        frm = ttk.LabelFrame(tab, text="赔率积与赔率和", padding=10)
        frm.pack(fill=tk.X, pady=5)
        f1 = ttk.Frame(frm); f1.pack(fill=tk.X, pady=3)
        self._create_filter_entry_group(f1, "赔率和范围:", "min_odds_sum", "max_odds_sum")
        f2 = ttk.Frame(frm); f2.pack(fill=tk.X, pady=3)
        self._create_filter_entry_group(f2, "赔率积范围:", "min_odds_product", "max_odds_product")

        frm = ttk.LabelFrame(tab, text="第一/二/三赔率个数", padding=10)
        frm.pack(fill=tk.X, pady=10)
        f3 = ttk.Frame(frm); f3.pack(fill=tk.X, pady=3)
        self._create_filter_entry_group(f3, "第一赔率个数:", "min_first_odds", "max_first_odds")
        f4 = ttk.Frame(frm); f4.pack(fill=tk.X, pady=3)
        self._create_filter_entry_group(f4, "第二赔率个数:", "min_second_odds", "max_second_odds")
        f5 = ttk.Frame(frm); f5.pack(fill=tk.X, pady=3)
        self._create_filter_entry_group(f5, "第三赔率个数:", "min_third_odds", "max_third_odds")
        
    def _create_pattern_filters_tab(self, tab):
        frm = ttk.LabelFrame(tab, text="最大连续赛果个数", padding=10)
        frm.pack(fill=tk.X, pady=5)
        f1 = ttk.Frame(frm); f1.pack(fill=tk.X, pady=3)
        self._create_filter_entry_group(f1, "连续主胜(3):", None, "max_consecutive_3")
        f2 = ttk.Frame(frm); f2.pack(fill=tk.X, pady=3)
        self._create_filter_entry_group(f2, "连续平局(1):", None, "max_consecutive_1")
        f3 = ttk.Frame(frm); f3.pack(fill=tk.X, pady=3)
        self._create_filter_entry_group(f3, "连续客胜(0):", None, "max_consecutive_0")

        frm = ttk.LabelFrame(tab, text="间断点个数", padding=10)
        frm.pack(fill=tk.X, pady=10)
        f4 = ttk.Frame(frm); f4.pack(fill=tk.X, pady=3)
        self._create_filter_entry_group(f4, "变化次数范围:", "min_breaks", "max_breaks")

    def _prefill_example_data(self):
        """ Fills the form with some example data for demonstration. """
        example_selections = [
            [1, 1, 0], [1, 0, 0], [1, 1, 0], [0, 1, 1], [1, 0, 0],
            [1, 1, 1], [1, 1, 0], [0, 0, 1], [1, 1, 0], [0, 1, 1],
            [1, 0, 1], [1, 1, 0], [0, 0, 1], [1, 1, 0]
        ]
        example_odds = [
            [1.8, 3.5, 4.0], [1.5, 4.0, 5.5], [2.1, 3.3, 3.1], [3.5, 3.4, 2.0], [1.9, 3.2, 3.8],
            [2.5, 3.0, 2.8], [1.7, 3.6, 4.5], [4.2, 3.8, 1.8], [2.2, 3.3, 2.9], [3.0, 3.1, 2.3],
            [1.6, 3.7, 5.0], [2.0, 3.2, 3.6], [5.5, 4.0, 1.5], [1.9, 3.4, 3.9]
        ]
        for i in range(14):
            for j in range(3):
                self.match_vars[i][j].set(example_selections[i][j])
                self.odds_entries[i][j].set(example_odds[i][j])
        
        # Example filters
        self.filters["min_count_3"].insert(0, "6")
        self.filters["max_count_3"].insert(0, "9")
        self.filters["min_count_1"].insert(0, "3")
        self.filters["max_count_1"].insert(0, "5")
        self.filters["min_first_odds"].insert(0, "7")
        self.filters["max_first_odds"].insert(0, "10")
        self.filters["max_third_odds"].insert(0, "2")
        self.status_label.config(text="已加载示例数据，可直接点击“开始缩水”测试。")

    def get_params(self):
        params = {}
        for key, widget in self.filters.items():
            if widget is None: continue
            val = widget.get()
            try:
                # Use float for odds-related filters, int for others
                if "odds" in key:
                    params[key] = float(val) if val else None
                else:
                    params[key] = int(val) if val else None
            except ValueError:
                messagebox.showerror("输入错误", f"条件 '{key}' 的值 '{val}' 格式不正确。")
                return None
        return params
        
    def prepare_odds_data(self):
        """Reads and processes odds from the GUI."""
        odds_data = [] # List of dicts for each match: {'3': 2.1, '1': 3.3, '0': 3.1}
        odds_ranks = [] # List of dicts: {'3': 1, '1': 3, '0': 2} 1=1st, 2=2nd, 3=3rd lowest odd

        for i in range(14):
            try:
                match_odds_map = {
                    '3': float(self.odds_entries[i][0].get()),
                    '1': float(self.odds_entries[i][1].get()),
                    '0': float(self.odds_entries[i][2].get())
                }
                odds_data.append(match_odds_map)
                
                # Rank odds for this match. Handle ties by preferring 3 > 1 > 0
                # Sort by value (odd), then by key ('3','1','0') descending for tie-breaking
                sorted_odds = sorted(match_odds_map.items(), key=lambda item: (item[1], -int(item[0])))
                
                rank_map = {}
                for rank, (outcome, _) in enumerate(sorted_odds, 1):
                    rank_map[outcome] = rank
                odds_ranks.append(rank_map)

            except (ValueError, TypeError):
                 messagebox.showerror("赔率错误", f"第 {i+1} 场的赔率输入不正确或不完整。")
                 return None, None
        return odds_data, odds_ranks

    def start_filtering_thread(self):
        self.start_button.config(state='disabled')
        self.clear_button.config(state='disabled')
        self.status_label.config(text="正在准备计算...")
        thread = threading.Thread(target=self.run_filter_logic)
        thread.daemon = True
        thread.start()

    def run_filter_logic(self):
        # 1. Get base ticket
        base_ticket = []
        for i in range(14):
            choices = [k for j, k in enumerate('310') if self.match_vars[i][j].get() == 1]
            if not choices:
                messagebox.showerror("输入错误", f"第 {i+1} 场没有选择任何赛果。")
                self.reset_ui_state(); return
            base_ticket.append(choices)

        # 2. Get filter parameters
        params = self.get_params()
        if params is None: self.reset_ui_state(); return

        # 3. Prepare odds data
        odds_data, odds_ranks = self.prepare_odds_data()
        if odds_data is None: self.reset_ui_state(); return

        # 4. Expand base ticket
        try:
            expanded_bets = list(itertools.product(*base_ticket))
            original_count = len(expanded_bets)
        except Exception as e:
            messagebox.showerror("计算错误", f"无法展开投注，错误: {e}")
            self.reset_ui_state(); return

        if original_count == 0:
            self.status_label.config(text="没有有效的基准投注方案。"); self.reset_ui_state(); return

        self.status_label.config(text=f"原始投注展开: {original_count} 注。开始过滤...")
        self.update_idletasks()

        # 5. Filtering logic
        filtered_bets = []
        self.progress_bar['maximum'] = original_count
        
        for i, bet in enumerate(expanded_bets):
            if i % 5000 == 0:
                self.progress_bar['value'] = i
                self.status_label.config(text=f"正在处理: {i}/{original_count}...")
                self.update_idletasks()

            c3, c1, c0 = bet.count('3'), bet.count('1'), bet.count('0')
            if (params.get("min_count_3") is not None and c3 < params["min_count_3"]) or \
               (params.get("max_count_3") is not None and c3 > params["max_count_3"]) or \
               (params.get("min_count_1") is not None and c1 < params["min_count_1"]) or \
               (params.get("max_count_1") is not None and c1 > params["max_count_1"]) or \
               (params.get("min_count_0") is not None and c0 < params["min_count_0"]) or \
               (params.get("max_count_0") is not None and c0 > params["max_count_0"]):
                continue

            bet_sum = sum(int(x) for x in bet)
            if (params.get("min_sum") is not None and bet_sum < params["min_sum"]) or \
               (params.get("max_sum") is not None and bet_sum > params["max_sum"]):
                continue
            
            # --- Odds Filters ---
            odds_sum = sum(odds_data[m][bet[m]] for m in range(14))
            if (params.get("min_odds_sum") is not None and odds_sum < params["min_odds_sum"]) or \
               (params.get("max_odds_sum") is not None and odds_sum > params["max_odds_sum"]):
                continue

            odds_prod = 1
            if params.get("min_odds_product") or params.get("max_odds_product"):
                for m in range(14): odds_prod *= odds_data[m][bet[m]]
                if (params.get("min_odds_product") is not None and odds_prod < params["min_odds_product"]) or \
                   (params.get("max_odds_product") is not None and odds_prod > params["max_odds_product"]):
                    continue

            r1 = sum(1 for m in range(14) if odds_ranks[m][bet[m]] == 1)
            r2 = sum(1 for m in range(14) if odds_ranks[m][bet[m]] == 2)
            r3 = 14 - r1 - r2
            if (params.get("min_first_odds") is not None and r1 < params["min_first_odds"]) or \
               (params.get("max_first_odds") is not None and r1 > params["max_first_odds"]) or \
               (params.get("min_second_odds") is not None and r2 < params["min_second_odds"]) or \
               (params.get("max_second_odds") is not None and r2 > params["max_second_odds"]) or \
               (params.get("min_third_odds") is not None and r3 < params["min_third_odds"]) or \
               (params.get("max_third_odds") is not None and r3 > params["max_third_odds"]):
                continue

            # --- Pattern Filters ---
            if (params.get("max_consecutive_3") is not None and self.get_max_consecutive(bet, '3') > params["max_consecutive_3"]) or \
               (params.get("max_consecutive_1") is not None and self.get_max_consecutive(bet, '1') > params["max_consecutive_1"]) or \
               (params.get("max_consecutive_0") is not None and self.get_max_consecutive(bet, '0') > params["max_consecutive_0"]):
                continue

            breaks = sum(1 for m in range(13) if bet[m] != bet[m+1])
            if (params.get("min_breaks") is not None and breaks < params["min_breaks"]) or \
               (params.get("max_breaks") is not None and breaks > params["max_breaks"]):
                continue
            
            filtered_bets.append("".join(bet))

        self.display_results(original_count, filtered_bets)

    def get_max_consecutive(self, bet, target):
        return max(len(list(g)) for k, g in itertools.groupby(bet) if k == target) if target in bet else 0
        
    def display_results(self, original_count, filtered_bets):
        self.progress_bar['value'] = self.progress_bar['maximum']
        final_count = len(filtered_bets)
        self.status_label.config(text=f"过滤完成！原始注数: {original_count}, 缩水后注数: {final_count}")
        
        self.result_text.config(state='normal')
        self.result_text.delete('1.0', tk.END)
        
        display_limit = 5000
        if final_count > display_limit:
             self.result_text.insert(tk.END, f"结果超过{display_limit}注，仅显示前{display_limit}注。\n\n")
             display_bets = filtered_bets[:display_limit]
        else:
            display_bets = filtered_bets

        self.result_text.insert(tk.END, "\n".join(display_bets))
        self.result_text.config(state='disabled')
        self.reset_ui_state()
        
    def clear_all(self):
        for i in range(14):
            for j in range(3):
                self.match_vars[i][j].set(0)
                self.odds_entries[i][j].set("")
        for widget in self.filters.values():
            if widget: widget.delete(0, tk.END)
        self.result_text.config(state='normal')
        self.result_text.delete('1.0', tk.END)
        self.result_text.config(state='disabled')
        self.status_label.config(text="已清空所有选项。")
        self.progress_bar['value'] = 0

    def reset_ui_state(self):
        self.start_button.config(state='normal')
        self.clear_button.config(state='normal')


if __name__ == "__main__":
    app = LotteryFilterAppPro()

    # Add a modern theme if available (e.g., 'clam', 'alt', 'default', 'classic')
    # This improves the look and feel on Windows and Linux
    try:
        style = ttk.Style()
        # available_themes = style.theme_names() # ('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative')
        style.theme_use('clam') 
        style.configure("Accent.TButton", foreground="white", background="#0078D7")
    except tk.TclError:
        print("ttk theme 'clam' not found, using default.")

    app.mainloop()
