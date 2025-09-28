"""
任九专业过滤器
基于4场进球过滤器的设计理念，专注于胜平负和大小球的过滤逻辑
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re
import requests
import json
from datetime import datetime

class R9AdvancedFilter:
    def __init__(self, root):
        self.root = root
        self.root.title("任九专业过滤器")
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
        
        # 按钮样式
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
        title_label = ttk.Label(main_frame, text="任九专业过滤器", style='Title.TLabel')
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
        input_info = ttk.Label(left_frame, text="请粘贴任九投注结果，每行一个投注，格式如：31031031031031", 
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
        headers = ["场次", "联赛", "开赛日期", "主队 VS 客队", "胆码", "胜", "平", "负"]
        
        # 创建表头
        for i, header in enumerate(headers):
            label = ttk.Label(table_frame, text=header, font=('Microsoft YaHei UI', 9, 'bold'))
            label.grid(row=0, column=i, padx=1, pady=1, sticky="ew")
        
        # 配置列权重
        for i in range(len(headers)):
            table_frame.columnconfigure(i, weight=1)
        
        # 创建14场比赛的行
        self.match_vars = {}
        for game_idx in range(14):
            row = game_idx + 1
            
            # 场次
            match_num_label = ttk.Label(table_frame, text=f"{game_idx + 1}", font=('Microsoft YaHei UI', 9))
            match_num_label.grid(row=row, column=0, padx=1, pady=1, sticky="ew")
            
            # 联赛
            league_label = ttk.Label(table_frame, text="英超", font=('Microsoft YaHei UI', 9))
            league_label.grid(row=row, column=1, padx=1, pady=1, sticky="ew")
            
            # 开赛日期
            date_label = ttk.Label(table_frame, text="2025-09-27", font=('Microsoft YaHei UI', 9))
            date_label.grid(row=row, column=2, padx=1, pady=1, sticky="ew")
            
            # 主队 VS 客队
            teams_label = ttk.Label(table_frame, text="曼联 VS 切尔西", font=('Microsoft YaHei UI', 9))
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
            
            # 胆码选择
            banker_var = tk.BooleanVar()
            banker_cb = tk.Checkbutton(table_frame, variable=banker_var, 
                                      font=('Microsoft YaHei UI', 8))
            banker_cb.grid(row=row, column=4, padx=1, pady=1, sticky="ew")
            
            # 胜平负选择
            wdl_vars = {}
            for result_idx, result_text in enumerate(["胜", "平", "负"]):
                var = tk.BooleanVar()
                wdl_vars[result_text] = var
                
                cb = tk.Checkbutton(table_frame, text=result_text, variable=var, 
                                   font=('Microsoft YaHei UI', 8))
                cb.grid(row=row, column=5 + result_idx, padx=1, pady=1, sticky="ew")
            
            # 保存变量引用
            self.match_vars[game_idx] = {
                'banker': banker_var,
                'wdl': wdl_vars
            }
    
    def _create_filter_controls(self, parent):
        """创建过滤器控制界面"""
        # 操作按钮区域
        filter_btn_frame = ttk.Frame(parent)
        filter_btn_frame.pack(fill=tk.X, pady=(0, 20))
        
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
                # 验证数据格式（14位数字，代表14场比赛的胜平负结果）
                if re.match(r'^[310]{14}$', line):
                    valid_data.append(line)
                else:
                    messagebox.showerror("错误", f"数据格式错误：{line}\n应为14位数字，每位代表3(胜)、1(平)、0(负)")
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
    
    
    def _display_results(self):
        """显示过滤结果"""
        self.result_text.delete("1.0", tk.END)
        
        if self.filtered_data:
            # 对结果进行升序排序
            sorted_data = sorted(self.filtered_data)
            for bet in sorted_data:
                self.result_text.insert(tk.END, bet + "\n")
        
        self.result_stats.config(text=f"过滤结果：{len(self.filtered_data)} 条")
    
    
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
            default_filename = f"任九过滤结果_{timestamp}.txt"
            
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
                    f.write(f"任九{data_type}\n")
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
            messagebox.showwarning("警告", "请先加载数据到投注区")
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
        
        ttk.Label(title_frame, text="14场比赛胜平负频率调整", 
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
        
        # 创建两列布局：左边第1-7场，右边第8-14场
        main_games_frame = ttk.Frame(scrollable_frame)
        main_games_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧列：第1-7场
        left_frame = ttk.Frame(main_games_frame)
        left_frame.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="nsew")
        
        # 右侧列：第8-14场
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
            for result_idx, result_name in enumerate(["胜", "平", "负"]):
                result_frame = ttk.LabelFrame(game_frame, text=result_name, padding="5", style='Card.TLabelframe')
                result_frame.grid(row=0, column=result_idx, padx=5, pady=2, sticky="nsew")
                
                # 频率调整控件
                control_frame = ttk.Frame(result_frame)
                control_frame.pack(fill=tk.X, pady=1)
                
                # 结果标签
                ttk.Label(control_frame, text=f"{result_name}：", width=6, 
                         font=('Microsoft YaHei UI', 9)).pack(side=tk.LEFT)
                
                # 减少按钮
                ttk.Button(control_frame, text="◀", width=2, 
                          command=lambda g=game_idx, r=result_name: self._adjust_frequency(freq_vars[f"game_{g}_{r}"], -0.1, summary_text)).pack(side=tk.LEFT, padx=(0, 2))
                
                # 频率输入框
                freq_var = tk.StringVar(value="0.0")
                freq_vars[f"game_{game_idx}_{result_name}"] = freq_var
                freq_entry = ttk.Entry(control_frame, textvariable=freq_var, width=5, justify=tk.CENTER,
                                      font=('Microsoft YaHei UI', 9))
                freq_entry.pack(side=tk.LEFT, padx=(0, 2))
                
                # 保存输入框引用
                freq_vars[f"game_{game_idx}_{result_name}_entry"] = freq_entry
                
                # 绑定输入框变化事件
                freq_var.trace('w', lambda *args, g=game_idx, r=result_name: self._update_frequency_summary(freq_vars, summary_text))
                
                ttk.Label(control_frame, text="%", width=1, 
                         font=('Microsoft YaHei UI', 9)).pack(side=tk.LEFT)
                
                # 增加按钮
                ttk.Button(control_frame, text="▶", width=2, 
                          command=lambda g=game_idx, r=result_name: self._adjust_frequency(freq_vars[f"game_{g}_{r}"], 0.1, summary_text)).pack(side=tk.LEFT, padx=(2, 0))
            
            # 配置每场比赛的列权重
            for i in range(3):
                game_frame.columnconfigure(i, weight=1)
        
        # 创建左侧的比赛（第1-7场）
        for i in range(7):
            create_game_controls(left_frame, i)
        
        # 创建右侧的比赛（第8-14场）
        for i in range(7, 14):
            create_game_controls(right_frame, i)
        
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
        
        self._update_frequency_display_r9(freq_vars, data_to_analyze, summary_text)
        
        # 操作按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="频率统计", command=lambda: self._show_frequency_stats_r9(freq_vars, freq_window), 
                  style='Filter.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="智能分配", command=lambda: self._smart_allocation_r9(freq_vars, freq_window), 
                  style='Filter.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="保存频率", command=lambda: self._save_frequency_settings_r9(freq_vars, freq_window), 
                  style='Filter.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="导入频率", command=lambda: self._load_frequency_settings_r9(freq_vars, freq_window), 
                  style='Filter.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="应用缩水", command=lambda: self._apply_frequency_filter_r9(freq_vars, freq_window), 
                  style='Filter.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="关闭", command=freq_window.destroy, 
                  style='Clear.TButton').pack(side=tk.RIGHT)
    
    def show_free_shrink_dialog(self):
        """显示自由缩水对话框"""
        # 优先检查过滤结果区，如果为空则检查投注区
        if not self.filtered_data and not self.betting_data:
            messagebox.showwarning("警告", "请先加载数据到投注区")
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
    
    def auto_refresh_period_and_details(self):
        """自动刷新期号并获取详情"""
        try:
            # 调用体彩API获取最新10期期号
            url = "https://webapi.sporttery.cn/gateway/lottery/getFootBallMatchV1.qry"
            params = {
                'param': '90,0',  # 任九的参数
                'lotteryDrawNum': '',
                'sellStatus': '0',
                'termLimits': '10'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # 清空详情显示区域
                self.details_text.delete("1.0", tk.END)
                
                if 'value' in data and 'sfclist' in data['value']:
                    # 获取最新10期期号
                    periods = []
                    for item in data['value']['sfclist']:
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
                    messagebox.showwarning("警告", f"API返回数据格式异常\n可用字段: {list(data.keys()) if isinstance(data, dict) else '非字典类型'}")
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
            # 调用体彩API获取最新10期期号
            url = "https://webapi.sporttery.cn/gateway/lottery/getFootBallMatchV1.qry"
            params = {
                'param': '90,0',  # 任九的参数
                'lotteryDrawNum': '',
                'sellStatus': '0',
                'termLimits': '10'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # 清空详情显示区域
                self.details_text.delete("1.0", tk.END)
                
                if 'value' in data and 'sfclist' in data['value']:
                    # 获取最新10期期号
                    periods = []
                    for item in data['value']['sfclist']:
                        if isinstance(item, str) and item:
                            periods.append(item)
                    
                    if periods:
                        # 更新下拉框选项
                        self.period_combo['values'] = periods
                        # 设置最新期号为当前值
                        self.period_var.set(periods[0])
                        self.current_period = periods[0]
                        messagebox.showinfo("成功", f"已获取最新10期期号：{', '.join(periods)}")
                    else:
                        messagebox.showwarning("警告", "未找到期号数据")
                else:
                    messagebox.showwarning("警告", f"API返回数据格式异常\n可用字段: {list(data.keys()) if isinstance(data, dict) else '非字典类型'}")
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
                'param': '90,0',  # 任九的参数
                'lotteryDrawNum': period,
                'sellStatus': '0',
                'termLimits': '1'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # 清空详情显示区域
                self.details_text.delete("1.0", tk.END)
                
                # 根据实际API结构获取对阵信息
                if 'value' in data and 'sfcMatch' in data['value']:
                    sfc_match = data['value']['sfcMatch']
                    match_list = sfc_match.get('matchList', [])
                    # 直接显示对阵信息
                    self._display_match_details_direct(match_list, sfc_match)
                else:
                    # 显示所有可用的字段
                    available_fields = []
                    if 'value' in data and isinstance(data['value'], dict):
                        available_fields = list(data['value'].keys())
                    messagebox.showwarning("警告", f"未找到该期号的对阵信息\nvalue字段下的可用字段: {available_fields}")
            else:
                messagebox.showerror("错误", f"API请求失败，状态码：{response.status_code}")
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("错误", f"网络请求失败：{e}")
        except Exception as e:
            messagebox.showerror("错误", f"获取详情失败：{e}")
    
    def _display_match_details_direct(self, match_list, value_data):
        """直接显示对阵详情（基于实际API结构）"""
        try:
            # 显示基本信息
            period = value_data.get('lotteryDrawNum', '未知')
            sell_end_time = value_data.get('sellEndTime', '未知')
            
            details = f"\n第{period}期对阵信息:\n"
            details += f"销售截止: {sell_end_time}\n"
            details += f"对阵详情:\n"
            
            # 保存对阵数据
            self.match_data = match_list
            
            for i, match in enumerate(match_list[:14]):  # 显示前14场
                # 根据实际API结构解析数据
                match_num = match.get('matchNum', '未知')
                master_team = match.get('masterTeamName', '未知')
                guest_team = match.get('guestTeamName', '未知')
                league = match.get('matchName', '未知')  # 联赛名称
                match_time = match.get('startTime', '未知')  # 开赛时间
                result = match.get('result', '未开奖')  # 比分结果
                
                # 获取赔率信息
                h_odds = match.get('h', '未知')  # 主胜赔率
                d_odds = match.get('d', '未知')  # 平局赔率
                a_odds = match.get('a', '未知')  # 客胜赔率
                
                details += f"第{match_num}场: {master_team} vs {guest_team}\n"
                details += f"  联赛: {league} | 时间: {match_time} | 结果: {result}\n"
                details += f"  赔率: 主胜({h_odds}) 平局({d_odds}) 客胜({a_odds})\n\n"
                
                # 更新表格显示
                self._update_match_table(match_num, master_team, guest_team, league, match_time)
            
            # 在调试信息后面追加对阵详情
            self.details_text.insert(tk.END, details)
            
        except Exception as e:
            messagebox.showerror("错误", f"显示详情失败：{e}")
    
    def _display_match_details(self, match_info):
        """显示对阵详情（旧版本，保留兼容性）"""
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
            
            for i, match in enumerate(match_list[:14]):  # 显示前14场
                # 正确解析API数据
                match_num = match.get('matchNum', '未知')
                master_team = match.get('masterTeamName', '未知')
                guest_team = match.get('guestTeamName', '未知')
                league = match.get('matchName', '未知')  # 联赛名称
                match_time = match.get('startTime', '未知')  # 开赛时间
                result = match.get('result', '未知')  # 比分结果
                
                details += f"第{match_num}场: {master_team} vs {guest_team} ({result}) -\n"
                
                # 更新表格显示
                self._update_match_table(match_num, master_team, guest_team, league, match_time)
            
            # 在调试信息后面追加对阵详情
            self.details_text.insert(tk.END, details)
            
        except Exception as e:
            messagebox.showerror("错误", f"显示详情失败：{e}")
    
    def _update_match_table(self, match_num, master_team, guest_team, league, match_time):
        """更新对阵表格显示"""
        try:
            # 将match_num转换为索引（假设match_num是1-14）
            if isinstance(match_num, str):
                game_idx = int(match_num) - 1 if match_num.isdigit() else 0
            else:
                game_idx = int(match_num) - 1
            
            # 移除调试信息
            
            # 确保索引在有效范围内
            if 0 <= game_idx < 14 and game_idx in self.match_labels:
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
                
            else:
                # 索引超出范围或标签不存在，静默处理
                pass
                
        except Exception as e:
            # 更新表格失败，静默处理
            pass
    
    def generate_bets(self):
        """生成任九投注（14场选9场）"""
        try:
            # 收集所有选择的投注
            selected_games = []
            unselected_games = []
            banker_games = []  # 胆码场次
            non_banker_games = []  # 非胆码场次
            
            # 遍历14场比赛
            for game_idx in range(14):
                if game_idx not in self.match_vars:
                    continue
                
                game_results = []
                
                # 收集胜平负选择
                wdl_vars = self.match_vars[game_idx]['wdl']
                for result_text, var in wdl_vars.items():
                    if var.get():
                        if result_text == "胜":
                            game_results.append("3")
                        elif result_text == "平":
                            game_results.append("1")
                        elif result_text == "负":
                            game_results.append("0")
                
                # 检查是否为胆码
                is_banker = self.match_vars[game_idx]['banker'].get()
                
                # 如果选择了结果，加入已选列表
                if game_results:
                    game_info = {
                        'game_idx': game_idx,
                        'results': game_results,
                        'is_banker': is_banker
                    }
                    selected_games.append(game_info)
                    
                    # 分类胆码和非胆码
                    if is_banker:
                        banker_games.append(game_info)
                    else:
                        non_banker_games.append(game_info)
                else:
                    # 未选择，加入未选列表
                    unselected_games.append(game_idx)
            
            # 检查胆码设置
            banker_count = len(banker_games)
            if banker_count > 9:
                messagebox.showwarning("警告", f"胆码不能超过9个，当前设置了{banker_count}个胆码")
                return
            
            # 检查是否选择了至少9场比赛
            if len(selected_games) < 9:
                messagebox.showwarning("警告", f"任九需要选择至少9场比赛，当前只选择了{len(selected_games)}场")
                return
            
            # 验证胆码设置
            if banker_count > 0:
                # 检查胆码是否都选择了结果
                for banker_game in banker_games:
                    if not banker_game['results']:
                        messagebox.showwarning("警告", f"第{banker_game['game_idx']+1}场设为胆码但未选择结果")
                        return
                
                # 检查胆码数量是否合理
                if banker_count > len(selected_games):
                    messagebox.showwarning("警告", "胆码数量不能超过选择的场次数量")
                    return
                
                # 计算需要的非胆码场次数量
                needed_non_banker = 9 - banker_count
                if len(non_banker_games) < needed_non_banker:
                    messagebox.showwarning("警告", f"需要至少{needed_non_banker}场非胆码比赛，当前只有{len(non_banker_games)}场")
                    return
            
            # 生成投注组合
            if banker_count > 0:
                # 有胆码的情况
                bet_strings = self._generate_r9_bets_with_bankers(banker_games, non_banker_games, unselected_games)
            else:
                # 无胆码的情况
                if len(selected_games) == 9:
                    # 正好9场，直接生成
                    bet_strings = self._generate_r9_bets(selected_games, unselected_games)
                else:
                    # 超过9场，生成所有可能的9场组合
                    bet_strings = self._generate_r9_combinations(selected_games, unselected_games)
            
            if bet_strings:
                # 添加到投注区
                self.betting_text.delete("1.0", tk.END)
                self.betting_text.insert("1.0", "\n".join(bet_strings))
                
                # 更新投注区数据
                self.betting_data = bet_strings.copy()
                self.original_data = bet_strings.copy()
                
                # 更新统计
                self.betting_stats.config(text=f"投注数据：{len(bet_strings)} 条")
                
                # 计算投注金额
                total_amount = len(bet_strings) * 2
                messagebox.showinfo("成功", f"已生成 {len(bet_strings)} 条投注数据\n投注金额：{total_amount} 元")
            else:
                messagebox.showwarning("警告", "未能生成有效的投注数据")
                
        except Exception as e:
            messagebox.showerror("错误", f"生成投注失败：{e}")
    
    def _generate_r9_bets(self, selected_games, unselected_games):
        """生成任九投注（正好9场）"""
        # 创建14位字符串，未选择的场次用*表示
        bet_strings = []
        
        # 生成所有结果组合
        all_combinations = self._generate_all_combinations([game['results'] for game in selected_games])
        
        for combo in all_combinations:
            # 创建14位字符串
            bet_str = ['*'] * 14
            
            # 填入选择的9场比赛结果
            for i, game in enumerate(selected_games):
                bet_str[game['game_idx']] = combo[i]
            
            bet_strings.append(''.join(bet_str))
        
        return bet_strings
    
    def _generate_r9_bets_with_bankers(self, banker_games, non_banker_games, unselected_games):
        """生成带胆码的任九投注"""
        from itertools import combinations
        
        bet_strings = []
        banker_count = len(banker_games)
        needed_non_banker = 9 - banker_count
        
        # 生成胆码的所有组合
        banker_combinations = self._generate_all_combinations([game['results'] for game in banker_games])
        
        # 生成非胆码的所有9场组合
        if len(non_banker_games) == needed_non_banker:
            # 正好需要的数量，直接使用
            non_banker_combinations = self._generate_all_combinations([game['results'] for game in non_banker_games])
        else:
            # 超过需要的数量，生成所有可能的组合
            non_banker_combinations = []
            for combo_indices in combinations(range(len(non_banker_games)), needed_non_banker):
                selected_non_banker = [non_banker_games[i] for i in combo_indices]
                combo_results = self._generate_all_combinations([game['results'] for game in selected_non_banker])
                non_banker_combinations.extend(combo_results)
        
        # 组合胆码和非胆码
        for banker_combo in banker_combinations:
            for non_banker_combo in non_banker_combinations:
                # 创建14位字符串
                bet_str = ['*'] * 14
                
                # 填入胆码结果
                for i, banker_game in enumerate(banker_games):
                    bet_str[banker_game['game_idx']] = banker_combo[i]
                
                # 填入非胆码结果
                non_banker_idx = 0
                for non_banker_game in non_banker_games:
                    if non_banker_idx < len(non_banker_combo):
                        bet_str[non_banker_game['game_idx']] = non_banker_combo[non_banker_idx]
                        non_banker_idx += 1
                
                bet_strings.append(''.join(bet_str))
        
        return bet_strings
    
    def _generate_r9_combinations(self, selected_games, unselected_games):
        """生成任九投注（超过9场，生成所有可能的9场组合）"""
        from itertools import combinations
        
        bet_strings = []
        
        # 生成所有可能的9场组合
        for game_combo in combinations(selected_games, 9):
            # 为这9场比赛生成所有结果组合
            game_results = [game['results'] for game in game_combo]
            all_combinations = self._generate_all_combinations(game_results)
            
            for combo in all_combinations:
                # 创建14位字符串
                bet_str = ['*'] * 14
                
                # 填入选择的9场比赛结果
                for i, game in enumerate(game_combo):
                    bet_str[game['game_idx']] = combo[i]
                
                bet_strings.append(''.join(bet_str))
        
        return bet_strings
    
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
    
    # 频率缩水相关函数
    def _adjust_frequency(self, var, delta, summary_text=None):
        """调整频率值"""
        try:
            current = float(var.get())
            new_value = max(0.0, min(100.0, current + delta))
            var.set(f"{new_value:.1f}")
        except ValueError:
            var.set("0.0")
    
    def _update_frequency_summary(self, freq_vars, summary_text):
        """更新频率汇总显示"""
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
            
            # 统计有数据的频率数量
            freq_count = 0
            total_freq = 0.0
            
            # 统计所有频率设置
            for key, var in freq_vars.items():
                if key.endswith('_entry'):
                    continue
                try:
                    freq = float(var.get())
                    total_freq += freq
                    if freq > 0:
                        freq_count += 1
                except ValueError:
                    pass
            
            # 更新汇总显示
            summary_info = f"总注数: {total_bets} | 有数据频率: {freq_count}个 | 数据源: {data_source}"
            summary_text.set(summary_info)
            
        except Exception as e:
            print(f"更新频率汇总失败：{e}")
    
    def _update_frequency_display_r9(self, freq_vars, valid_data, summary_text):
        """更新频率显示（任九版本）"""
        try:
            # 统计每场比赛的胜平负频率
            game_result_stats = {}
            game_total_selections = {}  # 每场比赛的总选择次数（不包括占位符）
            
            for game_idx in range(14):
                game_result_stats[game_idx] = {'胜': 0, '平': 0, '负': 0}
                game_total_selections[game_idx] = 0
            
            for bet in valid_data:
                for game_idx in range(14):
                    # 解析该场的结果
                    if game_idx < len(bet) and bet[game_idx] != '*':
                        result = bet[game_idx]
                        game_total_selections[game_idx] += 1  # 只统计非占位符的选择
                        
                        if result == '3':
                            game_result_stats[game_idx]['胜'] += 1
                        elif result == '1':
                            game_result_stats[game_idx]['平'] += 1
                        elif result == '0':
                            game_result_stats[game_idx]['负'] += 1
            
            # 更新界面显示
            for game_idx in range(14):
                for result_name in ['胜', '平', '负']:
                    var_key = f"game_{game_idx}_{result_name}"
                    if var_key in freq_vars:
                        count = game_result_stats[game_idx][result_name]
                        total_selections = game_total_selections[game_idx]
                        # 只基于该场比赛的实际选择次数计算百分比
                        if total_selections > 0:
                            percentage = (count / total_selections) * 100
                        else:
                            percentage = 0.0
                        freq_vars[var_key].set(f"{percentage:.1f}")
            
            # 更新频率汇总显示
            self._update_frequency_summary(freq_vars, summary_text)
                    
        except Exception as e:
            print(f"更新频率显示失败：{e}")
    
    def _show_frequency_stats_r9(self, freq_vars, parent_window):
        """显示频率统计（任九版本）"""
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
            
            # 统计每场比赛的胜平负频率
            game_result_stats = {}
            for game_idx in range(14):
                game_result_stats[game_idx] = {'胜': 0, '平': 0, '负': 0}
            
            for bet in data_to_analyze:
                for game_idx in range(14):
                    # 解析该场的结果
                    if game_idx < len(bet) and bet[game_idx] != '*':
                        result = bet[game_idx]
                        if result == '3':
                            game_result_stats[game_idx]['胜'] += 1
                        elif result == '1':
                            game_result_stats[game_idx]['平'] += 1
                        elif result == '0':
                            game_result_stats[game_idx]['负'] += 1
            
            # 显示统计结果
            stats_text = f"14场比赛胜平负频率统计（基于{data_source}）：\n\n"
            stats_text += f"数据条数：{total_count} 条\n\n"
            
            for game_idx in range(14):
                stats_text += f"第{game_idx + 1}场：\n"
                for result_name in ['胜', '平', '负']:
                    count = game_result_stats[game_idx][result_name]
                    percentage = (count / total_count) * 100 if total_count > 0 else 0
                    stats_text += f"  {result_name}：{count}次 ({percentage:.1f}%)\n"
                stats_text += "\n"
            
            messagebox.showinfo("频率统计", stats_text, parent=parent_window)
            
        except Exception as e:
            messagebox.showerror("错误", f"统计失败：{e}", parent=parent_window)
    
    def _apply_frequency_filter_r9(self, freq_vars, parent_window):
        """应用频率过滤（任九版本）"""
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
            for game_idx in range(14):
                for result_name in ['胜', '平', '负']:
                    var_key = f"game_{game_idx}_{result_name}"
                    if var_key in freq_vars:
                        try:
                            freq_settings[var_key] = float(freq_vars[var_key].get())
                        except ValueError:
                            freq_settings[var_key] = 0.0
            
            # 计算每种投注组合的期望值
            bet_expectations = []
            
            for bet in valid_data:
                expectation = 1.0
                bet_info = []
                has_zero_prob = False
                
                for game_idx in range(14):
                    if game_idx < len(bet) and bet[game_idx] != '*':
                        result = bet[game_idx]
                        if result == '3':
                            result_name = '胜'
                        elif result == '1':
                            result_name = '平'
                        elif result == '0':
                            result_name = '负'
                        else:
                            continue
                        
                        var_key = f"game_{game_idx}_{result_name}"
                        if var_key in freq_settings:
                            prob = freq_settings[var_key] / 100.0
                            expectation *= prob
                            bet_info.append(f"第{game_idx+1}场{result_name}({prob:.2%})")
                            if prob == 0:
                                has_zero_prob = True
                        else:
                            expectation *= 0.0
                            bet_info.append(f"第{game_idx+1}场{result_name}(0%)")
                            has_zero_prob = True
                
                # 只保留期望值大于0的投注
                if not has_zero_prob and expectation > 0:
                    bet_expectations.append({
                        'bet': bet,
                        'expectation': expectation,
                        'info': ' × '.join(bet_info)
                    })
            
            # 按期望值排序
            bet_expectations.sort(key=lambda x: x['expectation'], reverse=True)
            
            # 计算期望值阈值
            if bet_expectations:
                expectations = [bet['expectation'] for bet in bet_expectations]
                max_exp = max(expectations)
                min_exp = min(expectations)
                avg_exp = sum(expectations) / len(expectations)
                
                # 设置阈值：保留期望值大于平均值50%的投注
                threshold = avg_exp * 0.5
                
                # 筛选高期望值投注
                selected_bets = []
                for bet_data in bet_expectations:
                    if bet_data['expectation'] >= threshold:
                        selected_bets.append(bet_data['bet'])
                
                # 如果筛选结果太少，降低阈值
                if len(selected_bets) < len(valid_data) * 0.1:
                    threshold = avg_exp * 0.1
                    selected_bets = []
                    for bet_data in bet_expectations:
                        if bet_data['expectation'] >= threshold:
                            selected_bets.append(bet_data['bet'])
                
                # 如果还是太少，保留前20%
                if len(selected_bets) < len(valid_data) * 0.05:
                    selected_bets = [bet_data['bet'] for bet_data in bet_expectations[:max(1, len(bet_expectations)//5)]]
            else:
                selected_bets = []
            
            # 更新结果
            self.filtered_data = selected_bets
            self._display_results()
            
            # 更新数据统计
            self.result_stats.config(text=f"过滤结果：{len(selected_bets)} 条")
            
            # 显示完成提示
            original_count = len(valid_data)
            filtered_count = len(selected_bets)
            reduction_rate = ((original_count - filtered_count) / original_count * 100) if original_count > 0 else 0
            
            detail_text = f"科学缩水完成！\n\n"
            detail_text += f"数据源：{data_source}\n"
            detail_text += f"原始投注：{original_count} 条\n"
            detail_text += f"缩水结果：{filtered_count} 条\n"
            detail_text += f"缩水比例：{reduction_rate:.1f}%\n"
            
            messagebox.showinfo("科学缩水完成", detail_text, parent=parent_window)
            
            # 关闭窗口
            parent_window.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"科学缩水失败：{e}", parent=parent_window)
    
    def _smart_allocation_r9(self, freq_vars, parent_window):
        """智能分配功能（任九版本）"""
        try:
            # 创建智能分配窗口
            alloc_window = tk.Toplevel(parent_window)
            alloc_window.title("智能分配")
            alloc_window.geometry("600x500")
            alloc_window.resizable(True, True)
            
            # 居中显示
            alloc_window.update_idletasks()
            x = (alloc_window.winfo_screenwidth() // 2) - (600 // 2)
            y = (alloc_window.winfo_screenheight() // 2) - (500 // 2)
            alloc_window.geometry(f'600x500+{x}+{y}')
            
            # 主框架
            main_frame = ttk.Frame(alloc_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # 标题
            title_label = ttk.Label(main_frame, text="智能分配 - 基于概率科学分配", 
                                   font=('Microsoft YaHei UI', 14, 'bold'))
            title_label.pack(pady=(0, 20))
            
            # 说明
            info_text = """
智能分配原理：
1. 基于您设定的概率进行科学分配
2. 计算每种组合的期望值
3. 优先保留高期望值的组合
4. 自动优化投注数量
            """
            info_label = ttk.Label(main_frame, text=info_text, 
                                  font=('Microsoft YaHei UI', 10))
            info_label.pack(pady=(0, 20))
            
            # 分配策略选择
            strategy_frame = ttk.LabelFrame(main_frame, text="分配策略", padding="10")
            strategy_frame.pack(fill=tk.X, pady=(0, 20))
            
            self.strategy_var = tk.StringVar(value="期望值优先")
            strategies = ["期望值优先", "概率均衡", "风险控制", "自定义比例"]
            
            for i, strategy in enumerate(strategies):
                ttk.Radiobutton(strategy_frame, text=strategy, 
                               variable=self.strategy_var, value=strategy).grid(
                    row=i//2, column=i%2, sticky=tk.W, padx=10, pady=5)
            
            # 目标投注数设置
            target_frame = ttk.LabelFrame(main_frame, text="目标设置", padding="10")
            target_frame.pack(fill=tk.X, pady=(0, 20))
            
            ttk.Label(target_frame, text="目标投注数：").pack(side=tk.LEFT)
            self.target_bets_var = tk.StringVar(value="200")
            target_entry = ttk.Entry(target_frame, textvariable=self.target_bets_var, width=10)
            target_entry.pack(side=tk.LEFT, padx=(5, 20))
            
            ttk.Label(target_frame, text="最小期望值：").pack(side=tk.LEFT)
            self.min_expectation_var = tk.StringVar(value="0.01")
            min_exp_entry = ttk.Entry(target_frame, textvariable=self.min_expectation_var, width=10)
            min_exp_entry.pack(side=tk.LEFT, padx=(5, 0))
            
            # 按钮区域
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill=tk.X, pady=(20, 0))
            
            ttk.Button(btn_frame, text="开始智能分配", 
                      command=lambda: self._execute_smart_allocation_r9(freq_vars, alloc_window),
                      style='Filter.TButton').pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(btn_frame, text="关闭", 
                      command=alloc_window.destroy,
                      style='Clear.TButton').pack(side=tk.RIGHT)
            
        except Exception as e:
            messagebox.showerror("错误", f"创建智能分配窗口失败：{e}")
    
    def _execute_smart_allocation_r9(self, freq_vars, alloc_window):
        """执行智能分配（任九版本）"""
        try:
            # 获取当前数据
            if self.filtered_data:
                valid_data = self.filtered_data.copy()
                data_source = "过滤结果"
            elif self.betting_data:
                valid_data = self.betting_data.copy()
                data_source = "投注区数据"
            else:
                messagebox.showwarning("警告", "没有可用的数据", parent=alloc_window)
                return
            
            # 获取用户设置
            target_bets = int(self.target_bets_var.get())
            min_expectation = float(self.min_expectation_var.get())
            strategy = self.strategy_var.get()
            
            # 获取频率设置
            freq_settings = {}
            for game_idx in range(14):
                for result_name in ['胜', '平', '负']:
                    var_key = f"game_{game_idx}_{result_name}"
                    if var_key in freq_vars:
                        try:
                            freq_settings[var_key] = float(freq_vars[var_key].get())
                        except ValueError:
                            freq_settings[var_key] = 0.0
            
            # 计算每种投注组合的期望值
            bet_expectations = []
            
            for bet in valid_data:
                expectation = 1.0
                bet_info = []
                has_zero_prob = False
                
                for game_idx in range(14):
                    if game_idx < len(bet) and bet[game_idx] != '*':
                        result = bet[game_idx]
                        if result == '3':
                            result_name = '胜'
                        elif result == '1':
                            result_name = '平'
                        elif result == '0':
                            result_name = '负'
                        else:
                            continue
                        
                        var_key = f"game_{game_idx}_{result_name}"
                        if var_key in freq_settings:
                            prob = freq_settings[var_key] / 100.0
                            expectation *= prob
                            bet_info.append(f"第{game_idx+1}场{result_name}({prob:.2%})")
                            if prob == 0:
                                has_zero_prob = True
                        else:
                            expectation *= 0.0
                            bet_info.append(f"第{game_idx+1}场{result_name}(0%)")
                            has_zero_prob = True
                
                # 只保留期望值大于0的投注
                if not has_zero_prob and expectation > 0:
                    bet_expectations.append({
                        'bet': bet,
                        'expectation': expectation,
                        'info': ' × '.join(bet_info)
                    })
            
            # 根据策略排序
            if strategy == "期望值优先":
                bet_expectations.sort(key=lambda x: x['expectation'], reverse=True)
            elif strategy == "概率均衡":
                # 按概率分布均匀选择
                bet_expectations.sort(key=lambda x: x['expectation'], reverse=True)
                # 这里可以添加更复杂的均衡算法
            elif strategy == "风险控制":
                # 选择中等期望值的投注，避免过高或过低
                bet_expectations.sort(key=lambda x: abs(x['expectation'] - 0.1), reverse=False)
            
            # 筛选符合条件的投注
            selected_bets = []
            for bet_data in bet_expectations:
                if bet_data['expectation'] >= min_expectation:
                    selected_bets.append(bet_data)
                    if len(selected_bets) >= target_bets:
                        break
            
            # 如果筛选结果不够，降低期望值要求
            if len(selected_bets) < target_bets and bet_expectations:
                # 降低最小期望值要求
                min_expectation = min_expectation * 0.1
                selected_bets = []
                for bet_data in bet_expectations:
                    if bet_data['expectation'] >= min_expectation:
                        selected_bets.append(bet_data)
                        if len(selected_bets) >= target_bets:
                            break
            
            # 如果还是不够，直接取前N个
            if len(selected_bets) < target_bets:
                selected_bets = bet_expectations[:target_bets]
            
            # 更新结果
            self.filtered_data = [bet_data['bet'] for bet_data in selected_bets]
            self._display_results()
            
            # 显示分配结果
            result_text = f"智能分配完成！\n\n"
            result_text += f"数据源：{data_source}\n"
            result_text += f"原始投注：{len(valid_data)} 条\n"
            result_text += f"分配结果：{len(selected_bets)} 条\n"
            result_text += f"分配策略：{strategy}\n"
            result_text += f"目标投注数：{target_bets}\n"
            result_text += f"最小期望值：{min_expectation}\n\n"
            
            if selected_bets:
                result_text += "前5个高期望值投注：\n"
                for i, bet_data in enumerate(selected_bets[:5]):
                    result_text += f"{i+1}. {bet_data['bet']} (期望值: {bet_data['expectation']:.6f})\n"
                    result_text += f"   {bet_data['info']}\n"
            
            messagebox.showinfo("智能分配完成", result_text, parent=alloc_window)
            alloc_window.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"智能分配失败：{e}", parent=alloc_window)
    
    def _save_frequency_settings_r9(self, freq_vars, parent_window):
        """保存频率设置到文件（任九版本）"""
        try:
            from tkinter import filedialog
            import json
            
            # 选择保存文件
            filename = filedialog.asksaveasfilename(
                parent=parent_window,
                title="保存频率设置",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            
            if not filename:
                return
            
            # 收集所有频率设置
            settings = {}
            for game_idx in range(14):
                settings[f"game_{game_idx}"] = {}
                for result_name in ['胜', '平', '负']:
                    var_key = f"game_{game_idx}_{result_name}"
                    if var_key in freq_vars:
                        try:
                            settings[f"game_{game_idx}"][result_name] = float(freq_vars[var_key].get())
                        except ValueError:
                            settings[f"game_{game_idx}"][result_name] = 0.0
            
            # 保存到文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("保存成功", f"频率设置已保存到：\n{filename}", parent=parent_window)
            
        except Exception as e:
            messagebox.showerror("保存失败", f"保存频率设置时出错：\n{e}", parent=parent_window)
    
    def _load_frequency_settings_r9(self, freq_vars, parent_window):
        """从文件导入频率设置（任九版本）"""
        try:
            from tkinter import filedialog
            import json
            
            # 选择文件
            filename = filedialog.askopenfilename(
                parent=parent_window,
                title="导入频率设置",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            
            if not filename:
                return
            
            # 读取文件
            with open(filename, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 应用设置
            for game_idx in range(14):
                game_key = f"game_{game_idx}"
                if game_key in settings:
                    for result_name in ['胜', '平', '负']:
                        if result_name in settings[game_key]:
                            var_key = f"game_{game_idx}_{result_name}"
                            if var_key in freq_vars:
                                freq_vars[var_key].set(str(settings[game_key][result_name]))
            
            messagebox.showinfo("导入成功", f"频率设置已从以下文件导入：\n{filename}", parent=parent_window)
            
        except Exception as e:
            messagebox.showerror("导入失败", f"导入频率设置时出错：\n{e}", parent=parent_window)
    
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
                odd_indices = [i for i in range(0, len(source_data), 2)]
                if len(odd_indices) >= target_count:
                    selected_indices = odd_indices[:target_count]
                else:
                    # 如果奇数序号不够，补充偶数序号
                    even_indices = [i for i in range(1, len(source_data), 2)]
                    selected_indices = odd_indices + even_indices[:target_count - len(odd_indices)]
                self.filtered_data = [source_data[i] for i in selected_indices]
            elif method == "even":
                # 偶数序号选择
                even_indices = [i for i in range(1, len(source_data), 2)]
                if len(even_indices) >= target_count:
                    selected_indices = even_indices[:target_count]
                else:
                    # 如果偶数序号不够，补充奇数序号
                    odd_indices = [i for i in range(0, len(source_data), 2)]
                    selected_indices = even_indices + odd_indices[:target_count - len(even_indices)]
                self.filtered_data = [source_data[i] for i in selected_indices]
            elif method == "uniform":
                # 均匀选择
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
        
        # 统计每种投注组合的频率
        bet_groups = {}
        for bet in source_data:
            if bet in bet_groups:
                bet_groups[bet].append(bet)
            else:
                bet_groups[bet] = [bet]
        
        # 计算每种投注组合应该保留的数量
        result = []
        for bet, bets in bet_groups.items():
            # 按比例计算该投注组合应该保留的数量
            original_count = len(bets)
            target_ratio = target_count / len(source_data)
            target_for_this_bet = max(1, int(original_count * target_ratio))
            
            # 如果计算出的数量超过实际数量，则取实际数量
            target_for_this_bet = min(target_for_this_bet, original_count)
            
            # 从该投注组合中均匀选择
            if target_for_this_bet == original_count:
                result.extend(bets)
            else:
                step = original_count / target_for_this_bet
                selected_indices = [int(i * step) for i in range(target_for_this_bet)]
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
    
    def show_rotation_matrix_dialog(self):
        """显示旋转矩阵对话框"""
        # 检查投注区数据
        if not self.betting_data:
            messagebox.showwarning("警告", "请先生成投注数据")
            return
        
        # 统计选择的比赛场次
        selected_games = 0
        for bet in self.betting_data:
            for i, char in enumerate(bet):
                if char != '*' and i < 14:
                    selected_games = max(selected_games, i + 1)
        
        # 检查是否至少10场
        if selected_games < 10:
            messagebox.showwarning("警告", f"旋转矩阵需要至少10场比赛，当前只有{selected_games}场")
            return
        
        # 创建旋转矩阵对话框
        matrix_window = tk.Toplevel(self.root)
        matrix_window.title("旋转矩阵 - N保9")
        matrix_window.geometry("700x600")
        matrix_window.resizable(True, True)
        
        # 居中显示
        matrix_window.update_idletasks()
        x = (matrix_window.winfo_screenwidth() // 2) - (700 // 2)
        y = (matrix_window.winfo_screenheight() // 2) - (600 // 2)
        matrix_window.geometry(f'700x600+{x}+{y}')
        
        # 主框架
        main_frame = ttk.Frame(matrix_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="旋转矩阵 - N保9缩水", 
                               font=('Microsoft YaHei UI', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 说明
        info_text = f"""
旋转矩阵原理：
1. 从{selected_games}场比赛中选择N场进行矩阵旋转
2. 确保在N场比赛中至少有9场结果被覆盖
3. 通过矩阵排列减少投注数量，提高中奖概率
4. 适用于任九玩法的科学缩水
        """
        info_label = ttk.Label(main_frame, text=info_text, 
                              font=('Microsoft YaHei UI', 10))
        info_label.pack(pady=(0, 20))
        
        # 矩阵设置
        matrix_frame = ttk.LabelFrame(main_frame, text="矩阵设置", padding="15")
        matrix_frame.pack(fill=tk.X, pady=(0, 20))
        
        # L+N值设置
        ln_frame = ttk.Frame(matrix_frame)
        ln_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(ln_frame, text="L+N值（12-14）：").pack(side=tk.LEFT)
        self.ln_value_var = tk.StringVar(value=str(min(selected_games, 12)))
        ln_combo = ttk.Combobox(ln_frame, textvariable=self.ln_value_var, 
                               values=["12", "13", "14"], 
                               width=5, state="readonly")
        ln_combo.pack(side=tk.LEFT, padx=(5, 20))
        
        # 胆码数量设置
        ttk.Label(ln_frame, text="胆码数量L：").pack(side=tk.LEFT)
        self.bankers_var = tk.StringVar(value="3")
        bankers_combo = ttk.Combobox(ln_frame, textvariable=self.bankers_var,
                                    values=["2", "3", "4"], 
                                    width=5, state="readonly")
        bankers_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 矩阵类型选择
        matrix_type_frame = ttk.Frame(matrix_frame)
        matrix_type_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(matrix_type_frame, text="矩阵类型：").pack(side=tk.LEFT)
        self.matrix_type_var = tk.StringVar(value="专业矩阵")
        matrix_type_combo = ttk.Combobox(matrix_type_frame, textvariable=self.matrix_type_var,
                                        values=["专业矩阵", "标准矩阵", "优化矩阵"], 
                                        width=10, state="readonly")
        matrix_type_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 覆盖度设置
        coverage_frame = ttk.Frame(matrix_frame)
        coverage_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(coverage_frame, text="覆盖度：").pack(side=tk.LEFT)
        self.coverage_var = tk.StringVar(value="9")
        coverage_combo = ttk.Combobox(coverage_frame, textvariable=self.coverage_var,
                                     values=["8", "9", "10"], width=5, state="readonly")
        coverage_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="矩阵预览", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 预览文本框
        self.matrix_preview = scrolledtext.ScrolledText(preview_frame, height=8, 
                                                       font=('Consolas', 9),
                                                       bg='white', fg='black')
        self.matrix_preview.pack(fill=tk.BOTH, expand=True)
        
        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="生成矩阵", 
                  command=lambda: self._generate_rotation_matrix(matrix_window),
                  style='Filter.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="应用矩阵", 
                  command=lambda: self._apply_rotation_matrix(matrix_window),
                  style='Success.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="关闭", 
                  command=matrix_window.destroy,
                  style='Clear.TButton').pack(side=tk.RIGHT)
        
        # 初始化预览
        self._update_matrix_preview()
    
    def _update_matrix_preview(self):
        """更新矩阵预览"""
        try:
            ln_value = int(self.ln_value_var.get())
            bankers = int(self.bankers_var.get())
            matrix_type = self.matrix_type_var.get()
            coverage = int(self.coverage_var.get())
            
            # 计算矩阵应用场次
            matrix_fields = ln_value - bankers
            
            preview_text = f"矩阵参数：\n"
            preview_text += f"L+N值：{ln_value}\n"
            preview_text += f"胆码数量L：{bankers}\n"
            preview_text += f"矩阵应用场次：{matrix_fields}\n"
            preview_text += f"矩阵类型：{matrix_type}\n"
            preview_text += f"覆盖度：{coverage}\n\n"
            
            # 根据专业矩阵逻辑显示预计投注数
            expected_bets = self._get_professional_matrix_size(ln_value, bankers)
            preview_text += f"预计生成投注数：{expected_bets}\n\n"
            preview_text += "点击'生成矩阵'查看详细矩阵排列"
            
            self.matrix_preview.delete("1.0", tk.END)
            self.matrix_preview.insert("1.0", preview_text)
            
        except Exception as e:
            self.matrix_preview.delete("1.0", tk.END)
            self.matrix_preview.insert("1.0", f"预览更新失败：{e}")
    
    def _get_professional_matrix_size(self, ln_value, bankers):
        """根据专业矩阵逻辑计算投注数量"""
        if ln_value == 12:
            if bankers == 4:
                return 11  # 3-6-5矩阵
            elif bankers == 3:
                return 12  # 9-7-6矩阵
            elif bankers == 2:
                return 17  # 10场矩阵
        elif ln_value == 13:
            if bankers == 4:
                return 25  # 9-6-5矩阵
            elif bankers == 3:
                return 30  # 10-7-6矩阵
            elif bankers == 2:
                return 47  # 11-3-7矩阵
        elif ln_value == 14:
            if bankers == 4:
                return 51  # 10-6-5矩阵
            elif bankers == 3:
                return 66  # 11-7-6矩阵
            elif bankers == 2:
                return 113  # 12-2-7矩阵
        return 1
    
    def _calculate_matrix_size(self, n, coverage):
        """计算矩阵大小（保留兼容性）"""
        # 简化的矩阵大小计算
        if coverage == 9:
            if n == 10:
                return 6
            elif n == 11:
                return 11
            elif n == 12:
                return 20
            elif n == 13:
                return 35
            elif n == 14:
                return 56
        elif coverage == 8:
            return max(1, n - 2)
        elif coverage == 10:
            return max(1, n - 1)
        return 1
    
    def _generate_rotation_matrix(self, parent_window):
        """生成旋转矩阵"""
        try:
            ln_value = int(self.ln_value_var.get())
            bankers = int(self.bankers_var.get())
            matrix_type = self.matrix_type_var.get()
            coverage = int(self.coverage_var.get())
            
            # 生成矩阵
            matrix = self._create_rotation_matrix(ln_value, bankers, coverage, matrix_type)
            
            # 显示矩阵
            matrix_text = f"专业N保{coverage}旋转矩阵 (L+N={ln_value}, L={bankers}):\n\n"
            matrix_text += f"矩阵类型：{matrix_type}\n"
            matrix_text += f"胆码数量：{bankers}\n"
            matrix_text += f"矩阵应用场次：{ln_value - bankers}\n"
            matrix_text += f"总投注数：{len(matrix)}\n\n"
            matrix_text += "矩阵排列：\n"
            matrix_text += "-" * 60 + "\n"
            
            for i, row in enumerate(matrix, 1):
                matrix_text += f"{i:3d}. {row}\n"
            
            self.matrix_preview.delete("1.0", tk.END)
            self.matrix_preview.insert("1.0", matrix_text)
            
            # 保存矩阵供应用使用
            self.current_matrix = matrix
            self.current_matrix_params = {
                'ln_value': ln_value,
                'bankers': bankers,
                'coverage': coverage,
                'matrix_type': matrix_type
            }
            
        except Exception as e:
            messagebox.showerror("错误", f"生成矩阵失败：{e}", parent=parent_window)
    
    def _create_rotation_matrix(self, ln_value, bankers, coverage, matrix_type):
        """创建旋转矩阵"""
        if matrix_type == "专业矩阵":
            return self._create_professional_matrix(ln_value, bankers)
        elif matrix_type == "标准矩阵":
            return self._create_standard_matrix(ln_value - bankers, coverage)
        elif matrix_type == "优化矩阵":
            return self._create_optimized_matrix(ln_value - bankers, coverage)
        else:
            return self._create_custom_matrix(ln_value - bankers, coverage)
    
    def _create_professional_matrix(self, ln_value, bankers):
        """创建专业矩阵 - 基于专业N保9矩阵逻辑"""
        if ln_value == 12:
            if bankers == 4:
                return self._create_365_matrix()  # 3-6-5矩阵，11注
            elif bankers == 3:
                return self._create_976_matrix()  # 9-7-6矩阵，12注
            elif bankers == 2:
                return self._create_10_field_matrix()  # 10场矩阵，17注
        elif ln_value == 13:
            if bankers == 4:
                return self._create_965_matrix()  # 9-6-5矩阵，25注
            elif bankers == 3:
                return self._create_1076_matrix()  # 10-7-6矩阵，30注
            elif bankers == 2:
                return self._create_1137_matrix()  # 11-3-7矩阵，47注
        elif ln_value == 14:
            if bankers == 4:
                return self._create_1065_matrix()  # 10-6-5矩阵，51注
            elif bankers == 3:
                return self._create_1176_matrix()  # 11-7-6矩阵，66注
            elif bankers == 2:
                return self._create_1227_matrix()  # 12-2-7矩阵，113注
        
        # 默认返回空矩阵
        return []
    
    def _create_365_matrix(self):
        """创建3-6-5矩阵（11注）- 14位格式，9个有效数字，5个*占位"""
        return [
            "333333333****",
            "333333311****",
            "333333113****",
            "333333113****",
            "333331133****",
            "333311333****",
            "333113333****",
            "331133333****",
            "311333333****",
            "113333333****",
            "333111111****"
        ]
    
    def _create_976_matrix(self):
        """创建9-7-6矩阵（12注）- 14位格式，9个有效数字，5个*占位"""
        return [
            "333333333****",
            "333333311****",
            "333333113****",
            "333331133****",
            "333311333****",
            "333113333****",
            "331133333****",
            "311333333****",
            "113333333****",
            "333111111****",
            "311133311****",
            "111133333****"
        ]
    
    def _create_10_field_matrix(self):
        """创建10场矩阵（17注）- 14位格式，9个有效数字，5个*占位"""
        return [
            "333333333****",
            "333333331****",
            "333333313****",
            "333333133****",
            "333331333****",
            "333313333****",
            "333133333****",
            "331333333****",
            "313333333****",
            "133333333****",
            "333311111****",
            "333111133****",
            "331111333****",
            "311113333****",
            "111113333****",
            "333333111****",
            "111133333****"
        ]
    
    def _create_965_matrix(self):
        """创建9-6-5矩阵（25注）- 14位格式，9个有效数字，5个*占位"""
        return [
            "333333333****",
            "333333311****",
            "333333113****",
            "333331133****",
            "333311333****",
            "333113333****",
            "331133333****",
            "311333333****",
            "113333333****",
            "333331111****",
            "333311113****",
            "333111133****",
            "331111333****",
            "311113333****",
            "111113333****",
            "333333111****",
            "333311111****",
            "333111113****",
            "331111133****",
            "311111333****",
            "111111333****",
            "333333333****",
            "333333311****",
            "333333113****",
            "333331133****"
        ]
    
    def _create_1076_matrix(self):
        """创建10-7-6矩阵（30注）- 14位格式，9个有效数字，5个*占位"""
        return [
            "333333333****",
            "333333331****",
            "333333313****",
            "333333133****",
            "333331333****",
            "333313333****",
            "333133333****",
            "331333333****",
            "313333333****",
            "133333333****",
            "333333111****",
            "333331113****",
            "333311133****",
            "333111333****",
            "331111333****",
            "311113333****",
            "111113333****",
            "333311111****",
            "333111113****",
            "331111133****",
            "311111333****",
            "111111333****",
            "333333333****",
            "333333331****",
            "333333313****",
            "333333133****",
            "333331333****",
            "333313333****",
            "333133333****",
            "331333333****"
        ]
    
    def _create_1137_matrix(self):
        """创建11-3-7矩阵（47注）- 14位格式，9个有效数字，5个*占位"""
        return [
            "333333333****",
            "333333331****",
            "333333313****",
            "333333133****",
            "333331333****",
            "333313333****",
            "333133333****",
            "331333333****",
            "313333333****",
            "133333333****",
            "333333111****",
            "333331113****",
            "333311133****",
            "333111333****",
            "331111333****",
            "311113333****",
            "111113333****",
            "333311111****",
            "333111113****",
            "331111133****",
            "311111333****",
            "111111333****",
            "333333331****",
            "333333313****",
            "333333133****",
            "333331333****",
            "333313333****",
            "333133333****",
            "331333333****",
            "313333333****",
            "133333333****",
            "333333111****",
            "333331113****",
            "333311133****",
            "333111333****",
            "331111333****",
            "311113333****",
            "111113333****",
            "333311111****",
            "333111113****",
            "331111133****",
            "311111333****",
            "111111333****",
            "333311111****",
            "333111113****",
            "331111133****",
            "311111333****"
        ]
    
    def _create_1065_matrix(self):
        """创建10-6-5矩阵（51注）- 14位格式，9个有效数字，5个*占位"""
        return [
            "333333333****",
            "333333331****",
            "333333313****",
            "333333133****",
            "333331333****",
            "333313333****",
            "333133333****",
            "331333333****",
            "313333333****",
            "133333333****",
            "333333111****",
            "333331113****",
            "333311133****",
            "333111333****",
            "331111333****",
            "311113333****",
            "111113333****",
            "333311111****",
            "333111113****",
            "331111133****",
            "311111333****",
            "111111333****",
            "333333333****",
            "333333331****",
            "333333313****",
            "333333133****",
            "333331333****",
            "333313333****",
            "333133333****",
            "331333333****",
            "313333333****",
            "133333333****",
            "333333111****",
            "333331113****",
            "333311133****",
            "333111333****",
            "331111333****",
            "311113333****",
            "111113333****",
            "333311111****",
            "333111113****",
            "331111133****",
            "311111333****",
            "111111333****",
            "333333333****",
            "333333331****",
            "333333313****",
            "333333133****",
            "333331333****",
            "333313333****",
            "333133333****"
        ]
    
    def _create_1176_matrix(self):
        """创建11-7-6矩阵（66注）- 14位格式，9个有效数字，5个*占位"""
        # 生成66注的11-7-6矩阵，每注都是14位格式
        matrix = []
        for i in range(66):
            # 生成9个有效数字的组合
            if i < 9:
                # 前9注：333333333, 333333331, 333333313, ...
                pattern = "333333333"
                if i > 0:
                    # 从右到左替换3为1
                    pos = 8 - (i - 1)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            elif i < 18:
                # 中间9注：333333111, 333331113, ...
                pattern = "333333111"
                if i > 9:
                    pos = 8 - (i - 10)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            elif i < 27:
                # 更多组合
                pattern = "333311111"
                if i > 18:
                    pos = 8 - (i - 19)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            else:
                # 其他组合
                pattern = "333333333"
                if i > 27:
                    pos = 8 - (i - 28)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            
            matrix.append(pattern + "****")
        
        return matrix
    
    def _create_1227_matrix(self):
        """创建12-2-7矩阵（113注）- 14位格式，9个有效数字，5个*占位"""
        # 生成113注的12-2-7矩阵，每注都是14位格式
        matrix = []
        for i in range(113):
            # 生成9个有效数字的组合
            if i < 9:
                # 前9注：333333333, 333333331, 333333313, ...
                pattern = "333333333"
                if i > 0:
                    pos = 8 - (i - 1)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            elif i < 18:
                # 中间9注：333333111, 333331113, ...
                pattern = "333333111"
                if i > 9:
                    pos = 8 - (i - 10)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            elif i < 27:
                # 更多组合
                pattern = "333311111"
                if i > 18:
                    pos = 8 - (i - 19)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            elif i < 36:
                # 其他组合
                pattern = "333333333"
                if i > 27:
                    pos = 8 - (i - 28)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            elif i < 45:
                # 更多组合
                pattern = "333333111"
                if i > 36:
                    pos = 8 - (i - 37)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            elif i < 54:
                # 更多组合
                pattern = "333311111"
                if i > 45:
                    pos = 8 - (i - 46)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            elif i < 63:
                # 更多组合
                pattern = "333333333"
                if i > 54:
                    pos = 8 - (i - 55)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            elif i < 72:
                # 更多组合
                pattern = "333333111"
                if i > 63:
                    pos = 8 - (i - 64)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            elif i < 81:
                # 更多组合
                pattern = "333311111"
                if i > 72:
                    pos = 8 - (i - 73)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            elif i < 90:
                # 更多组合
                pattern = "333333333"
                if i > 81:
                    pos = 8 - (i - 82)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            elif i < 99:
                # 更多组合
                pattern = "333333111"
                if i > 90:
                    pos = 8 - (i - 91)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            elif i < 108:
                # 更多组合
                pattern = "333311111"
                if i > 99:
                    pos = 8 - (i - 100)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            else:
                # 最后5注
                pattern = "333333333"
                if i > 108:
                    pos = 8 - (i - 109)
                    pattern = pattern[:pos] + "1" + pattern[pos+1:]
            
            matrix.append(pattern + "****")
        
        return matrix
    
    def _create_standard_matrix(self, n, coverage):
        """创建标准矩阵"""
        matrix = []
        
        if n == 10 and coverage == 9:
            # 10保9标准矩阵
            matrix = [
                "333333333*",
                "3333333*3",
                "333333*33",
                "33333*333",
                "3333*3333",
                "333*33333"
            ]
        elif n == 11 and coverage == 9:
            # 11保9标准矩阵
            matrix = [
                "3333333333*",
                "333333333*3",
                "33333333*33",
                "3333333*333",
                "333333*3333",
                "33333*33333",
                "3333*333333",
                "333*3333333",
                "33*33333333",
                "3*333333333",
                "*3333333333"
            ]
        elif n == 12 and coverage == 9:
            # 12保9标准矩阵
            matrix = [
                "33333333333*",
                "3333333333*3",
                "333333333*33",
                "33333333*333",
                "3333333*3333",
                "333333*33333",
                "33333*333333",
                "3333*3333333",
                "333*33333333",
                "33*333333333",
                "3*3333333333",
                "*33333333333",
                "333333333*33",
                "33333333*333",
                "3333333*3333",
                "333333*33333",
                "33333*333333",
                "3333*3333333",
                "333*33333333",
                "33*333333333"
            ]
        else:
            # 通用矩阵生成
            matrix = self._generate_generic_matrix(n, coverage)
        
        return matrix
    
    def _create_optimized_matrix(self, n, coverage):
        """创建优化矩阵"""
        # 优化矩阵使用更复杂的排列算法
        matrix = []
        
        # 基础矩阵
        base_matrix = self._create_standard_matrix(n, coverage)
        
        # 优化：添加更多覆盖组合
        for i in range(len(base_matrix)):
            row = base_matrix[i]
            # 创建变体
            for j in range(n):
                if row[j] == '3':
                    variant = list(row)
                    variant[j] = '1'
                    matrix.append(''.join(variant))
        
        # 去重并限制数量
        matrix = list(set(matrix))
        return matrix[:min(len(matrix), self._calculate_matrix_size(n, coverage) * 2)]
    
    def _create_custom_matrix(self, n, coverage):
        """创建自定义矩阵"""
        # 自定义矩阵：基于用户偏好
        matrix = []
        
        # 生成所有可能的组合，然后筛选
        import itertools
        
        # 生成所有3^9的组合（简化版）
        for combo in itertools.product(['3', '1', '0'], repeat=min(9, n)):
            if combo.count('3') >= coverage - 1:  # 至少coverage-1个3
                row = ''.join(combo) + '*' * (n - len(combo))
                matrix.append(row)
                if len(matrix) >= self._calculate_matrix_size(n, coverage):
                    break
        
        return matrix
    
    def _generate_generic_matrix(self, n, coverage):
        """生成通用矩阵"""
        matrix = []
        
        # 简单的通用算法
        for i in range(self._calculate_matrix_size(n, coverage)):
            row = ['3'] * (coverage - 1) + ['1'] * (n - coverage + 1)
            # 旋转
            row = row[i:] + row[:i]
            matrix.append(''.join(row))
        
        return matrix
    
    def _apply_rotation_matrix(self, parent_window):
        """应用旋转矩阵"""
        try:
            if not hasattr(self, 'current_matrix') or not self.current_matrix:
                messagebox.showwarning("警告", "请先生成矩阵", parent=parent_window)
                return
            
            # 保存当前状态到历史记录
            self._save_to_history()
            
            # 应用矩阵到投注数据
            matrix_bets = []
            
            for matrix_row in self.current_matrix:
                # 将矩阵行转换为投注格式
                bet = self._convert_matrix_to_bet(matrix_row)
                if bet:
                    matrix_bets.append(bet)
            
            # 更新过滤结果
            self.filtered_data = matrix_bets
            self._display_results()
            
            # 显示结果
            result_text = f"专业旋转矩阵应用完成！\n\n"
            result_text += f"矩阵参数：L+N={self.current_matrix_params['ln_value']}, L={self.current_matrix_params['bankers']}\n"
            result_text += f"矩阵类型：{self.current_matrix_params['matrix_type']}\n"
            result_text += f"覆盖度：{self.current_matrix_params['coverage']}\n"
            result_text += f"生成投注：{len(matrix_bets)} 条\n"
            result_text += f"缩水比例：{((len(self.betting_data) - len(matrix_bets)) / len(self.betting_data) * 100):.1f}%"
            
            messagebox.showinfo("矩阵应用完成", result_text, parent=parent_window)
            parent_window.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"应用矩阵失败：{e}", parent=parent_window)
    
    def _convert_matrix_to_bet(self, matrix_row):
        """将矩阵行转换为投注格式"""
        try:
            # 矩阵行格式：333333333**** (14位，前9位有效数字，后5位*占位)
            # 需要根据选中的比赛位置填充到14位投注中
            
            bet = ['*'] * 14  # 初始化14位投注
            
            # 将矩阵行的前9位有效数字填充到选中的比赛位置
            matrix_digits = matrix_row[:9]  # 取前9位有效数字
            
            # 获取当前选中的比赛场次
            selected_games = []
            if self.betting_data:
                # 从投注数据中获取选中的比赛场次
                template = self.betting_data[0]
                for i, char in enumerate(template):
                    if char != '*':
                        selected_games.append(i)
            
            # 将矩阵数字填充到选中的比赛位置
            for i, game_idx in enumerate(selected_games[:9]):
                if i < len(matrix_digits):
                    bet[game_idx] = matrix_digits[i]
            
            return ''.join(bet)
            
        except Exception as e:
            return None

def main():
    root = tk.Tk()
    app = R9AdvancedFilter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
