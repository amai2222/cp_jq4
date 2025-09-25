"""
4场进球玩法专用过滤器
专注于胜平负和大小球的过滤逻辑
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re

class JQC4GameFilter:
    def __init__(self, root):
        self.root = root
        self.root.title("4场进球玩法过滤器")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # 数据存储
        self.original_data = []  # 原始投注数据
        self.betting_data = []   # 投注区数据
        self.filtered_data = []  # 过滤后数据
        
        self._create_widgets()
        self._setup_styles()
    
    def _setup_styles(self):
        """设置界面样式"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 配置样式
        self.style.configure('Title.TLabel', font=('Microsoft YaHei UI', 14, 'bold'))
        self.style.configure('Header.TLabel', font=('Microsoft YaHei UI', 11, 'bold'))
        self.style.configure('Filter.TButton', font=('Microsoft YaHei UI', 10))
        self.style.configure('Clear.TButton', font=('Microsoft YaHei UI', 10))
        
        # 按钮样式
        self.style.configure('Filter.TButton', foreground='white', background='#007bff')
        self.style.configure('Clear.TButton', foreground='white', background='#6c757d')
        
        self.style.map('Filter.TButton', background=[('active', '#0056b3')])
        self.style.map('Clear.TButton', background=[('active', '#545b62')])
        
        # 高亮输入框样式
        self.style.configure('Highlight.TEntry', fieldbackground='#d4edda', foreground='#155724')
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="4场进球玩法过滤器", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # 左右分栏
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：投注数据输入区
        left_frame = ttk.LabelFrame(content_frame, text="投注数据输入", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 输入说明
        input_info = ttk.Label(left_frame, text="请粘贴4场进球投注结果，每行一个投注，格式如：10303111", 
                              font=('Microsoft YaHei UI', 9), foreground='gray')
        input_info.pack(pady=(0, 10))
        
        # 输入文本框
        self.input_text = scrolledtext.ScrolledText(left_frame, height=20, width=30, 
                                                   font=('Consolas', 10))
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 输入按钮
        input_btn_frame = ttk.Frame(left_frame)
        input_btn_frame.pack(fill=tk.X)
        
        ttk.Button(input_btn_frame, text="加载数据到投注区", command=self.load_data_to_betting_area, 
                  style='Filter.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(input_btn_frame, text="清空", command=self.clear_input, 
                  style='Clear.TButton').pack(side=tk.LEFT)
        
        # 数据统计
        self.stats_label = ttk.Label(left_frame, text="数据统计：0 条", 
                                    font=('Microsoft YaHei UI', 10))
        self.stats_label.pack(pady=(10, 0))
        
        # 投注区
        betting_frame = ttk.LabelFrame(left_frame, text="投注区", padding="10")
        betting_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 投注区文本框
        self.betting_text = scrolledtext.ScrolledText(betting_frame, height=15, width=30, 
                                                     font=('Consolas', 10))
        self.betting_text.pack(fill=tk.BOTH, expand=True)
        
        # 投注区统计标签
        self.betting_stats = ttk.Label(betting_frame, text="投注数据：0 条", 
                                      font=('Microsoft YaHei UI', 10))
        self.betting_stats.pack(pady=(5, 0))
        
        # 右侧：过滤器设置区
        right_frame = ttk.LabelFrame(content_frame, text="过滤器设置", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建过滤器界面
        self._create_filter_controls(right_frame)
    
    def _create_filter_controls(self, parent):
        """创建过滤器控制界面"""
        # 胜平负过滤区域
        wdl_frame = ttk.LabelFrame(parent, text="胜平负过滤", padding="10")
        wdl_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 4场比赛的胜平负设置
        self.wdl_vars = {}
        self.wdl_checks = {}
        
        for i in range(4):
            game_frame = ttk.Frame(wdl_frame)
            game_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(game_frame, text=f"第{i+1}场：", width=8).pack(side=tk.LEFT)
            
            # 胜平负选择
            wdl_var = tk.StringVar(value="任意")
            self.wdl_vars[i] = wdl_var
            
            wdl_combo = ttk.Combobox(game_frame, textvariable=wdl_var, 
                                   values=["任意", "胜", "平", "负"], width=8, state="readonly")
            wdl_combo.pack(side=tk.LEFT, padx=(0, 10))
            
            # 启用复选框
            check_var = tk.BooleanVar()
            self.wdl_checks[i] = check_var
            
            ttk.Checkbutton(game_frame, text="启用", variable=check_var).pack(side=tk.LEFT)
        
        # 大小球过滤区域
        ou_frame = ttk.LabelFrame(parent, text="大小球过滤", padding="10")
        ou_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 4场比赛的大小球设置
        self.ou_vars = {}
        self.ou_checks = {}
        
        for i in range(4):
            game_frame = ttk.Frame(ou_frame)
            game_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(game_frame, text=f"第{i+1}场：", width=8).pack(side=tk.LEFT)
            
            # 大小球选择
            ou_var = tk.StringVar(value="任意")
            self.ou_vars[i] = ou_var
            
            ou_combo = ttk.Combobox(game_frame, textvariable=ou_var, 
                                  values=["任意", "大球", "小球"], width=8, state="readonly")
            ou_combo.pack(side=tk.LEFT, padx=(0, 10))
            
            # 启用复选框
            check_var = tk.BooleanVar()
            self.ou_checks[i] = check_var
            
            ttk.Checkbutton(game_frame, text="启用", variable=check_var).pack(side=tk.LEFT)
        
        # 过滤按钮区域
        filter_btn_frame = ttk.Frame(parent)
        filter_btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(filter_btn_frame, text="开始过滤", command=self.apply_filter, 
                  style='Filter.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(filter_btn_frame, text="重置过滤", command=self.reset_filter, 
                  style='Clear.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(filter_btn_frame, text="比分频率缩水", command=self.show_frequency_filter, 
                  style='Filter.TButton').pack(side=tk.LEFT)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(parent, text="过滤结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))
        
        # 结果统计
        self.result_stats = ttk.Label(result_frame, text="过滤结果：0 条", 
                                     font=('Microsoft YaHei UI', 10, 'bold'))
        self.result_stats.pack(pady=(0, 10))
        
        # 结果显示
        self.result_text = scrolledtext.ScrolledText(result_frame, height=8, 
                                                    font=('Consolas', 9))
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 结果操作按钮
        result_btn_frame = ttk.Frame(result_frame)
        result_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(result_btn_frame, text="复制结果", command=self.copy_result, 
                  style='Filter.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(result_btn_frame, text="清空结果", command=self.clear_result, 
                  style='Clear.TButton').pack(side=tk.LEFT)
    
    def load_data_to_betting_area(self):
        """加载数据到投注区"""
        try:
            input_data = self.input_text.get("1.0", tk.END).strip()
            if not input_data:
                messagebox.showwarning("警告", "请输入投注数据")
                return
            
            lines = [line.strip() for line in input_data.split('\n') if line.strip()]
            valid_data = []
            
            for line in lines:
                # 验证数据格式（8位数字，代表4场比赛的主客队进球数）
                if re.match(r'^[0-3]{8}$', line):
                    valid_data.append(line)
                else:
                    messagebox.showerror("错误", f"数据格式错误：{line}\n应为8位数字，每位代表0-3球")
                    return
            
            # 保存到投注区
            self.betting_data = valid_data.copy()
            self.original_data = valid_data.copy()
            
            # 显示在投注区
            self.betting_text.delete("1.0", tk.END)
            self.betting_text.insert("1.0", "\n".join(valid_data))
            
            # 更新统计
            self.stats_label.config(text=f"数据统计：{len(valid_data)} 条")
            self.betting_stats.config(text=f"投注数据：{len(valid_data)} 条")
            
            messagebox.showinfo("成功", f"成功加载 {len(valid_data)} 条投注数据到投注区")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败：{e}")
    
    def clear_input(self):
        """清空输入"""
        self.input_text.delete("1.0", tk.END)
        self.original_data = []
    
    def clear_betting_area(self):
        """清空投注区"""
        self.betting_text.delete("1.0", tk.END)
        self.betting_data = []
        self.betting_stats.config(text="投注数据：0 条")
        self.stats_label.config(text="数据统计：0 条")
    
    def apply_filter(self):
        """应用过滤器"""
        if not self.original_data:
            messagebox.showwarning("警告", "请先加载投注数据")
            return
        
        try:
            self.filtered_data = []
            
            for bet in self.original_data:
                if self._check_bet(bet):
                    self.filtered_data.append(bet)
            
            # 显示结果
            self._display_results()
            
        except Exception as e:
            messagebox.showerror("错误", f"过滤失败：{e}")
    
    def _check_bet(self, bet):
        """检查单个投注是否满足过滤条件"""
        # 解析投注数据（8位数字，每2位代表一场比赛的主客队进球数）
        games = []
        for i in range(0, 8, 2):
            home_goals = int(bet[i])
            away_goals = int(bet[i+1])
            games.append((home_goals, away_goals))
        
        # 检查胜平负过滤
        for i in range(4):
            if self.wdl_checks[i].get():  # 如果启用了该场的过滤
                wdl_condition = self.wdl_vars[i].get()
                if wdl_condition != "任意":
                    home_goals, away_goals = games[i]
                    result = self._get_wdl_result(home_goals, away_goals)
                    if result != wdl_condition:
                        return False
        
        # 检查大小球过滤
        for i in range(4):
            if self.ou_checks[i].get():  # 如果启用了该场的过滤
                ou_condition = self.ou_vars[i].get()
                if ou_condition != "任意":
                    home_goals, away_goals = games[i]
                    total_goals = home_goals + away_goals
                    ou_result = "大球" if total_goals >= 3 else "小球"
                    if ou_result != ou_condition:
                        return False
        
        return True
    
    def _get_wdl_result(self, home_goals, away_goals):
        """获取胜平负结果"""
        if home_goals > away_goals:
            return "胜"
        elif home_goals == away_goals:
            return "平"
        else:
            return "负"
    
    def _display_results(self):
        """显示过滤结果"""
        self.result_text.delete("1.0", tk.END)
        
        if self.filtered_data:
            for bet in self.filtered_data:
                self.result_text.insert(tk.END, bet + "\n")
        
        self.result_stats.config(text=f"过滤结果：{len(self.filtered_data)} 条")
    
    def reset_filter(self):
        """重置过滤器"""
        # 重置所有选择
        for i in range(4):
            self.wdl_vars[i].set("任意")
            self.wdl_checks[i].set(False)
            self.ou_vars[i].set("任意")
            self.ou_checks[i].set(False)
        
        # 清空结果
        self.clear_result()
    
    def copy_result(self):
        """复制结果到剪贴板"""
        if self.filtered_data:
            result_text = "\n".join(self.filtered_data)
            self.root.clipboard_clear()
            self.root.clipboard_append(result_text)
            messagebox.showinfo("成功", f"已复制 {len(self.filtered_data)} 条结果到剪贴板")
        else:
            messagebox.showwarning("警告", "没有结果可复制")
    
    def clear_result(self):
        """清空结果"""
        self.result_text.delete("1.0", tk.END)
        self.filtered_data = []
        self.result_stats.config(text="过滤结果：0 条")
    
    def show_frequency_filter(self):
        """显示比分频率缩水窗口"""
        # 检查投注区是否有数据
        if not self.betting_data:
            messagebox.showwarning("警告", "请先加载数据到投注区")
            return
        
        # 创建频率缩水窗口
        freq_window = tk.Toplevel(self.root)
        freq_window.title("比分频率缩水")
        freq_window.geometry("1000x800")
        freq_window.resizable(True, True)
        
        # 居中显示
        freq_window.update_idletasks()
        x = (freq_window.winfo_screenwidth() // 2) - (1000 // 2)
        y = (freq_window.winfo_screenheight() // 2) - (800 // 2)
        freq_window.geometry(f'1000x800+{x}+{y}')
        
        # 主框架
        main_frame = ttk.Frame(freq_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="比分频率缩水", 
                               font=('Microsoft YaHei UI', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 标题说明
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(title_frame, text="4场比赛胜平负频率调整", 
                 font=('Microsoft YaHei UI', 12, 'bold')).pack()
        
        # 频率汇总显示区域
        summary_frame = ttk.LabelFrame(main_frame, text="频率汇总", padding="10")
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建汇总显示标签
        summary_text = tk.StringVar()
        summary_label = ttk.Label(summary_frame, textvariable=summary_text, 
                                 font=('Microsoft YaHei UI', 11, 'bold'),
                                 foreground='#007bff')
        summary_label.pack()
        
        # 频率调整区域
        freq_frame = ttk.LabelFrame(main_frame, text="频率调整", padding="15")
        freq_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 创建频率变量存储
        freq_vars = {}
        
        # 创建4场比赛的胜平负频率调整区域
        games_frame = ttk.Frame(freq_frame)
        games_frame.pack(fill=tk.BOTH, expand=True)
        
        # 4场比赛，每场3个区域（胜、平、负）
        for game_idx in range(4):
            game_frame = ttk.LabelFrame(games_frame, text=f"第{game_idx + 1}场", padding="10")
            game_frame.grid(row=0, column=game_idx, padx=5, pady=5, sticky="nsew")
            
            # 胜平负三个区域
            for result_idx, result_name in enumerate(["胜区", "平区", "负区"]):
                result_frame = ttk.LabelFrame(game_frame, text=result_name, padding="5")
                result_frame.grid(row=result_idx, column=0, padx=2, pady=2, sticky="ew")
                
                # 创建该结果的频率调整控件
                result_key = f"game_{game_idx}_{result_idx}"  # game_0_0, game_0_1, game_0_2 等
                
                # 频率调整控件
                control_frame = ttk.Frame(result_frame)
                control_frame.pack(fill=tk.X)
                
                # 减少按钮
                ttk.Button(control_frame, text="◀", width=2, 
                          command=lambda k=result_key: self._adjust_frequency(freq_vars[k], -0.1, summary_text)).pack(side=tk.LEFT, padx=(0, 3))
                
                # 频率输入框
                freq_var = tk.StringVar(value="0.0")
                freq_vars[result_key] = freq_var
                freq_entry = ttk.Entry(control_frame, textvariable=freq_var, width=6, justify=tk.CENTER,
                                      font=('Microsoft YaHei UI', 10))
                freq_entry.pack(side=tk.LEFT, padx=(0, 3))
                
                # 保存输入框引用
                freq_vars[f"{result_key}_entry"] = freq_entry
                
                # 绑定输入框变化事件
                freq_var.trace('w', lambda *args, k=result_key: self._update_frequency_summary(freq_vars, summary_text))
                
                ttk.Label(control_frame, text="%", width=1, 
                         font=('Microsoft YaHei UI', 10)).pack(side=tk.LEFT)
                
                # 增加按钮
                ttk.Button(control_frame, text="▶", width=2, 
                          command=lambda k=result_key: self._adjust_frequency(freq_vars[k], 0.1, summary_text)).pack(side=tk.LEFT, padx=(3, 0))
        
        # 配置列权重
        for i in range(4):
            games_frame.columnconfigure(i, weight=1)
        
        # 初始化频率显示
        self._update_frequency_display_new(freq_vars, self.betting_data, summary_text)
        
        # 操作按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="频率统计", command=lambda: self._show_frequency_stats_new(freq_vars, freq_window), 
                  style='Filter.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="应用缩水", command=lambda: self._apply_frequency_filter_new(freq_vars, freq_window), 
                  style='Filter.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="关闭", command=freq_window.destroy, 
                  style='Clear.TButton').pack(side=tk.RIGHT)
    
    def _update_frequency_display_new(self, freq_vars, valid_data, summary_text):
        """更新频率显示（新版本：胜平负分区）"""
        try:
            total_count = len(valid_data)
            
            # 统计每场比赛的胜平负频率
            game_stats = {}
            for game_idx in range(4):
                game_stats[game_idx] = {'win': 0, 'draw': 0, 'lose': 0}
            
            for bet in valid_data:
                for game_idx in range(4):
                    # 解析该场的主客队进球数
                    home_goals = int(bet[game_idx * 2])
                    away_goals = int(bet[game_idx * 2 + 1])
                    
                    # 判断胜平负
                    if home_goals > away_goals:
                        game_stats[game_idx]['win'] += 1
                    elif home_goals == away_goals:
                        game_stats[game_idx]['draw'] += 1
                    else:
                        game_stats[game_idx]['lose'] += 1
            
            # 更新界面显示
            for game_idx in range(4):
                for result_idx, result_key in enumerate(['win', 'draw', 'lose']):
                    var_key = f"game_{game_idx}_{result_idx}"
                    if var_key in freq_vars:
                        count = game_stats[game_idx][result_key]
                        percentage = (count / total_count) * 100
                        freq_vars[var_key].set(f"{percentage:.1f}")
            
            # 高亮显示有数据的频率
            self._highlight_frequency_entries_new(freq_vars, game_stats)
            
            # 更新频率汇总显示
            self._update_frequency_summary(freq_vars, summary_text)
                    
        except Exception as e:
            print(f"更新频率显示失败：{e}")
    
    def _update_frequency_display(self, freq_vars, game_name, valid_data, summary_text):
        """更新频率显示（旧版本：比分显示）"""
        try:
            # 获取场次索引
            game_index = int(game_name[1]) - 1
            
            # 统计当前场次的比分频率
            score_stats = {}
            total_count = len(valid_data)
            
            for bet in valid_data:
                # 解析该场的主客队进球数
                home_goals = int(bet[game_index * 2])
                away_goals = int(bet[game_index * 2 + 1])
                
                # 构造比分字符串
                score = f"{home_goals}:{away_goals}"
                
                # 统计比分频率
                if score in score_stats:
                    score_stats[score] += 1
                else:
                    score_stats[score] = 1
            
            # 更新界面显示
            for score, var in freq_vars.items():
                # 跳过Entry对象，只处理StringVar对象
                if score.endswith('_entry'):
                    continue
                if score in score_stats:
                    count = score_stats[score]
                    percentage = (count / total_count) * 100
                    var.set(f"{percentage:.1f}")
                else:
                    var.set("0.0")
            
            # 高亮显示有数据的频率
            self._highlight_frequency_entries(freq_vars, score_stats)
            
            # 更新频率汇总显示
            self._update_frequency_summary(freq_vars, summary_text)
                    
        except Exception as e:
            print(f"更新频率显示失败：{e}")
    
    def _highlight_frequency_entries(self, freq_vars, score_stats):
        """高亮显示有数据的频率条目"""
        try:
            # 遍历所有比分，高亮显示有数据的条目
            for score in score_stats.keys():
                entry_key = f"{score}_entry"
                if entry_key in freq_vars:
                    entry_widget = freq_vars[entry_key]
                    if score_stats[score] > 0:
                        # 有数据：使用绿色背景
                        entry_widget.configure(style='Highlight.TEntry')
                    else:
                        # 无数据：使用默认样式
                        entry_widget.configure(style='TEntry')
            
            # 重置所有无数据的条目
            for score in freq_vars.keys():
                if score.endswith('_entry'):
                    continue
                if score not in score_stats or score_stats[score] == 0:
                    entry_key = f"{score}_entry"
                    if entry_key in freq_vars:
                        freq_vars[entry_key].configure(style='TEntry')
        except Exception as e:
            print(f"高亮显示失败：{e}")
    
    def _highlight_frequency_entries_new(self, freq_vars, game_stats):
        """高亮显示有数据的频率条目（新版本：胜平负分区）"""
        try:
            # 遍历所有比赛和结果，高亮显示有数据的条目
            for game_idx in range(4):
                for result_idx, result_key in enumerate(['win', 'draw', 'lose']):
                    var_key = f"game_{game_idx}_{result_idx}"
                    entry_key = f"{var_key}_entry"
                    
                    if entry_key in freq_vars:
                        entry_widget = freq_vars[entry_key]
                        if game_stats[game_idx][result_key] > 0:
                            # 有数据：使用绿色背景
                            entry_widget.configure(style='Highlight.TEntry')
                        else:
                            # 无数据：使用默认样式
                            entry_widget.configure(style='TEntry')
        except Exception as e:
            print(f"高亮显示失败：{e}")
    
    def _update_frequency_summary(self, freq_vars, summary_text):
        """更新频率汇总显示"""
        try:
            total_freq = 0.0
            used_freq = 0.0
            count = 0
            
            for score, var in freq_vars.items():
                if score.endswith('_entry'):
                    continue
                try:
                    freq = float(var.get())
                    total_freq += freq
                    if freq > 0:
                        used_freq += freq
                        count += 1
                except ValueError:
                    pass
            
            remaining_freq = 100.0 - total_freq
            
            # 更新汇总显示
            summary_info = f"总频率: {total_freq:.1f}% | 已使用: {used_freq:.1f}% | 剩余可调: {remaining_freq:.1f}% | 有数据比分: {count}个"
            summary_text.set(summary_info)
            
        except Exception as e:
            print(f"更新频率汇总失败：{e}")
    
    def _adjust_frequency(self, var, delta, summary_text=None):
        """调整频率值"""
        try:
            current = float(var.get())
            new_value = max(0.0, min(100.0, current + delta))
            var.set(f"{new_value:.1f}")
        except ValueError:
            var.set("0.0")
    
    def _show_frequency_stats(self, game_name, parent_window):
        """显示频率统计"""
        try:
            # 优先使用过滤后的数据，如果没有则使用投注区数据
            if self.filtered_data:
                data_to_analyze = self.filtered_data
                data_source = "过滤后的数据"
            else:
                # 使用投注区数据
                if not self.betting_data:
                    messagebox.showwarning("警告", "投注区没有数据", parent=parent_window)
                    return
                
                data_to_analyze = self.betting_data
                data_source = "投注区数据"
            
            # 获取场次索引
            game_index = int(game_name[1]) - 1
            
            # 统计比分频率
            score_stats = {}
            total_count = len(data_to_analyze)
            
            for bet in data_to_analyze:
                # 解析该场的主客队进球数
                home_goals = int(bet[game_index * 2])
                away_goals = int(bet[game_index * 2 + 1])
                
                # 构造比分字符串
                score = f"{home_goals}:{away_goals}"
                
                # 统计比分频率
                if score in score_stats:
                    score_stats[score] += 1
                else:
                    score_stats[score] = 1
            
            # 按频率排序
            sorted_scores = sorted(score_stats.items(), key=lambda x: x[1], reverse=True)
            
            # 显示统计结果
            stats_text = f"{game_name} 比分频率统计（基于{data_source}）：\n\n"
            stats_text += f"数据条数：{total_count} 条\n\n"
            
            # 显示比分统计
            stats_text += "比分分布：\n"
            for score, count in sorted_scores:
                percentage = (count / total_count) * 100
                stats_text += f"  {score}：{count}次 ({percentage:.1f}%)\n"
            
            messagebox.showinfo("频率统计", stats_text, parent=parent_window)
            
        except Exception as e:
            messagebox.showerror("错误", f"统计失败：{e}", parent=parent_window)
    
    def _apply_frequency_filter(self, game_name, freq_vars, parent_window):
        """应用频率过滤"""
        try:
            # 使用投注区数据
            if not self.betting_data:
                messagebox.showwarning("警告", "投注区没有数据", parent=parent_window)
                return
            
            valid_data = self.betting_data.copy()
            
            # 获取场次索引
            game_index = int(game_name[1]) - 1
            
            # 获取频率设置
            freq_settings = {}
            for score, var in freq_vars.items():
                try:
                    freq_settings[score] = float(var.get())
                except ValueError:
                    freq_settings[score] = 0.0
            
            # 应用比分频率过滤
            filtered_data = []
            for bet in valid_data:
                home_goals = int(bet[game_index * 2])
                away_goals = int(bet[game_index * 2 + 1])
                
                # 构造比分字符串
                score = f"{home_goals}:{away_goals}"
                
                # 检查该比分的频率设置
                if score in freq_settings:
                    score_freq = freq_settings[score]
                    # 如果频率设置为0，则过滤掉该结果
                    if score_freq == 0:
                        continue
                
                filtered_data.append(bet)
            
            # 更新结果
            self.filtered_data = filtered_data
            self._display_results()
            
            # 更新数据统计
            self.stats_label.config(text=f"数据统计：{len(valid_data)} 条")
            
            # 显示完成提示
            messagebox.showinfo("完成", f"频率缩水完成！从 {len(valid_data)} 条数据中筛选出 {len(filtered_data)} 条结果", parent=parent_window)
            
            # 关闭窗口
            parent_window.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"频率过滤失败：{e}", parent=parent_window)
    
    def _show_frequency_stats_new(self, freq_vars, parent_window):
        """显示频率统计（新版本：胜平负分区）"""
        try:
            # 使用投注区数据
            if not self.betting_data:
                messagebox.showwarning("警告", "投注区没有数据", parent=parent_window)
                return
            
            data_to_analyze = self.betting_data
            total_count = len(data_to_analyze)
            
            # 统计每场比赛的胜平负频率
            game_stats = {}
            for game_idx in range(4):
                game_stats[game_idx] = {'win': 0, 'draw': 0, 'lose': 0}
            
            for bet in data_to_analyze:
                for game_idx in range(4):
                    # 解析该场的主客队进球数
                    home_goals = int(bet[game_idx * 2])
                    away_goals = int(bet[game_idx * 2 + 1])
                    
                    # 判断胜平负
                    if home_goals > away_goals:
                        game_stats[game_idx]['win'] += 1
                    elif home_goals == away_goals:
                        game_stats[game_idx]['draw'] += 1
                    else:
                        game_stats[game_idx]['lose'] += 1
            
            # 显示统计结果
            stats_text = f"4场比赛胜平负频率统计（基于投注区数据）：\n\n"
            stats_text += f"数据条数：{total_count} 条\n\n"
            
            for game_idx in range(4):
                stats_text += f"第{game_idx + 1}场：\n"
                win_pct = (game_stats[game_idx]['win'] / total_count) * 100
                draw_pct = (game_stats[game_idx]['draw'] / total_count) * 100
                lose_pct = (game_stats[game_idx]['lose'] / total_count) * 100
                
                stats_text += f"  胜：{game_stats[game_idx]['win']}次 ({win_pct:.1f}%)\n"
                stats_text += f"  平：{game_stats[game_idx]['draw']}次 ({draw_pct:.1f}%)\n"
                stats_text += f"  负：{game_stats[game_idx]['lose']}次 ({lose_pct:.1f}%)\n\n"
            
            messagebox.showinfo("频率统计", stats_text, parent=parent_window)
            
        except Exception as e:
            messagebox.showerror("错误", f"统计失败：{e}", parent=parent_window)
    
    def _apply_frequency_filter_new(self, freq_vars, parent_window):
        """应用频率过滤（新版本：胜平负分区）"""
        try:
            # 使用投注区数据
            if not self.betting_data:
                messagebox.showwarning("警告", "投注区没有数据", parent=parent_window)
                return
            
            valid_data = self.betting_data.copy()
            
            # 获取频率设置
            freq_settings = {}
            for game_idx in range(4):
                for result_idx in range(3):
                    var_key = f"game_{game_idx}_{result_idx}"
                    if var_key in freq_vars:
                        try:
                            freq_settings[var_key] = float(freq_vars[var_key].get())
                        except ValueError:
                            freq_settings[var_key] = 0.0
            
            # 应用胜平负频率过滤
            filtered_data = []
            for bet in valid_data:
                should_include = True
                
                for game_idx in range(4):
                    # 解析该场的主客队进球数
                    home_goals = int(bet[game_idx * 2])
                    away_goals = int(bet[game_idx * 2 + 1])
                    
                    # 判断胜平负
                    if home_goals > away_goals:
                        result_idx = 0  # 胜
                    elif home_goals == away_goals:
                        result_idx = 1  # 平
                    else:
                        result_idx = 2  # 负
                    
                    var_key = f"game_{game_idx}_{result_idx}"
                    if var_key in freq_settings:
                        if freq_settings[var_key] == 0:
                            should_include = False
                            break
                
                if should_include:
                    filtered_data.append(bet)
            
            # 更新结果
            self.filtered_data = filtered_data
            self._display_results()
            
            # 更新数据统计
            self.result_stats.config(text=f"过滤结果：{len(filtered_data)} 条")
            
            # 显示完成提示
            messagebox.showinfo("完成", f"频率缩水完成！从 {len(valid_data)} 条数据中筛选出 {len(filtered_data)} 条结果", parent=parent_window)
            
            # 关闭窗口
            parent_window.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"频率过滤失败：{e}", parent=parent_window)

def main():
    root = tk.Tk()
    app = JQC4GameFilter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
