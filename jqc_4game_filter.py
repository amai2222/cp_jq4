"""
4场进球玩法专用过滤器
专注于胜平负和大小球的过滤逻辑
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re
import requests
import json
from datetime import datetime

class JQC4GameFilter:
    def __init__(self, root):
        self.root = root
        self.root.title("4场进球玩法过滤器")
        self.root.geometry("1800x900")
        self.root.resizable(True, True)
        self.root.configure(bg='#FFFFFF')
        
        # 数据存储
        self.original_data = []  # 原始投注数据
        self.betting_data = []   # 投注区数据
        self.filtered_data = []  # 过滤后数据
        self.history = []  # 操作历史记录
        
        # 期号和对阵数据
        self.current_period = ""  # 当前期号
        self.match_data = []      # 对阵数据
        self.betting_selections = {}  # 投注选择
        self.match_labels = {}    # 表格标签引用
        
        self._create_widgets()
        self._setup_styles()
        
        # 初始化时自动获取最新期号
        self.root.after(1000, self.auto_refresh_period_and_details)
    
    def _setup_styles(self):
        """设置界面样式"""
        self.style = ttk.Style()
        # 使用高对比度主题
        self.style.theme_use('clam')
        
        # 配置统一白色主题
        self.colors = {
            'primary': '#0078D4',      # 主色调 - 蓝色
            'secondary': '#6C757D',    # 次要色 - 灰色
            'success': '#28A745',      # 成功色 - 绿色
            'danger': '#DC3545',       # 危险色 - 红色
            'warning': '#FFC107',      # 警告色 - 黄色
            'light': '#FFFFFF',        # 纯白背景
            'dark': '#212529',         # 深色文字
            'border': '#DEE2E6'        # 浅灰边框
        }
        
        # 标题样式
        self.style.configure('Title.TLabel',
                           font=('Microsoft YaHei UI', 16, 'bold'))
        
        # 头部标签样式
        self.style.configure('Header.TLabel',
                           font=('Microsoft YaHei UI', 12, 'bold'))
        
        # 说明文字样式
        self.style.configure('Info.TLabel',
                           font=('Microsoft YaHei UI', 9))
        
        # 按钮样式 - 使用默认样式
        self.style.configure('Primary.TButton',
                           font=('Microsoft YaHei UI', 10))
        
        self.style.configure('Secondary.TButton',
                           font=('Microsoft YaHei UI', 10))
        
        self.style.configure('Success.TButton',
                           font=('Microsoft YaHei UI', 10))
        
        self.style.configure('Danger.TButton',
                           font=('Microsoft YaHei UI', 10))
        
        # 框架样式
        self.style.configure('Card.TFrame', 
                           background='#FFFFFF',
                           relief='solid',
                           borderwidth=1)
        
        # 标签框架样式
        self.style.configure('Card.TLabelframe', 
                           background='#FFFFFF',
                           relief='solid',
                           borderwidth=1)
        
        self.style.configure('Card.TLabelframe.Label',
                           font=('Microsoft YaHei UI', 11, 'bold'))
        
        # 输入框样式
        self.style.configure('Modern.TEntry',
                           fieldbackground='white',
                           borderwidth=1,
                           relief='solid')
        
        # 下拉框样式
        self.style.configure('Modern.TCombobox',
                           fieldbackground='white',
                           borderwidth=1,
                           relief='solid')
        
        # 高亮输入框样式
        self.style.configure('Highlight.TEntry', 
                           borderwidth=2,
                           relief='solid')
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="4场进球玩法过滤器", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # 三栏布局
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 最左侧：期号获取和对阵选择区
        data_frame = ttk.LabelFrame(content_frame, text="期号获取与投注选择", padding="10", style='Card.TLabelframe')
        data_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        data_frame.configure(width=400)
        
        # 创建期号获取和对阵选择界面
        self._create_data_acquisition_ui(data_frame)
        
        # 中间：投注数据输入区
        left_frame = ttk.LabelFrame(content_frame, text="投注数据输入", padding="10", style='Card.TLabelframe')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 输入说明
        input_info = ttk.Label(left_frame, text="请粘贴4场进球投注结果，每行一个投注，格式如：10303111", 
                              style='Info.TLabel')
        input_info.pack(pady=(0, 10))
        
        # 输入文本框
        self.input_text = scrolledtext.ScrolledText(left_frame, height=20, width=30, 
                                                   font=('Consolas', 10),
                                                   bg='white', fg='black',
                                                   relief='flat', bd=1)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 输入按钮
        input_btn_frame = ttk.Frame(left_frame)
        input_btn_frame.pack(fill=tk.X)
        
        ttk.Button(input_btn_frame, text="加载数据到投注区", command=self.load_data_to_betting_area, 
                  style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(input_btn_frame, text="清空", command=self.clear_input, 
                  style='Danger.TButton').pack(side=tk.LEFT)
        
        # 数据统计
        self.stats_label = ttk.Label(left_frame, text="数据统计：0 条", 
                                    font=('Microsoft YaHei UI', 10))
        self.stats_label.pack(pady=(10, 0))
        
        # 投注区
        betting_frame = ttk.LabelFrame(left_frame, text="投注区", padding="10", style='Card.TLabelframe')
        betting_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 投注区文本框
        self.betting_text = scrolledtext.ScrolledText(betting_frame, height=15, width=30, 
                                                     font=('Consolas', 10),
                                                     bg='white', fg='black',
                                                     relief='flat', bd=1)
        self.betting_text.pack(fill=tk.BOTH, expand=True)
        
        # 投注区统计标签
        self.betting_stats = ttk.Label(betting_frame, text="投注数据：0 条", 
                                      font=('Microsoft YaHei UI', 10))
        self.betting_stats.pack(pady=(5, 0))
        
        # 右侧：过滤器设置区
        right_frame = ttk.LabelFrame(content_frame, text="过滤器设置", padding="10", style='Card.TLabelframe')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建过滤器界面
        self._create_filter_controls(right_frame)
    
    def _create_data_acquisition_ui(self, parent):
        """创建期号获取和对阵选择界面"""
        # ①数据获取区域
        data_acq_frame = ttk.LabelFrame(parent, text="①数据获取", padding="10", style='Card.TLabelframe')
        data_acq_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 期号输入和按钮
        period_frame = ttk.Frame(data_acq_frame)
        period_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(period_frame, text="期号:", width=6).pack(side=tk.LEFT)
        self.period_var = tk.StringVar(value="")
        self.period_combo = ttk.Combobox(period_frame, textvariable=self.period_var, width=10, state="normal")
        self.period_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        # 绑定期号变化事件，自动获取详情
        self.period_var.trace('w', self.on_period_changed)
        
        ttk.Button(period_frame, text="刷新期号", command=self.refresh_period, 
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(period_frame, text="获取详情", command=self.get_match_details, 
                  style='Success.TButton').pack(side=tk.LEFT)
        
        # 详情显示区域
        self.details_text = scrolledtext.ScrolledText(data_acq_frame, height=8, width=45,
                                                    font=('Microsoft YaHei UI', 9),
                                                    bg='white', fg='black',
                                                    relief='flat', bd=1)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # ②投注选择区域
        betting_frame = ttk.LabelFrame(parent, text="②投注选择", padding="10", style='Card.TLabelframe')
        betting_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 创建对阵表格
        self._create_match_table(betting_frame)
        
        # 投注按钮
        btn_frame = ttk.Frame(betting_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="生成投注", command=self.generate_bets, 
                  style='Primary.TButton').pack(side=tk.RIGHT)
    
    def _create_match_table(self, parent):
        """创建对阵表格"""
        # 创建表格框架
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 表头
        headers = ["场次", "联赛", "开赛日期", "主队 VS 客队", "主/客", "0球", "1球", "2球", "3+球"]
        
        # 创建表头
        for i, header in enumerate(headers):
            label = ttk.Label(table_frame, text=header, font=('Microsoft YaHei UI', 9, 'bold'))
            label.grid(row=0, column=i, padx=1, pady=1, sticky="ew")
        
        # 配置列权重
        for i in range(len(headers)):
            table_frame.columnconfigure(i, weight=1)
        
        # 创建4场比赛的行
        self.match_vars = {}
        for game_idx in range(4):
            row_start = game_idx * 2 + 1
            
            # 主队行
            self._create_match_row(table_frame, game_idx, row_start, "主")
            # 客队行
            self._create_match_row(table_frame, game_idx, row_start + 1, "客")
    
    def _create_match_row(self, parent, game_idx, row, team_type):
        """创建比赛行"""
        # 场次
        if team_type == "主":
            match_num_label = ttk.Label(parent, text=f"{game_idx + 1}", font=('Microsoft YaHei UI', 9))
            match_num_label.grid(row=row, column=0, padx=1, pady=1, sticky="ew")
            # 联赛
            league_label = ttk.Label(parent, text="德甲", font=('Microsoft YaHei UI', 9))
            league_label.grid(row=row, column=1, padx=1, pady=1, sticky="ew")
            # 开赛日期
            date_label = ttk.Label(parent, text="2025-09-27", font=('Microsoft YaHei UI', 9))
            date_label.grid(row=row, column=2, padx=1, pady=1, sticky="ew")
            # 主队 VS 客队
            teams_label = ttk.Label(parent, text="拜仁 VS 不来梅", font=('Microsoft YaHei UI', 9))
            teams_label.grid(row=row, column=3, padx=1, pady=1, sticky="ew")
            
            # 保存标签引用以便后续更新
            if game_idx not in self.match_labels:
                self.match_labels[game_idx] = {}
            self.match_labels[game_idx] = {
                'match_num': match_num_label,
                'league': league_label,
                'date': date_label,
                'teams': teams_label
            }
        else:
            # 客队行，前几列留空
            for col in range(4):
                ttk.Label(parent, text="").grid(row=row, column=col, padx=1, pady=1)
        
        # 主/客
        ttk.Label(parent, text=team_type, font=('Microsoft YaHei UI', 9)).grid(
            row=row, column=4, padx=1, pady=1, sticky="ew")
        
        # 进球数选择（0球, 1球, 2球, 3+球）
        goal_vars = {}
        for goal_idx, goal_text in enumerate(["0", "1", "2", "3+"]):
            var = tk.BooleanVar()
            goal_vars[goal_text] = var
            
            cb = tk.Checkbutton(parent, text=goal_text, variable=var, 
                               font=('Microsoft YaHei UI', 8))
            cb.grid(row=row, column=5 + goal_idx, padx=1, pady=1, sticky="ew")
        
        # 保存变量引用
        if game_idx not in self.match_vars:
            self.match_vars[game_idx] = {}
        self.match_vars[game_idx][team_type] = goal_vars
    
    def _create_filter_controls(self, parent):
        """创建过滤器控制界面"""
        # 胜平负过滤区域
        wdl_frame = ttk.LabelFrame(parent, text="胜平负过滤", padding="10", style='Card.TLabelframe')
        wdl_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 添加说明文字
        info_label = ttk.Label(wdl_frame, text="说明：勾选任意选项即启用该场过滤，支持多选", 
                              style='Info.TLabel')
        info_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 4场比赛的胜平负设置
        self.wdl_vars = {}
        
        for i in range(4):
            game_frame = ttk.Frame(wdl_frame)
            game_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(game_frame, text=f"第{i+1}场：", width=8).pack(side=tk.LEFT)
            
            # 胜平负多选勾选框
            wdl_vars = {
                '胜': tk.BooleanVar(),
                '平': tk.BooleanVar(), 
                '负': tk.BooleanVar()
            }
            self.wdl_vars[i] = wdl_vars
            
            # 创建三个勾选框
            tk.Checkbutton(game_frame, text="胜", variable=wdl_vars['胜'], 
                          font=('Microsoft YaHei UI', 9)).pack(side=tk.LEFT, padx=(0, 5))
            tk.Checkbutton(game_frame, text="平", variable=wdl_vars['平'], 
                          font=('Microsoft YaHei UI', 9)).pack(side=tk.LEFT, padx=(0, 5))
            tk.Checkbutton(game_frame, text="负", variable=wdl_vars['负'], 
                          font=('Microsoft YaHei UI', 9)).pack(side=tk.LEFT)
        
        # 大小球过滤区域
        ou_frame = ttk.LabelFrame(parent, text="大小球过滤", padding="10", style='Card.TLabelframe')
        ou_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 添加说明文字
        info_label2 = ttk.Label(ou_frame, text="说明：选择非'任意'选项即启用该场过滤，单选模式", 
                               style='Info.TLabel')
        info_label2.pack(anchor=tk.W, pady=(0, 10))
        
        # 4场比赛的大小球设置
        self.ou_vars = {}
        
        for i in range(4):
            game_frame = ttk.Frame(ou_frame)
            game_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(game_frame, text=f"第{i+1}场：", width=8).pack(side=tk.LEFT)
            
            # 大小球单选下拉框
            ou_var = tk.StringVar(value="任意")
            self.ou_vars[i] = ou_var
            
            ou_combo = ttk.Combobox(game_frame, textvariable=ou_var, 
                                  values=["任意", "大球", "小球"], width=8, state="readonly",
                                  style='Modern.TCombobox')
            ou_combo.pack(side=tk.LEFT)
        
        # 操作选择区域
        operation_frame = ttk.LabelFrame(parent, text="操作选择", padding="10", style='Card.TLabelframe')
        operation_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 操作选择单选按钮
        self.operation_var = tk.StringVar(value="保留")
        
        operation_retain = ttk.Radiobutton(operation_frame, text="保留", 
                                         variable=self.operation_var, value="保留")
        operation_retain.pack(side=tk.LEFT, padx=(0, 20))
        
        operation_delete = ttk.Radiobutton(operation_frame, text="删除", 
                                         variable=self.operation_var, value="删除")
        operation_delete.pack(side=tk.LEFT)
        
        ttk.Label(operation_frame, text="符合条件的注", 
                 font=('Microsoft YaHei UI', 10)).pack(side=tk.LEFT, padx=(10, 0))
        
        # 过滤按钮区域
        filter_btn_frame = ttk.Frame(parent)
        filter_btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(filter_btn_frame, text="开始过滤", command=self.apply_filter, 
                  style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(filter_btn_frame, text="重置过滤", command=self.reset_filter, 
                  style='Danger.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(filter_btn_frame, text="比分频率缩水", command=self.show_frequency_filter, 
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(filter_btn_frame, text="自由缩水", command=self.show_free_shrink_dialog, 
                  style='Success.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(filter_btn_frame, text="一键恢复", command=self.undo_last_operation, 
                  style='Secondary.TButton').pack(side=tk.LEFT)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(parent, text="过滤结果", padding="10", style='Card.TLabelframe')
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))
        
        # 结果统计
        self.result_stats = ttk.Label(result_frame, text="过滤结果：0 条", 
                                     font=('Microsoft YaHei UI', 10, 'bold'))
        self.result_stats.pack(pady=(0, 10))
        
        # 结果显示
        self.result_text = scrolledtext.ScrolledText(result_frame, height=8, 
                                                    font=('Consolas', 9),
                                                    bg='white', fg='black',
                                                    relief='flat', bd=1)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 结果操作按钮
        result_btn_frame = ttk.Frame(result_frame)
        result_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(result_btn_frame, text="复制结果", command=self.copy_result, 
                  style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(result_btn_frame, text="清空结果", command=self.clear_result, 
                  style='Danger.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(result_btn_frame, text="导出文本", command=self.export_result, 
                  style='Success.TButton').pack(side=tk.LEFT)
    
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
        """清空输入和投注区"""
        # 清空粘贴区
        self.input_text.delete("1.0", tk.END)
        self.original_data = []
        
        # 清空投注区
        self.betting_text.delete("1.0", tk.END)
        self.betting_data = []
        self.filtered_data = []
        
        # 更新统计显示
        self.stats_label.config(text="数据统计：0 条")
        self.betting_stats.config(text="投注数据：0 条")
    
    def clear_betting_area(self):
        """清空投注区"""
        self.betting_text.delete("1.0", tk.END)
        self.betting_data = []
        self.original_data = []
        self.filtered_data = []
        self.betting_stats.config(text="投注数据：0 条")
        self.stats_label.config(text="数据统计：0 条")
        self.result_text.delete("1.0", tk.END)
        self.result_stats.config(text="过滤结果：0 条")
    
    def apply_filter(self):
        """应用过滤器"""
        if not self.betting_data:
            messagebox.showwarning("警告", "投注区没有数据，请先加载数据到投注区")
            return
        
        try:
            # 保存当前状态到历史记录
            self._save_to_history()
            
            # 获取操作选择
            operation = self.operation_var.get()
            
            self.filtered_data = []
            
            for bet in self.betting_data:
                meets_conditions = self._check_bet(bet)
                
                if operation == "保留":
                    # 保留符合条件的注
                    if meets_conditions:
                        self.filtered_data.append(bet)
                else:  # 删除
                    # 删除符合条件的注，保留不符合条件的注
                    if not meets_conditions:
                        self.filtered_data.append(bet)
            
            # 显示结果
            self._display_results()
            
            # 显示过滤结果统计
            original_count = len(self.betting_data)
            filtered_count = len(self.filtered_data)
            operation_text = "保留" if operation == "保留" else "删除"
            messagebox.showinfo("过滤完成", f"从 {original_count} 条投注数据中{operation_text}了 {filtered_count} 条结果")
            
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
            # 检查是否有任何胜平负选项被选中
            wdl_selected = any(self.wdl_vars[i][result].get() for result in ['胜', '平', '负'])
            if wdl_selected:  # 如果有选项被选中
                home_goals, away_goals = games[i]
                result = self._get_wdl_result(home_goals, away_goals)
                # 检查结果是否在选中的选项中
                if not self.wdl_vars[i][result].get():
                    return False
        
        # 检查大小球过滤
        for i in range(4):
            ou_condition = self.ou_vars[i].get()
            if ou_condition != "任意":  # 如果选择了具体的大小球条件
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
            # 对结果进行升序排序
            sorted_data = sorted(self.filtered_data)
            for bet in sorted_data:
                self.result_text.insert(tk.END, bet + "\n")
        
        self.result_stats.config(text=f"过滤结果：{len(self.filtered_data)} 条")
    
    def reset_filter(self):
        """重置过滤器"""
        # 重置所有选择
        for i in range(4):
            # 重置胜平负选择
            for result in ['胜', '平', '负']:
                self.wdl_vars[i][result].set(False)
            # 重置大小球选择
            self.ou_vars[i].set("任意")
        
        # 清空结果
        self.clear_result()
    
    def copy_result(self):
        """复制结果到剪贴板"""
        # 优先复制过滤结果区，如果为空则复制投注区
        if self.filtered_data:
            # 对结果进行升序排序后复制
            sorted_data = sorted(self.filtered_data)
            result_text = "\n".join(sorted_data)
            self.root.clipboard_clear()
            self.root.clipboard_append(result_text)
            messagebox.showinfo("成功", f"已复制过滤结果 {len(self.filtered_data)} 条到剪贴板")
        elif self.betting_data:
            # 如果过滤结果区为空，复制投注区数据
            sorted_data = sorted(self.betting_data)
            result_text = "\n".join(sorted_data)
            self.root.clipboard_clear()
            self.root.clipboard_append(result_text)
            messagebox.showinfo("成功", f"已复制投注区数据 {len(self.betting_data)} 条到剪贴板")
        else:
            messagebox.showwarning("警告", "没有数据可复制")
    
    def export_result(self):
        """导出结果到文本文件"""
        # 优先导出过滤结果区，如果为空则导出投注区
        if not self.filtered_data and not self.betting_data:
            messagebox.showwarning("警告", "没有数据可导出")
            return
        
        try:
            from tkinter import filedialog
            import os
            from datetime import datetime
            
            # 生成默认文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"过滤结果_{timestamp}.txt"
            
            # 选择保存位置
            file_path = filedialog.asksaveasfilename(
                title="导出过滤结果",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                initialvalue=default_filename
            )
            
            if file_path:
                # 确定要导出的数据源
                if self.filtered_data:
                    data_to_export = self.filtered_data
                    data_type = "过滤结果"
                else:
                    data_to_export = self.betting_data
                    data_type = "投注区数据"
                
                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"4场进球玩法{data_type}\n")
                    f.write(f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"数据数量：{len(data_to_export)} 条\n")
                    f.write("=" * 50 + "\n\n")
                    
                    # 对结果进行升序排序后导出
                    sorted_data = sorted(data_to_export)
                    for i, bet in enumerate(sorted_data, 1):
                        f.write(f"{i:4d}. {bet}\n")
                
                messagebox.showinfo("导出成功", f"已成功导出{data_type} {len(data_to_export)} 条到：\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("导出失败", f"导出文件时发生错误：{e}")
    
    def clear_result(self):
        """清空结果"""
        self.result_text.delete("1.0", tk.END)
        self.filtered_data = []
        self.result_stats.config(text="过滤结果：0 条")
    
    def show_frequency_filter(self):
        """显示比分频率缩水窗口"""
        # 优先检查过滤结果区，如果为空则检查投注区
        if not self.filtered_data and not self.betting_data:
            messagebox.showwarning("警告", "请先加载数据到投注区并进行过滤")
            return
        
        # 创建频率缩水窗口
        freq_window = tk.Toplevel(self.root)
        freq_window.title("比分频率缩水")
        freq_window.geometry("1400x1000")
        freq_window.resizable(True, True)
        
        # 居中显示
        freq_window.update_idletasks()
        x = (freq_window.winfo_screenwidth() // 2) - (1400 // 2)
        y = (freq_window.winfo_screenheight() // 2) - (1000 // 2)
        freq_window.geometry(f'1400x1000+{x}+{y}')
        
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
        summary_frame = ttk.LabelFrame(main_frame, text="频率汇总", padding="10", style='Card.TLabelframe')
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建汇总显示标签
        summary_text = tk.StringVar()
        summary_label = ttk.Label(summary_frame, textvariable=summary_text, 
                                 font=('Microsoft YaHei UI', 11, 'bold'),
                                 foreground='#007bff')
        summary_label.pack()
        
        # 频率调整区域（使用滚动区域）
        freq_frame = ttk.LabelFrame(main_frame, text="频率调整", padding="15", style='Card.TLabelframe')
        freq_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 创建滚动区域
        canvas = tk.Canvas(freq_frame, height=600)
        scrollbar = ttk.Scrollbar(freq_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 创建频率变量存储
        freq_vars = {}
        
        # 创建两列布局：左边第1、2场，右边第3、4场
        main_games_frame = ttk.Frame(scrollable_frame)
        main_games_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧列：第1场和第2场
        left_frame = ttk.Frame(main_games_frame)
        left_frame.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="nsew")
        
        # 右侧列：第3场和第4场
        right_frame = ttk.Frame(main_games_frame)
        right_frame.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="nsew")
        
        # 配置主框架的列权重
        main_games_frame.columnconfigure(0, weight=1)
        main_games_frame.columnconfigure(1, weight=1)
        
        # 创建比赛控件的函数
        def create_game_controls(parent_frame, game_idx):
            game_frame = ttk.LabelFrame(parent_frame, text=f"第{game_idx + 1}场", padding="10", style='Card.TLabelframe')
            game_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            
            # 胜平负三个区域横排
            for result_idx, result_name in enumerate(["胜区", "平区", "负区"]):
                result_frame = ttk.LabelFrame(game_frame, text=result_name, padding="5", style='Card.TLabelframe')
                result_frame.grid(row=0, column=result_idx, padx=5, pady=2, sticky="nsew")
                
                # 获取该结果对应的比分列表
                scores = self._get_scores_by_result(result_idx)
                
                # 为每个比分创建频率调整控件
                for score in scores:
                    score_key = f"game_{game_idx}_{score}"  # game_0_1:0, game_0_0:0 等
                    
                    # 频率调整控件
                    control_frame = ttk.Frame(result_frame)
                    control_frame.pack(fill=tk.X, pady=1)
                    
                    # 比分标签
                    ttk.Label(control_frame, text=f"{score}：", width=6, 
                             font=('Microsoft YaHei UI', 9)).pack(side=tk.LEFT)
            
            # 减少按钮
                    ttk.Button(control_frame, text="◀", width=2, 
                              command=lambda k=score_key: self._adjust_frequency(freq_vars[k], -0.1, summary_text)).pack(side=tk.LEFT, padx=(0, 2))
            
            # 频率输入框
                    freq_var = tk.StringVar(value="0.0")
                    freq_vars[score_key] = freq_var
                    freq_entry = ttk.Entry(control_frame, textvariable=freq_var, width=5, justify=tk.CENTER,
                                          font=('Microsoft YaHei UI', 9))
                    freq_entry.pack(side=tk.LEFT, padx=(0, 2))
                    
                    # 保存输入框引用
                    freq_vars[f"{score_key}_entry"] = freq_entry
                    
                    # 绑定输入框变化事件
                    freq_var.trace('w', lambda *args, k=score_key: self._update_frequency_summary(freq_vars, summary_text))
                    
                    ttk.Label(control_frame, text="%", width=1, 
                             font=('Microsoft YaHei UI', 9)).pack(side=tk.LEFT)
            
            # 增加按钮
                    ttk.Button(control_frame, text="▶", width=2, 
                              command=lambda k=score_key: self._adjust_frequency(freq_vars[k], 0.1, summary_text)).pack(side=tk.LEFT, padx=(2, 0))
            
            # 配置每场比赛的列权重
            for i in range(3):
                game_frame.columnconfigure(i, weight=1)
        
        # 创建左侧的比赛（第1场和第2场）
        create_game_controls(left_frame, 0)  # 第1场
        create_game_controls(left_frame, 1)  # 第2场
        
        # 创建右侧的比赛（第3场和第4场）
        create_game_controls(right_frame, 2)  # 第3场
        create_game_controls(right_frame, 3)  # 第4场
        
        # 显示滚动区域
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 初始化频率显示
        # 使用过滤结果数据，如果没有过滤结果则使用投注区数据
        if self.filtered_data:
            data_to_analyze = self.filtered_data
        elif self.betting_data:
            data_to_analyze = self.betting_data
        else:
            data_to_analyze = []
        
        self._update_frequency_display_new(freq_vars, data_to_analyze, summary_text)
        
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
        """更新频率显示（新版本：胜平负分区显示比分）"""
        try:
            total_count = len(valid_data)
            
            # 统计每场比赛的比分频率
            game_score_stats = {}
            for game_idx in range(4):
                game_score_stats[game_idx] = {}
            
            for bet in valid_data:
                for game_idx in range(4):
                    # 解析该场的主客队进球数
                    home_goals = int(bet[game_idx * 2])
                    away_goals = int(bet[game_idx * 2 + 1])
                    
                    # 构造比分字符串
                    score = f"{home_goals}:{away_goals}"
                    
                    # 统计比分频率
                    if score in game_score_stats[game_idx]:
                        game_score_stats[game_idx][score] += 1
                    else:
                        game_score_stats[game_idx][score] = 1
            
            # 更新界面显示
            for game_idx in range(4):
                for result_idx in range(3):  # 胜平负3个区
                    scores = self._get_scores_by_result(result_idx)
                    for score in scores:
                        var_key = f"game_{game_idx}_{score}"
                        if var_key in freq_vars:
                            if score in game_score_stats[game_idx]:
                                count = game_score_stats[game_idx][score]
                                percentage = (count / total_count) * 100
                                freq_vars[var_key].set(f"{percentage:.1f}")
                            else:
                                freq_vars[var_key].set("0.0")
            
            # 高亮显示有数据的频率
            self._highlight_frequency_entries_by_score(freq_vars, game_score_stats)
            
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
    
    def _highlight_frequency_entries_by_score(self, freq_vars, game_score_stats):
        """高亮显示有数据的频率条目（按比分）"""
        try:
            # 遍历所有比赛和比分，高亮显示有数据的条目
            for game_idx in range(4):
                for result_idx in range(3):
                    scores = self._get_scores_by_result(result_idx)
                    for score in scores:
                        var_key = f"game_{game_idx}_{score}"
                        entry_key = f"{var_key}_entry"
                        
                        if entry_key in freq_vars:
                            entry_widget = freq_vars[entry_key]
                            if score in game_score_stats[game_idx] and game_score_stats[game_idx][score] > 0:
                                # 有数据：使用绿色背景
                                entry_widget.configure(style='Highlight.TEntry')
                            else:
                                # 无数据：使用默认样式
                                entry_widget.configure(style='TEntry')
        except Exception as e:
            print(f"高亮显示失败：{e}")
    
    def _get_scores_by_result(self, result_idx):
        """根据胜平负结果返回对应的比分列表"""
        if result_idx == 0:  # 胜区：主队获胜
            return ["1:0", "2:0", "2:1", "3:0", "3:1", "3:2"]
        elif result_idx == 1:  # 平区：平局
            return ["0:0", "1:1", "2:2", "3:3"]
        else:  # 负区：主队失败
            return ["0:1", "0:2", "1:2", "0:3", "1:3", "2:3"]
    
    def _update_frequency_summary(self, freq_vars, summary_text):
        """更新频率汇总显示（显示注数）"""
        try:
            # 获取当前数据源
            if self.filtered_data:
                current_data = self.filtered_data
                data_source = "过滤结果"
            elif self.betting_data:
                current_data = self.betting_data
                data_source = "投注区数据"
            else:
                current_data = []
                data_source = "无数据"
            
            total_bets = len(current_data)
            
            # 统计有数据的比分数量
            score_count = 0
            total_freq = 0.0
            
            # 统计所有频率设置
            for key, var in freq_vars.items():
                if key.endswith('_entry'):
                    continue
                try:
                    freq = float(var.get())
                    total_freq += freq
                    if freq > 0:
                        score_count += 1
                except ValueError:
                    pass
            
            # 计算基于频率的目标注数
            if total_freq > 0:
                # 假设总频率应该对应总注数
                target_bets = int((total_freq / 400.0) * total_bets) if total_bets > 0 else 0
                remaining_bets = total_bets - target_bets
            else:
                target_bets = 0
                remaining_bets = total_bets
            
            # 限制显示范围
            if remaining_bets < -1000:
                remaining_bets = -1000
            elif remaining_bets > 1000:
                remaining_bets = 1000
            
            # 更新汇总显示
            summary_info = f"总注数: {total_bets} | 目标注数: {target_bets} | 剩余可调: {remaining_bets} | 有数据比分: {score_count}个 | 数据源: {data_source}"
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
        """显示频率统计（新版本：胜平负分区显示比分）"""
        try:
            # 使用过滤结果数据，如果没有过滤结果则使用投注区数据
            if self.filtered_data:
                data_to_analyze = self.filtered_data
                data_source = "过滤结果"
            elif self.betting_data:
                data_to_analyze = self.betting_data
                data_source = "投注区数据"
            else:
                messagebox.showwarning("警告", "没有可用的数据", parent=parent_window)
                return
            total_count = len(data_to_analyze)
            
            # 统计每场比赛的比分频率
            game_score_stats = {}
            for game_idx in range(4):
                game_score_stats[game_idx] = {}
            
            for bet in data_to_analyze:
                for game_idx in range(4):
                    # 解析该场的主客队进球数
                    home_goals = int(bet[game_idx * 2])
                    away_goals = int(bet[game_idx * 2 + 1])
                    
                    # 构造比分字符串
                    score = f"{home_goals}:{away_goals}"
                    
                    # 统计比分频率
                    if score in game_score_stats[game_idx]:
                        game_score_stats[game_idx][score] += 1
                    else:
                        game_score_stats[game_idx][score] = 1
            
            # 显示统计结果
            stats_text = f"4场比赛比分频率统计（基于{data_source}）：\n\n"
            stats_text += f"数据条数：{total_count} 条\n\n"
            
            for game_idx in range(4):
                stats_text += f"第{game_idx + 1}场：\n"
                
                # 按胜平负分区显示
                for result_idx, result_name in enumerate(["胜区", "平区", "负区"]):
                    stats_text += f"  {result_name}：\n"
                    scores = self._get_scores_by_result(result_idx)
                    
                    for score in scores:
                        if score in game_score_stats[game_idx]:
                            count = game_score_stats[game_idx][score]
                            percentage = (count / total_count) * 100
                            stats_text += f"    {score}：{count}次 ({percentage:.1f}%)\n"
                
                stats_text += "\n"
            
            messagebox.showinfo("频率统计", stats_text, parent=parent_window)
            
        except Exception as e:
            messagebox.showerror("错误", f"统计失败：{e}", parent=parent_window)
    
    def _apply_frequency_filter_new(self, freq_vars, parent_window):
        """应用频率过滤（新版本：按比分过滤）"""
        try:
            # 保存当前状态到历史记录
            self._save_to_history()
            
            # 使用过滤结果数据，如果没有过滤结果则使用投注区数据
            if self.filtered_data:
                valid_data = self.filtered_data.copy()
                data_source = "过滤结果"
            elif self.betting_data:
                valid_data = self.betting_data.copy()
                data_source = "投注区数据"
            else:
                messagebox.showwarning("警告", "没有可用的数据", parent=parent_window)
                return
            
            # 获取频率设置
            freq_settings = {}
            for game_idx in range(4):
                for result_idx in range(3):
                    scores = self._get_scores_by_result(result_idx)
                    for score in scores:
                        var_key = f"game_{game_idx}_{score}"
                        if var_key in freq_vars:
                            try:
                                freq_settings[var_key] = float(freq_vars[var_key].get())
                            except ValueError:
                                freq_settings[var_key] = 0.0
            
            # 应用比分频率过滤和扩充
            filtered_data = []
            
            # 首先过滤掉频率为0的比分
            for bet in valid_data:
                should_include = True
                
                for game_idx in range(4):
                    # 解析该场的主客队进球数
                    home_goals = int(bet[game_idx * 2])
                    away_goals = int(bet[game_idx * 2 + 1])
                    
                    # 构造比分字符串
                    score = f"{home_goals}:{away_goals}"
                    
                    var_key = f"game_{game_idx}_{score}"
                    if var_key in freq_settings:
                        if freq_settings[var_key] == 0:
                            should_include = False
                            break
                
                if should_include:
                    filtered_data.append(bet)
            
            # 然后根据频率设置扩充数据
            # 如果用户增加了某些比分的频率，我们需要扩充这些比分的数据
            expanded_data = []
            
            # 统计当前各比分的数量
            score_counts = {}
            for game_idx in range(4):
                score_counts[game_idx] = {}
            
            for bet in filtered_data:
                for game_idx in range(4):
                    home_goals = int(bet[game_idx * 2])
                    away_goals = int(bet[game_idx * 2 + 1])
                    score = f"{home_goals}:{away_goals}"
                    
                    if score in score_counts[game_idx]:
                        score_counts[game_idx][score] += 1
                    else:
                        score_counts[game_idx][score] = 1
            
            # 计算需要扩充的比分
            total_bets = len(filtered_data)
            for game_idx in range(4):
                for result_idx in range(3):
                    scores = self._get_scores_by_result(result_idx)
                    for score in scores:
                        var_key = f"game_{game_idx}_{score}"
                        if var_key in freq_settings:
                            target_freq = freq_settings[var_key]
                            if target_freq > 0:
                                # 计算目标数量
                                target_count = int((target_freq / 100.0) * total_bets)
                                current_count = score_counts[game_idx].get(score, 0)
                                
                                # 如果需要扩充
                                if target_count > current_count:
                                    # 从原始数据中寻找该比分的投注进行扩充
                                    needed = target_count - current_count
                                    found = 0
                                    
                                    # 从投注区数据中寻找该比分的投注
                                    for bet in self.betting_data:
                                        if found >= needed:
                                            break
                                        
                                        bet_home_goals = int(bet[game_idx * 2])
                                        bet_away_goals = int(bet[game_idx * 2 + 1])
                                        bet_score = f"{bet_home_goals}:{bet_away_goals}"
                                        
                                        if bet_score == score and bet not in filtered_data:
                                            # 检查这个投注是否满足其他条件
                                            other_games_ok = True
                                            for other_game_idx in range(4):
                                                if other_game_idx != game_idx:
                                                    other_var_key = f"game_{other_game_idx}_{bet[other_game_idx * 2]}:{bet[other_game_idx * 2 + 1]}"
                                                    if other_var_key in freq_settings and freq_settings[other_var_key] == 0:
                                                        other_games_ok = False
                                                        break
                                            
                                            if other_games_ok:
                                                filtered_data.append(bet)
                                                found += 1
                                
                                # 如果需要缩水（当前数量超过目标数量）
                                elif target_count < current_count:
                                    # 随机移除多余的该比分投注
                                    excess = current_count - target_count
                                    removed = 0
                                    
                                    # 找到所有该比分的投注
                                    bets_to_remove = []
                                    for bet in filtered_data:
                                        if removed >= excess:
                                            break
                                        
                                        bet_home_goals = int(bet[game_idx * 2])
                                        bet_away_goals = int(bet[game_idx * 2 + 1])
                                        bet_score = f"{bet_home_goals}:{bet_away_goals}"
                                        
                                        if bet_score == score:
                                            bets_to_remove.append(bet)
                                            removed += 1
                                    
                                    # 从filtered_data中移除这些投注
                                    for bet in bets_to_remove:
                                        if bet in filtered_data:
                                            filtered_data.remove(bet)
            
            # 最终结果
            final_data = filtered_data
            
            # 更新结果
            self.filtered_data = final_data
            self._display_results()
            
            # 更新数据统计
            self.result_stats.config(text=f"过滤结果：{len(final_data)} 条")
            
            # 显示完成提示和详细统计
            original_count = len(valid_data)
            filtered_count = len(final_data)
            reduction_rate = ((original_count - filtered_count) / original_count * 100) if original_count > 0 else 0
            
            # 统计被过滤掉的比分
            filtered_scores = []
            for game_idx in range(4):
                for result_idx in range(3):
                    scores = self._get_scores_by_result(result_idx)
                    for score in scores:
                        var_key = f"game_{game_idx}_{score}"
                        if var_key in freq_settings and freq_settings[var_key] == 0:
                            filtered_scores.append(f"第{game_idx + 1}场{score}")
            
            # 计算扩充情况
            if filtered_count > original_count:
                expansion_rate = ((filtered_count - original_count) / original_count * 100) if original_count > 0 else 0
                detail_text = f"频率调整完成！\n\n"
                detail_text += f"数据源：{data_source}\n"
                detail_text += f"原始数据：{original_count} 条\n"
                detail_text += f"调整结果：{filtered_count} 条\n"
                detail_text += f"扩充比例：+{expansion_rate:.1f}%\n\n"
            else:
                detail_text = f"频率缩水完成！\n\n"
                detail_text += f"数据源：{data_source}\n"
                detail_text += f"原始数据：{original_count} 条\n"
                detail_text += f"筛选结果：{filtered_count} 条\n"
                detail_text += f"缩水比例：{reduction_rate:.1f}%\n\n"
            
            if filtered_scores:
                detail_text += f"被过滤的比分：\n"
                for score in filtered_scores[:10]:  # 最多显示10个
                    detail_text += f"• {score}\n"
                if len(filtered_scores) > 10:
                    detail_text += f"... 等{len(filtered_scores)}个比分"
            
            messagebox.showinfo("频率缩水完成", detail_text, parent=parent_window)
            
            # 关闭窗口
            parent_window.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"频率过滤失败：{e}", parent=parent_window)
    
    def _save_to_history(self):
        """保存当前状态到历史记录"""
        if self.filtered_data:
            self.history.append({
                'filtered_data': self.filtered_data.copy(),
                'operation': 'filter'
            })
            # 限制历史记录数量，避免内存过多占用
            if len(self.history) > 10:
                self.history.pop(0)
    
    def undo_last_operation(self):
        """恢复上一次操作"""
        # 优先检查过滤结果区，如果为空则检查投注区
        if not self.filtered_data and not self.betting_data:
            messagebox.showwarning("警告", "没有可用的数据进行恢复操作")
            return
            
        if not self.history:
            messagebox.showinfo("提示", "没有可恢复的操作")
            return
        
        try:
            # 获取上一次状态
            last_state = self.history.pop()
            self.filtered_data = last_state['filtered_data']
            
            # 更新显示
            self._display_results()
            
            messagebox.showinfo("恢复完成", f"已恢复到上一次操作，当前结果：{len(self.filtered_data)} 条")
            
        except Exception as e:
            messagebox.showerror("错误", f"恢复失败：{e}")
    
    def show_free_shrink_dialog(self):
        """显示自由缩水对话框"""
        # 优先检查过滤结果区，如果为空则检查投注区
        if not self.filtered_data and not self.betting_data:
            messagebox.showwarning("警告", "请先加载数据到投注区并进行过滤")
            return
        
        # 创建缩水对话框
        shrink_window = tk.Toplevel(self.root)
        shrink_window.title("自由缩水")
        shrink_window.geometry("600x600")
        shrink_window.resizable(True, True)
        shrink_window.transient(self.root)
        shrink_window.grab_set()
        
        # 居中显示
        shrink_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # 主框架
        main_frame = ttk.Frame(shrink_window, padding="25")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 投注总金额设置
        amount_frame = ttk.LabelFrame(main_frame, text="投注总金额(M)", padding="15", style='Card.TLabelframe')
        amount_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 限定投注金额
        self.limit_amount_var = tk.BooleanVar(value=True)
        ttk.Radiobutton(amount_frame, text="限定投注金额为", variable=self.limit_amount_var, 
                       value=True).pack(anchor=tk.W)
        
        limit_frame = ttk.Frame(amount_frame)
        limit_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.target_amount_var = tk.StringVar(value="200")
        ttk.Entry(limit_frame, textvariable=self.target_amount_var, width=10).pack(side=tk.LEFT)
        ttk.Label(limit_frame, text="注").pack(side=tk.LEFT, padx=(5, 0))
        
        # 不限制投注金额
        ttk.Radiobutton(amount_frame, text="不限制投注金额", variable=self.limit_amount_var, 
                       value=False).pack(anchor=tk.W, pady=(10, 0))
        
        # 选注范围设置
        scope_frame = ttk.LabelFrame(main_frame, text="选注范围(S)", padding="15", style='Card.TLabelframe')
        scope_frame.pack(fill=tk.X, pady=(0, 25))
        
        self.selection_method_var = tk.StringVar(value="random")
        
        ttk.Radiobutton(scope_frame, text="从所有投注结果中随机选择", 
                       variable=self.selection_method_var, value="random").pack(anchor=tk.W)
        ttk.Radiobutton(scope_frame, text="从所有奇数序号投注结果中选择", 
                       variable=self.selection_method_var, value="odd").pack(anchor=tk.W)
        ttk.Radiobutton(scope_frame, text="从所有偶数序号投注结果中选择", 
                       variable=self.selection_method_var, value="even").pack(anchor=tk.W)
        ttk.Radiobutton(scope_frame, text="从所有投注结果中均匀选择", 
                       variable=self.selection_method_var, value="uniform").pack(anchor=tk.W)
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="开始缩水", command=lambda: self._apply_free_shrink(shrink_window)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=shrink_window.destroy).pack(side=tk.LEFT)
    
    def _apply_free_shrink(self, parent_window):
        """应用自由缩水"""
        try:
            # 保存当前状态到历史记录
            self._save_to_history()
            
            # 获取数据源
            if self.filtered_data:
                source_data = self.filtered_data
                data_source = "过滤结果"
            else:
                source_data = self.betting_data
                data_source = "投注区数据"
            
            # 获取目标数量
            if self.limit_amount_var.get():
                try:
                    target_count = int(self.target_amount_var.get())
                    if target_count <= 0:
                        messagebox.showerror("错误", "目标数量必须大于0", parent=parent_window)
                        return
                except ValueError:
                    messagebox.showerror("错误", "请输入有效的数字", parent=parent_window)
                    return
            else:
                target_count = len(source_data)
            
            # 如果目标数量大于等于源数据数量，不需要缩水
            if target_count >= len(source_data):
                messagebox.showinfo("提示", f"目标数量({target_count})大于等于源数据数量({len(source_data)})，无需缩水", parent=parent_window)
                parent_window.destroy()
                return
            
            # 根据选择方法进行缩水
            method = self.selection_method_var.get()
            if method == "random":
                # 随机选择
                import random
                self.filtered_data = random.sample(source_data, target_count)
            elif method == "odd":
                # 奇数序号选择
                odd_indices = [i for i in range(0, len(source_data), 2)]  # 0, 2, 4, 6...
                if len(odd_indices) >= target_count:
                    selected_indices = odd_indices[:target_count]
                else:
                    # 如果奇数序号不够，补充偶数序号
                    even_indices = [i for i in range(1, len(source_data), 2)]  # 1, 3, 5, 7...
                    selected_indices = odd_indices + even_indices[:target_count - len(odd_indices)]
                self.filtered_data = [source_data[i] for i in selected_indices]
            elif method == "even":
                # 偶数序号选择
                even_indices = [i for i in range(1, len(source_data), 2)]  # 1, 3, 5, 7...
                if len(even_indices) >= target_count:
                    selected_indices = even_indices[:target_count]
                else:
                    # 如果偶数序号不够，补充奇数序号
                    odd_indices = [i for i in range(0, len(source_data), 2)]  # 0, 2, 4, 6...
                    selected_indices = even_indices + odd_indices[:target_count - len(even_indices)]
                self.filtered_data = [source_data[i] for i in selected_indices]
            elif method == "uniform":
                # 均匀选择 - 保持原有频率分布
                self.filtered_data = self._uniform_selection_with_frequency_preservation(source_data, target_count)
            
            # 更新显示
            self._display_results()
            
            # 显示结果
            original_count = len(source_data)
            final_count = len(self.filtered_data)
            reduction_rate = ((original_count - final_count) / original_count * 100) if original_count > 0 else 0
            
            messagebox.showinfo("缩水完成", 
                              f"缩水完成！\n\n"
                              f"数据源：{data_source}\n"
                              f"原始数量：{original_count} 条\n"
                              f"缩水后：{final_count} 条\n"
                              f"缩水比例：{reduction_rate:.1f}%\n"
                              f"选择方法：{self._get_method_name(method)}", 
                              parent=parent_window)
            
            # 关闭窗口
            parent_window.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"缩水失败：{e}", parent=parent_window)
    
    def _uniform_selection_with_frequency_preservation(self, source_data, target_count):
        """均匀选择并保持原有频率分布"""
        if target_count >= len(source_data):
            return source_data.copy()
        
        # 统计每种比分组合的频率
        score_groups = {}
        for bet in source_data:
            # 将8位数字转换为比分组合的字符串
            score_key = bet  # 直接使用投注字符串作为键
            if score_key in score_groups:
                score_groups[score_key].append(bet)
            else:
                score_groups[score_key] = [bet]
        
        # 计算每种比分组合应该保留的数量
        result = []
        for score_key, bets in score_groups.items():
            # 按比例计算该比分组合应该保留的数量
            original_count = len(bets)
            target_ratio = target_count / len(source_data)
            target_for_this_score = max(1, int(original_count * target_ratio))
            
            # 如果计算出的数量超过实际数量，则取实际数量
            target_for_this_score = min(target_for_this_score, original_count)
            
            # 从该比分组合中均匀选择
            if target_for_this_score == original_count:
                result.extend(bets)
            else:
                step = original_count / target_for_this_score
                selected_indices = [int(i * step) for i in range(target_for_this_score)]
                for idx in selected_indices:
                    if idx < len(bets):
                        result.append(bets[idx])
        
        # 如果结果数量不够，随机补充
        if len(result) < target_count:
            remaining_needed = target_count - len(result)
            remaining_bets = [bet for bet in source_data if bet not in result]
            if remaining_bets:
                import random
                additional = random.sample(remaining_bets, min(remaining_needed, len(remaining_bets)))
                result.extend(additional)
        
        # 如果结果数量超过目标，随机移除
        elif len(result) > target_count:
            import random
            result = random.sample(result, target_count)
        
        return result
    
    def _get_method_name(self, method):
        """获取方法名称"""
        method_names = {
            "random": "随机选择",
            "odd": "奇数序号选择",
            "even": "偶数序号选择",
            "uniform": "均匀选择(保持频率分布)"
        }
        return method_names.get(method, "未知方法")
    
    def auto_refresh_period_and_details(self):
        """自动刷新期号并获取详情"""
        try:
            # 调用体彩API获取最新5期期号
            url = "https://webapi.sporttery.cn/gateway/lottery/getFootBallMatchV1.qry"
            params = {
                'param': '94,0',
                'lotteryDrawNum': '',
                'sellStatus': '0',
                'termLimits': '5'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'value' in data and 'jqclist' in data['value']:
                    # 获取最新5期期号
                    periods = []
                    for item in data['value']['jqclist']:
                        if isinstance(item, str) and item:
                            periods.append(item)
                    
                    if periods:
                        # 更新下拉框选项
                        self.period_combo['values'] = periods
                        # 设置最新期号为当前值
                        self.period_var.set(periods[0])
                        self.current_period = periods[0]
                        
                        # 自动获取详情
                        self.get_match_details()
                    else:
                        messagebox.showwarning("警告", "未找到期号数据")
                else:
                    messagebox.showwarning("警告", "API返回数据格式异常")
            else:
                messagebox.showerror("错误", f"API请求失败，状态码：{response.status_code}")
                
        except Exception as e:
            messagebox.showerror("错误", f"自动刷新失败：{e}")
    
    def on_period_changed(self, *args):
        """期号变化时的回调函数"""
        # 延迟执行，避免频繁调用
        if hasattr(self, '_period_change_timer'):
            self.root.after_cancel(self._period_change_timer)
        
        self._period_change_timer = self.root.after(500, self.get_match_details)
    
    def refresh_period(self):
        """刷新期号"""
        try:
            # 调用体彩API获取最新5期期号
            url = "https://webapi.sporttery.cn/gateway/lottery/getFootBallMatchV1.qry"
            params = {
                'param': '94,0',
                'lotteryDrawNum': '',
                'sellStatus': '0',
                'termLimits': '5'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'value' in data and 'jqclist' in data['value']:
                    # 获取最新5期期号
                    periods = []
                    for item in data['value']['jqclist']:
                        if isinstance(item, str) and item:
                            periods.append(item)
                    
                    if periods:
                        # 更新下拉框选项
                        self.period_combo['values'] = periods
                        # 设置最新期号为当前值
                        self.period_var.set(periods[0])
                        self.current_period = periods[0]
                        messagebox.showinfo("成功", f"已获取最新5期期号：{', '.join(periods)}")
                    else:
                        messagebox.showwarning("警告", "未找到期号数据")
                else:
                    messagebox.showwarning("警告", "API返回数据格式异常")
            else:
                messagebox.showerror("错误", f"API请求失败，状态码：{response.status_code}")
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("错误", f"网络请求失败：{e}")
        except Exception as e:
            messagebox.showerror("错误", f"刷新期号失败：{e}")
    
    def get_match_details(self):
        """获取对阵详情"""
        try:
            period = self.period_var.get().strip()
            if not period:
                messagebox.showwarning("警告", "请输入期号")
                return
            
            # 调用体彩API获取对阵信息
            url = "https://webapi.sporttery.cn/gateway/lottery/getFootBallMatchV1.qry"
            params = {
                'param': '94,0',
                'lotteryDrawNum': period,
                'sellStatus': '0',
                'termLimits': '1'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'value' in data and 'jqcMatch' in data['value']:
                    match_info = data['value']['jqcMatch']
                    self._display_match_details(match_info)
                else:
                    messagebox.showwarning("警告", "未找到该期号的对阵信息")
            else:
                messagebox.showerror("错误", f"API请求失败，状态码：{response.status_code}")
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("错误", f"网络请求失败：{e}")
        except Exception as e:
            messagebox.showerror("错误", f"获取详情失败：{e}")
    
    def _display_match_details(self, match_info):
        """显示对阵详情"""
        try:
            self.details_text.delete("1.0", tk.END)
            
            # 显示基本信息
            period = match_info.get('lotteryDrawNum', '未知')
            sell_end_time = match_info.get('sellEndTime', '未知')
            
            details = f"第{period}期尚未开奖\n"
            details += f"销售截止: {sell_end_time}\n"
            details += f"对阵信息:\n"
            
            # 显示对阵信息
            match_list = match_info.get('matchList', [])
            self.match_data = match_list
            
            for i, match in enumerate(match_list[:4]):  # 只显示前4场
                # 正确解析API数据
                match_num = match.get('matchNum', '未知')
                master_team = match.get('masterTeamName', '未知')
                guest_team = match.get('guestTeamName', '未知')
                league = match.get('matchName', '未知')  # 联赛名称
                match_time = match.get('startTime', '未知')  # 开赛时间
                
                print(f"解析第{i+1}场: matchNum={match_num}, 主队={master_team}, 客队={guest_team}, 联赛={league}")
                
                details += f"第{match_num}场: {master_team} vs {guest_team} -\n"
                
                # 更新表格显示
                self._update_match_table(match_num, master_team, guest_team, league, match_time)
            
            self.details_text.insert("1.0", details)
            
        except Exception as e:
            messagebox.showerror("错误", f"显示详情失败：{e}")
    
    def _update_match_table(self, match_num, master_team, guest_team, league, match_time):
        """更新对阵表格显示"""
        try:
            # 将match_num转换为索引（假设match_num是1-4）
            if isinstance(match_num, str):
                game_idx = int(match_num) - 1 if match_num.isdigit() else 0
            else:
                game_idx = int(match_num) - 1
            
            # 确保索引在有效范围内
            if 0 <= game_idx < 4 and game_idx in self.match_labels:
                labels = self.match_labels[game_idx]
                
                # 更新场次
                labels['match_num'].config(text=str(match_num))
                
                # 更新联赛
                labels['league'].config(text=league)
                
                # 更新开赛日期
                if match_time:
                    # 直接使用API返回的日期格式
                    labels['date'].config(text=match_time)
                
                # 更新主队 VS 客队
                teams_text = f"{master_team} VS {guest_team}"
                labels['teams'].config(text=teams_text)
                
                print(f"更新第{game_idx+1}场: {teams_text} ({league})")
                
        except Exception as e:
            print(f"更新表格失败：{e}")
    
    def generate_bets(self):
        """生成投注"""
        try:
            # 收集所有选择的投注
            bets = []
            
            # 遍历4场比赛
            for game_idx in range(4):
                if game_idx not in self.match_vars:
                    continue
                
                home_goals = []
                away_goals = []
                
                # 收集主队进球选择
                if "主" in self.match_vars[game_idx]:
                    for goal, var in self.match_vars[game_idx]["主"].items():
                        if var.get():
                            if goal == "3+":
                                home_goals.append("3")
                            else:
                                home_goals.append(goal)
                
                # 收集客队进球选择
                if "客" in self.match_vars[game_idx]:
                    for goal, var in self.match_vars[game_idx]["客"].items():
                        if var.get():
                            if goal == "3+":
                                away_goals.append("3")
                            else:
                                away_goals.append(goal)
                
                # 如果没有选择，默认选择0球
                if not home_goals:
                    home_goals = ["0"]
                if not away_goals:
                    away_goals = ["0"]
                
                # 生成该场比赛的所有组合
                game_bets = []
                for h_goal in home_goals:
                    for a_goal in away_goals:
                        game_bets.append((h_goal, a_goal))
                
                bets.append(game_bets)
            
            # 生成所有投注组合
            all_bets = self._generate_all_combinations(bets)
            
            # 将生成的投注添加到投注区
            if all_bets:
                # 转换为8位数字格式
                bet_strings = []
                for bet in all_bets:
                    bet_str = ""
                    for game_bet in bet:
                        bet_str += game_bet[0] + game_bet[1]
                    bet_strings.append(bet_str)
                
                # 添加到投注区
                self.betting_text.delete("1.0", tk.END)
                self.betting_text.insert("1.0", "\n".join(bet_strings))
                
                # 更新投注区数据
                self.betting_data = bet_strings.copy()
                self.original_data = bet_strings.copy()
                
                # 更新统计
                self.betting_stats.config(text=f"投注数据：{len(bet_strings)} 条")
                
                messagebox.showinfo("成功", f"已生成 {len(bet_strings)} 条投注数据")
            else:
                messagebox.showwarning("警告", "请至少选择一些投注选项")
                
        except Exception as e:
            messagebox.showerror("错误", f"生成投注失败：{e}")
    
    def _generate_all_combinations(self, bets):
        """生成所有投注组合"""
        if not bets:
            return []
        
        if len(bets) == 1:
            return [[bet] for bet in bets[0]]
        
        result = []
        for bet in bets[0]:
            for combo in self._generate_all_combinations(bets[1:]):
                result.append([bet] + combo)
        
        return result

def main():
    root = tk.Tk()
    app = JQC4GameFilter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
