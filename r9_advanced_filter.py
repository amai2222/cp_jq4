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
        # 胜平负过滤区域
        wdl_frame = ttk.LabelFrame(parent, text="胜平负过滤", padding="10", style='Card.TLabelframe')
        wdl_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 添加说明文字
        info_label = ttk.Label(wdl_frame, text="说明：勾选任意选项即启用该场过滤，支持多选", 
                              style='Info.TLabel')
        info_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 14场比赛的胜平负设置
        self.wdl_vars = {}
        
        for i in range(14):
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
        
        # 14场比赛的大小球设置
        self.ou_vars = {}
        
        for i in range(14):
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
        # 解析投注数据（14位数字，每位代表一场比赛的胜平负结果）
        results = []
        for i in range(14):
            result = int(bet[i])
            results.append(result)
        
        # 检查胜平负过滤
        for i in range(14):
            # 检查是否有任何胜平负选项被选中
            wdl_selected = any(self.wdl_vars[i][result].get() for result in ['胜', '平', '负'])
            if wdl_selected:  # 如果有选项被选中
                # 将数字结果转换为文字
                if results[i] == 3:
                    result_text = "胜"
                elif results[i] == 1:
                    result_text = "平"
                else:  # results[i] == 0
                    result_text = "负"
                
                # 检查结果是否在选中的选项中
                if not self.wdl_vars[i][result_text].get():
                    return False
        
        # 检查大小球过滤（这里需要根据实际需求实现）
        # 暂时跳过大小球过滤，因为任九主要是胜平负
        for i in range(14):
            ou_condition = self.ou_vars[i].get()
            if ou_condition != "任意":  # 如果选择了具体的大小球条件
                # 这里需要根据实际需求实现大小球判断逻辑
                # 暂时跳过
                pass
        
        return True
    
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
        for i in range(14):
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
            messagebox.showwarning("警告", "请先加载数据到投注区并进行过滤")
            return
        
        messagebox.showinfo("提示", "比分频率缩水功能正在开发中...")
    
    def show_free_shrink_dialog(self):
        """显示自由缩水对话框"""
        # 优先检查过滤结果区，如果为空则检查投注区
        if not self.filtered_data and not self.betting_data:
            messagebox.showwarning("警告", "请先加载数据到投注区并进行过滤")
            return
        
        messagebox.showinfo("提示", "自由缩水功能正在开发中...")
    
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
                
                # 如果选择了结果，加入已选列表
                if game_results:
                    selected_games.append({
                        'game_idx': game_idx,
                        'results': game_results
                    })
                else:
                    # 未选择，加入未选列表
                    unselected_games.append(game_idx)
            
            # 检查是否选择了至少9场比赛
            if len(selected_games) < 9:
                messagebox.showwarning("警告", f"任九需要选择至少9场比赛，当前只选择了{len(selected_games)}场")
                return
            
            # 如果选择了超过9场，需要用户确认
            if len(selected_games) > 9:
                result = messagebox.askyesno("确认", f"您选择了{len(selected_games)}场比赛，任九只需要9场。是否继续生成投注？\n（将生成所有可能的9场组合）")
                if not result:
                    return
            
            # 生成投注组合
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

def main():
    root = tk.Tk()
    app = R9AdvancedFilter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
