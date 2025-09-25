import tkinter as tk
from tkinter import messagebox, ttk
import itertools
import math

# ##################################################################
# 核心逻辑引擎 (Model) - 无需修改，它已经很完美
# ##################################################################
class BettingEngine:
    # ... (这部分代码与上一版完全相同，因为它只负责逻辑，不关心显示)
    # ... 为了简洁，我将它折叠起来，但在下面的完整代码块中是完整的。
    def __init__(self, selections, bankers):
        if len(selections) != 14: raise ValueError("必须提供14场比赛的选择")
        self.selections = selections
        self.bankers = bankers
        self._original_bets = self._generate_full_set()
        self.current_bets = list(self._original_bets)
        self.history = ["原始复式"]
        self.n = len([s for s in self.selections if s])

    def _generate_full_set(self):
        print("正在生成原始复式方案...")
        banker_options = [self.selections[i] for i in self.bankers]
        regular_options = [s for i, s in enumerate(self.selections) if s and i not in self.bankers]
        banker_combos = list(itertools.product(*banker_options))
        regular_combos = list(itertools.product(*regular_options))
        full_bets = []
        if not banker_combos: return [tuple(list(c)) for c in regular_combos] # 修复无胆码时的元组问题
        for banker_combo in banker_combos:
            for regular_combo in regular_combos:
                full_bet = [''] * 14
                for i, banker_index in enumerate(self.bankers):
                    full_bet[banker_index] = banker_combo[i]
                reg_idx = 0
                for i in range(14):
                    if self.selections[i] and i not in self.bankers:
                        full_bet[i] = regular_combo[reg_idx]
                        reg_idx += 1
                final_bet = tuple([choice for choice in full_bet if choice])
                full_bets.append(final_bet)
        print(f"原始方案生成完毕，共 {len(full_bets)} 注。")
        return full_bets
    
    def get_state(self):
        return {"count": len(self.current_bets), "history": " -> ".join(self.history)}

    def reset(self, selections, bankers):
        self.__init__(selections, bankers)
        print("引擎已重置并使用新选择重新初始化。")

    def apply_filter(self, conditions):
        print(f"开始过滤，当前注数: {len(self.current_bets)}")
        active_conditions = {k: v for k, v in conditions.items() if v['active']}
        if not active_conditions:
            messagebox.showinfo("提示", "没有选择任何过滤条件。")
            return
        filtered_bets = []
        for bet in self.current_bets:
            wins = bet.count('3')
            draws = bet.count('1')
            losses = bet.count('0')
            is_match = True
            for key, cond in active_conditions.items():
                val = 0
                if key == 'wins': val = wins
                elif key == 'draws': val = draws
                elif key == 'losses': val = losses
                if not (cond['min'] <= val <= cond['max']):
                    is_match = False
                    break
            if is_match: filtered_bets.append(bet)
        self.current_bets = filtered_bets
        self.history.append("过滤")
        print(f"过滤完成，剩余注数: {len(self.current_bets)}")

    def apply_wheel(self, n, k):
        print(f"开始旋转缩水 (中{n}保{k})，当前注数: {len(self.current_bets)}")
        if "过滤" in self.history and k < n:
            messagebox.showwarning("逻辑警告", f"您正在对过滤后的方案进行保{k}缩水，这可能无法实现数学覆盖。\n\n建议先旋转，再过滤。")
        if k == n:
            self.history.append(f"旋转(中{n}保{n})")
            return
        if k == n - 1:
            value_map = {'3': 0, '1': 1, '0': 2}
            groups = {0: [], 1: [], 2: []}
            for bet in self.current_bets:
                s = sum(value_map[choice] for choice in bet)
                groups[s % 3].append(bet)
            min_group_key = min(groups, key=lambda k: len(groups[k]))
            self.current_bets = groups[min_group_key]
            self.history.append(f"旋转(中{n}保{k})")
            print(f"旋转完成，剩余注数: {len(self.current_bets)}")
        else:
            messagebox.showinfo("提示", f"“中{n}保{k}”是一个复杂的组合数学问题，暂不支持。请使用“中N保N-1”。")

# ##################################################################
# 图形用户界面 (View & Controller) - 带分页和精确复制功能
# ##################################################################
class ProfessionalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("足彩任九专业缩水工具 V14.0 (最终交付版)")
        self.root.geometry("850x650") 
        self.engine = None

        # --- 分页状态 ---
        self.items_per_page = 1000
        self.current_page = 1
        self.total_pages = 0

        # --- 主框架 ---
        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X)
        self._create_match_panel(top_frame)
        self._create_filter_panel(top_frame)

        self.status_var = tk.StringVar(value="欢迎使用。请选择场次，然后点击 [① 投注]。")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X, pady=5)

        # --- 结果显示区 (包含分页) ---
        result_frame = ttk.Frame(main_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.result_text = tk.Text(result_frame, wrap=tk.NONE, height=10, width=80) # wrap=NONE 保证格式整齐
        ysb = ttk.Scrollbar(result_frame, command=self.result_text.yview)
        xsb = ttk.Scrollbar(result_frame, command=self.result_text.xview, orient=tk.HORIZONTAL)
        self.result_text.config(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.result_text.grid(row=0, column=0, sticky='nsew')
        ysb.grid(row=0, column=1, sticky='ns')
        xsb.grid(row=1, column=0, sticky='ew')
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        
        # --- 分页控制栏 ---
        self.pagination_frame = ttk.Frame(main_frame)
        self.pagination_frame.pack(fill=tk.X)
        self.btn_first = ttk.Button(self.pagination_frame, text="首页", command=self.go_to_first, state=tk.DISABLED)
        self.btn_prev = ttk.Button(self.pagination_frame, text="上一页", command=self.go_to_prev, state=tk.DISABLED)
        self.page_status_var = tk.StringVar(value="Page 0 of 0")
        self.lbl_page_status = ttk.Label(self.pagination_frame, textvariable=self.page_status_var)
        self.btn_next = ttk.Button(self.pagination_frame, text="下一页", command=self.go_to_next, state=tk.DISABLED)
        self.btn_last = ttk.Button(self.pagination_frame, text="末页", command=self.go_to_last, state=tk.DISABLED)
        
        self.btn_first.pack(side=tk.LEFT, padx=2)
        self.btn_prev.pack(side=tk.LEFT, padx=2)
        self.lbl_page_status.pack(side=tk.LEFT, padx=10)
        self.btn_next.pack(side=tk.LEFT, padx=2)
        self.btn_last.pack(side=tk.LEFT, padx=2)

        # --- 底部按钮 ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=5)
        ttk.Button(bottom_frame, text="复制结果到剪贴板", command=self.copy_to_clipboard).pack(side=tk.RIGHT)

    # --- 界面创建方法 (_create_match_panel, _create_filter_panel) 与之前相同 ---
    def _create_match_panel(self, parent):
        panel = ttk.LabelFrame(parent, text="① 选择场次与赛果", padding=10)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        headers = ["场", "3", "1", "0", "胆"]
        for col, text in enumerate(headers):
            ttk.Label(panel, text=text, font=('Helvetica', 9, 'bold')).grid(row=0, column=col, padx=5)
        self.match_vars = []
        for i in range(14):
            ttk.Label(panel, text=f"{i+1:02d}").grid(row=i+1, column=0, sticky="w")
            row_vars = {'3': tk.BooleanVar(value=True), '1': tk.BooleanVar(value=True), '0': tk.BooleanVar(value=True), 'banker': tk.BooleanVar()}
            ttk.Checkbutton(panel, variable=row_vars['3']).grid(row=i+1, column=1)
            ttk.Checkbutton(panel, variable=row_vars['1']).grid(row=i+1, column=2)
            ttk.Checkbutton(panel, variable=row_vars['0']).grid(row=i+1, column=3)
            ttk.Checkbutton(panel, variable=row_vars['banker']).grid(row=i+1, column=4)
            self.match_vars.append(row_vars)

    def _create_filter_panel(self, parent):
        panel = ttk.LabelFrame(parent, text="常用过滤", padding=10)
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        filter_area = ttk.Frame(panel)
        filter_area.pack(fill=tk.X)
        headers = ["选择", "过滤条件", "范围"]
        for col, text in enumerate(headers):
            ttk.Label(filter_area, text=text, font=('Helvetica', 9, 'bold')).grid(row=0, column=col*3, columnspan=3, pady=5)
        filter_definitions = [("胜场数", "wins"), ("平场数", "draws"), ("负场数", "losses"), ("积分和", "points"), ("断点数", "breaks"), ("连号个数", "streaks")]
        self.filter_controls = {}
        for i, (label, key) in enumerate(filter_definitions):
            controls = {'active': tk.BooleanVar(), 'min': tk.StringVar(value='0'), 'max': tk.StringVar(value='14')}
            ttk.Checkbutton(filter_area, variable=controls['active']).grid(row=i+1, column=0, padx=2)
            ttk.Label(filter_area, text=label).grid(row=i+1, column=1, sticky='w', padx=5)
            ttk.Spinbox(filter_area, from_=0, to=14, textvariable=controls['min'], width=5).grid(row=i+1, column=2)
            ttk.Label(filter_area, text="≤...≤").grid(row=i+1, column=3)
            ttk.Spinbox(filter_area, from_=0, to=14, textvariable=controls['max'], width=5).grid(row=i+1, column=4)
            self.filter_controls[key] = controls
        action_frame = ttk.Frame(panel)
        action_frame.pack(fill=tk.X, pady=20)
        # **核心修改：按钮文字**
        ttk.Button(action_frame, text="① 投注", command=self.on_bet).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="② 开始过滤", command=self.on_filter).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="③ 旋转矩阵缩水", command=self.on_wheel).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="清空所有", command=self.on_reset).pack(side=tk.LEFT, padx=3)

    # --- 核心功能方法 ---
    def on_bet(self): # 原 on_calculate
        selections, bankers, num_selected = [], [], 0
        for i, row_vars in enumerate(self.match_vars):
            sel = "".join(opt for opt, var in row_vars.items() if opt.isdigit() and var.get())
            if sel: num_selected += 1
            selections.append(sel)
            if row_vars['banker'].get():
                if not sel: messagebox.showerror("错误", f"场次 {i+1} 设为胆，但未选择赛果！"); return
                bankers.append(i)
        if num_selected < 9: messagebox.showerror("错误", f"您只选了 {num_selected} 场，请至少选择9场。"); return
        
        try:
            self.status_var.set("正在计算，请稍候..."); self.root.update()
            self.engine = BettingEngine(selections, bankers)
            self.update_display("计算完成！")
        except Exception as e:
            messagebox.showerror("计算错误", str(e)); self.status_var.set("计算出错，请检查选择。")
    
    def on_filter(self):
        if not self.engine: messagebox.showerror("错误", "请先点击 [① 投注] 初始化。"); return
        conditions = {}
        try:
            for key, controls in self.filter_controls.items():
                conditions[key] = {'active': controls['active'].get(),'min': int(controls['min'].get()),'max': int(controls['max'].get())}
            self.engine.apply_filter(conditions)
            self.update_display("过滤操作完成。")
        except ValueError: messagebox.showerror("输入错误", "过滤范围必须是整数。")
    
    def on_wheel(self):
        if not self.engine: messagebox.showerror("错误", "请先点击 [① 投注] 初始化。"); return
        if self.engine.n < 9: messagebox.showinfo("提示", f"当前方案只有 {self.engine.n} 场，无法旋转。"); return
        n, k = self.engine.n, self.engine.n - 1
        if messagebox.askyesno("确认旋转", f"当前方案共 {n} 场，将进行“中{n}保{k}”旋转，是否继续？"):
            self.engine.apply_wheel(n, k)
            self.update_display("旋转缩水完成。")

    def on_reset(self):
        self.engine = None
        for row_vars in self.match_vars: [var.set(val) for var, val in zip(row_vars.values(), [True,True,True,False])]
        self.result_text.delete(1.0, tk.END)
        self.status_var.set("已清空。请重新选择并计算。")
        self.update_pagination_controls() # 禁用分页按钮

    # --- 结果显示与分页的核心逻辑 ---
    def update_display(self, message):
        if not self.engine: return
        state = self.engine.get_state()
        self.status_var.set(f"{message} 当前注数: {state['count']:,} | 操作路径: {state['history']}")
        
        # 重置分页
        total_items = state['count']
        self.total_pages = math.ceil(total_items / self.items_per_page) if total_items > 0 else 0
        self.current_page = 1 if self.total_pages > 0 else 0
        
        self.display_current_page()
        self.update_pagination_controls()

    def display_current_page(self):
        self.result_text.delete(1.0, tk.END)
        if not self.engine or self.current_page == 0:
            self.page_status_var.set("Page 0 of 0")
            return

        start_index = (self.current_page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        
        bets_to_display = self.engine.current_bets[start_index:end_index]
        
        # 格式化输出，带行号
        max_line_num_width = len(str(min(len(self.engine.current_bets),end_index)))
        display_lines = []
        for i, bet in enumerate(bets_to_display):
            line_num = start_index + i + 1
            line = f"{line_num:<{max_line_num_width+1}} {'  '.join(map(str, bet))}"
            display_lines.append(line)
            
        self.result_text.insert(tk.END, "\n".join(display_lines))
        self.page_status_var.set(f"Page {self.current_page} of {self.total_pages}")
        
    def update_pagination_controls(self):
        if self.total_pages <= 1:
            for btn in [self.btn_first, self.btn_prev, self.btn_next, self.btn_last]:
                btn.config(state=tk.DISABLED)
        else:
            self.btn_first.config(state=(tk.NORMAL if self.current_page > 1 else tk.DISABLED))
            self.btn_prev.config(state=(tk.NORMAL if self.current_page > 1 else tk.DISABLED))
            self.btn_next.config(state=(tk.NORMAL if self.current_page < self.total_pages else tk.DISABLED))
            self.btn_last.config(state=(tk.NORMAL if self.current_page < self.total_pages else tk.DISABLED))

    def go_to_first(self): self.go_to_page(1)
    def go_to_prev(self): self.go_to_page(self.current_page - 1)
    def go_to_next(self): self.go_to_page(self.current_page + 1)
    def go_to_last(self): self.go_to_page(self.total_pages)
    def go_to_page(self, page_num):
        if 1 <= page_num <= self.total_pages:
            self.current_page = page_num
            self.display_current_page()
            self.update_pagination_controls()

    # --- 复制功能 ---
    def copy_to_clipboard(self):
        if not self.engine or not self.engine.current_bets:
            self.status_var.set("没有结果可以复制。")
            return
        
        self.status_var.set("正在准备复制，请稍候...")
        self.root.update()
        
        # **核心修改：复制全部结果**
        all_bets = self.engine.current_bets
        results_string = "\n".join([" ".join(map(str, bet)) for bet in all_bets])
        
        self.root.clipboard_clear()
        self.root.clipboard_append(results_string)
        self.status_var.set(f"成功复制 {len(all_bets):,} 注结果到剪贴板！")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProfessionalApp(root)
    root.mainloop()
