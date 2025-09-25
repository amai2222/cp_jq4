"""
14场胜负彩缩水工具
支持自动获取期号对阵、投注选择、缩水过滤、旋转矩阵
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import itertools
from common_api import LotteryAPI, ShrinkAlgorithm, WheelMatrix, ThreadManager, UIHelper

class SFCShrinkTool:
    def __init__(self, root):
        self.root = root
        self.root.title("14场胜负彩专业缩水工具 V1.0")
        self.root.geometry("1400x1000")
        self.root.minsize(1200, 800)
        
        # 初始化API
        self.api = LotteryAPI()
        
        # 数据存储
        self.current_draw_data = None
        self.original_bets = []
        self.filtered_bets = []
        self.wheeled_bets = []
        
        # UI变量
        self.match_vars = [[tk.IntVar(value=0) for _ in range(3)] for _ in range(14)]  # 14场，每场3个选项(3,1,0)
        self.draw_id_var = tk.StringVar()
        self.status_var = tk.StringVar(value="欢迎使用14场胜负彩缩水工具")
        
        # 过滤条件变量
        self.filter_vars = {
            'min_wins': tk.StringVar(),
            'max_wins': tk.StringVar(),
            'min_draws': tk.StringVar(),
            'max_draws': tk.StringVar(),
            'min_loses': tk.StringVar(),
            'max_loses': tk.StringVar(),
            'min_points': tk.StringVar(),
            'max_points': tk.StringVar(),
            'min_breaks': tk.StringVar(),
            'max_breaks': tk.StringVar(),
            'min_consecutive_wins': tk.StringVar(),
            'max_consecutive_wins': tk.StringVar(),
            'min_consecutive_draws': tk.StringVar(),
            'max_consecutive_draws': tk.StringVar(),
            'min_consecutive_loses': tk.StringVar(),
            'max_consecutive_loses': tk.StringVar(),
            'min_blocks': tk.StringVar(),
            'max_blocks': tk.StringVar()
        }
        
        self._create_widgets()
        self._setup_styles()
        
        # 自动加载最新期号
        self.root.after(100, self.refresh_draw_list)
    
    def _setup_styles(self):
        """设置样式"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 配置样式
        self.style.configure('Title.TLabel', font=('Microsoft YaHei UI', 14, 'bold'))
        self.style.configure('Header.TLabel', font=('Microsoft YaHei UI', 12, 'bold'))
        self.style.configure('Success.TButton', foreground='white', background='#28a745')
        self.style.configure('Warning.TButton', foreground='white', background='#ffc107')
        self.style.configure('Danger.TButton', foreground='white', background='#dc3545')
        
        self.style.map('Success.TButton', background=[('active', '#218838')])
        self.style.map('Warning.TButton', background=[('active', '#e0a800')])
        self.style.map('Danger.TButton', background=[('active', '#c82333')])
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="14场胜负彩专业缩水工具", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # 创建四个主要区域
        self._create_data_area(main_frame)
        self._create_betting_area(main_frame)
        self._create_shrink_area(main_frame)
        self._create_result_area(main_frame)
        
        # 状态栏
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=(10, 0))
        
        # 进度条
        self.progress_bar = ttk.Progressbar(main_frame, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
    
    def _create_data_area(self, parent):
        """创建数据获取区域"""
        data_frame = ttk.LabelFrame(parent, text="① 数据获取", padding="10")
        data_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 期号选择
        period_frame = ttk.Frame(data_frame)
        period_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(period_frame, text="期号:", style='Header.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        self.draw_id_combo = ttk.Combobox(period_frame, textvariable=self.draw_id_var, width=15, state='readonly')
        self.draw_id_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.draw_id_combo.bind('<<ComboboxSelected>>', self.on_draw_selected)
        
        ttk.Button(period_frame, text="刷新期号", command=self.refresh_draw_list).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(period_frame, text="获取详情", command=self.fetch_draw_details).pack(side=tk.LEFT)
        
        # 对阵信息显示
        self.match_info_text = scrolledtext.ScrolledText(data_frame, height=8, wrap=tk.WORD, state='disabled')
        self.match_info_text.pack(fill=tk.X, pady=(10, 0))
    
    def _create_betting_area(self, parent):
        """创建投注选择区域"""
        betting_frame = ttk.LabelFrame(parent, text="② 投注选择", padding="10")
        betting_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 投注表格
        table_frame = ttk.Frame(betting_frame)
        table_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 表头
        headers = ["场次", "主队", "客队", "3", "1", "0"]
        for col, header in enumerate(headers):
            ttk.Label(table_frame, text=header, style='Header.TLabel').grid(row=0, column=col, padx=3, pady=5, sticky='ew')
        
        # 投注选项
        self.match_labels = []
        for i in range(14):
            # 场次号
            ttk.Label(table_frame, text=f"第{i+1:02d}场").grid(row=i+1, column=0, padx=3, pady=3)
            
            # 队伍名称（占位）
            ttk.Label(table_frame, text="主队", width=15).grid(row=i+1, column=1, padx=3, pady=3)
            ttk.Label(table_frame, text="客队", width=15).grid(row=i+1, column=2, padx=3, pady=3)
            
            # 投注选项
            for j in range(3):
                cb = ttk.Checkbutton(table_frame, variable=self.match_vars[i][j])
                cb.grid(row=i+1, column=j+3, padx=3, pady=3)
        
        # 投注信息
        info_frame = ttk.Frame(betting_frame)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.bet_info_label = ttk.Label(info_frame, text="请选择投注选项", foreground="blue")
        self.bet_info_label.pack(side=tk.LEFT)
        
        ttk.Button(info_frame, text="计算投注", command=self.calculate_bets, style='Success.TButton').pack(side=tk.RIGHT)
    
    def _create_shrink_area(self, parent):
        """创建缩水区域"""
        shrink_frame = ttk.LabelFrame(parent, text="③ 缩水过滤", padding="10")
        shrink_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建标签页
        notebook = ttk.Notebook(shrink_frame)
        notebook.pack(fill=tk.X, pady=(0, 10))
        
        # 基础过滤标签页
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="基础过滤")
        
        # 第一行过滤条件
        row1 = ttk.Frame(basic_frame)
        row1.pack(fill=tk.X, pady=5)
        
        ttk.Label(row1, text="胜场数:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(row1, textvariable=self.filter_vars['min_wins'], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(row1, text="≤").pack(side=tk.LEFT, padx=2)
        ttk.Entry(row1, textvariable=self.filter_vars['max_wins'], width=5).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(row1, text="平场数:").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Entry(row1, textvariable=self.filter_vars['min_draws'], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(row1, text="≤").pack(side=tk.LEFT, padx=2)
        ttk.Entry(row1, textvariable=self.filter_vars['max_draws'], width=5).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(row1, text="负场数:").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Entry(row1, textvariable=self.filter_vars['min_loses'], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(row1, text="≤").pack(side=tk.LEFT, padx=2)
        ttk.Entry(row1, textvariable=self.filter_vars['max_loses'], width=5).pack(side=tk.LEFT, padx=2)
        
        # 第二行过滤条件
        row2 = ttk.Frame(basic_frame)
        row2.pack(fill=tk.X, pady=5)
        
        ttk.Label(row2, text="积分和:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(row2, textvariable=self.filter_vars['min_points'], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(row2, text="≤").pack(side=tk.LEFT, padx=2)
        ttk.Entry(row2, textvariable=self.filter_vars['max_points'], width=5).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(row2, text="断点数:").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Entry(row2, textvariable=self.filter_vars['min_breaks'], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(row2, text="≤").pack(side=tk.LEFT, padx=2)
        ttk.Entry(row2, textvariable=self.filter_vars['max_breaks'], width=5).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(row2, text="连号个数:").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Entry(row2, textvariable=self.filter_vars['min_blocks'], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(row2, text="≤").pack(side=tk.LEFT, padx=2)
        ttk.Entry(row2, textvariable=self.filter_vars['max_blocks'], width=5).pack(side=tk.LEFT, padx=2)
        
        # 高级过滤标签页
        advanced_frame = ttk.Frame(notebook, padding="10")
        notebook.add(advanced_frame, text="高级过滤")
        
        # 连续过滤条件
        row3 = ttk.Frame(advanced_frame)
        row3.pack(fill=tk.X, pady=5)
        
        ttk.Label(row3, text="连续胜场:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(row3, textvariable=self.filter_vars['min_consecutive_wins'], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(row3, text="≤").pack(side=tk.LEFT, padx=2)
        ttk.Entry(row3, textvariable=self.filter_vars['max_consecutive_wins'], width=5).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(row3, text="连续平场:").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Entry(row3, textvariable=self.filter_vars['min_consecutive_draws'], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(row3, text="≤").pack(side=tk.LEFT, padx=2)
        ttk.Entry(row3, textvariable=self.filter_vars['max_consecutive_draws'], width=5).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(row3, text="连续负场:").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Entry(row3, textvariable=self.filter_vars['min_consecutive_loses'], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(row3, text="≤").pack(side=tk.LEFT, padx=2)
        ttk.Entry(row3, textvariable=self.filter_vars['max_consecutive_loses'], width=5).pack(side=tk.LEFT, padx=2)
        
        # 缩水按钮
        button_frame = ttk.Frame(shrink_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="开始缩水", command=self.start_shrink, style='Warning.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="旋转矩阵(保8)", command=self.start_wheel, style='Danger.TButton').pack(side=tk.LEFT)
    
    def _create_result_area(self, parent):
        """创建结果显示区域"""
        result_frame = ttk.LabelFrame(parent, text="④ 结果展示", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 结果统计
        stats_frame = ttk.Frame(result_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_label = ttk.Label(stats_frame, text="", style='Header.TLabel')
        self.stats_label.pack(side=tk.LEFT)
        
        # 结果文本
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, state='disabled', height=15)
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 操作按钮
        action_frame = ttk.Frame(result_frame)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="导出结果", command=self.export_results).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="复制到剪贴板", command=self.copy_results).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="清空所有", command=self.clear_all).pack(side=tk.RIGHT)
    
    def refresh_draw_list(self):
        """刷新期号列表"""
        def worker():
            UIHelper.show_progress(self, "正在获取期号列表...")
            result = self.api.get_draw_list('sfc', 10)
            
            def update_ui():
                UIHelper.hide_progress(self)
                if result['success']:
                    self.draw_id_combo['values'] = result['ids']
                    if result['default_id']:
                        self.draw_id_var.set(result['default_id'])
                        self.fetch_draw_details()
                    self.status_var.set("期号列表获取成功")
                else:
                    UIHelper.show_error(self, "错误", result['message'])
                    self.status_var.set("期号列表获取失败")
            
            self.root.after(0, update_ui)
        
        ThreadManager.run_in_thread(worker)
    
    def on_draw_selected(self, event=None):
        """期号选择事件"""
        self.fetch_draw_details()
    
    def fetch_draw_details(self):
        """获取开奖详情"""
        draw_id = self.draw_id_var.get()
        if not draw_id:
            return
        
        def worker():
            UIHelper.show_progress(self, f"正在获取第{draw_id}期详情...")
            result = self.api.get_draw_details('sfc', draw_id)
            
            def update_ui():
                UIHelper.hide_progress(self)
                self.current_draw_data = result
                
                if result['status'] == 'error':
                    UIHelper.show_error(self, "错误", result['message'])
                    self.status_var.set("详情获取失败")
                    return
                
                # 更新对阵信息
                self._update_match_info(result)
                self.status_var.set(f"第{draw_id}期详情获取成功")
            
            self.root.after(0, update_ui)
        
        ThreadManager.run_in_thread(worker)
    
    def _update_match_info(self, data):
        """更新对阵信息显示"""
        self.match_info_text.config(state='normal')
        self.match_info_text.delete('1.0', tk.END)
        
        if data['status'] == 'drawn':
            self.match_info_text.insert(tk.END, f"第{data['draw_id']}期已开奖\n")
            self.match_info_text.insert(tk.END, f"开奖时间: {data['draw_time']}\n")
            self.match_info_text.insert(tk.END, f"开奖号码: {data['numbers']}\n\n")
        else:
            self.match_info_text.insert(tk.END, f"第{data['draw_id']}期尚未开奖\n")
            self.match_info_text.insert(tk.END, f"销售截止: {data.get('message', '未知')}\n\n")
        
        # 显示对阵信息
        matches = data.get('matches', [])
        if matches:
            self.match_info_text.insert(tk.END, "对阵信息:\n")
            for i, match in enumerate(matches[:14]):  # 显示前14场
                home = match.get('masterTeamName', '主队')
                away = match.get('guestTeamName', '客队')
                result = match.get('result', '未开奖')
                self.match_info_text.insert(tk.END, f"第{i+1:02d}场: {home} vs {away} - {result}\n")
        
        self.match_info_text.config(state='disabled')
    
    def calculate_bets(self):
        """计算投注组合"""
        # 检查选择
        selected_matches = []
        
        for i in range(14):
            options = []
            for j in range(3):
                if self.match_vars[i][j].get():
                    options.append(['3', '1', '0'][j])
            
            if not options:
                UIHelper.show_error(self, "错误", f"第{i+1}场必须选择至少一个选项")
                return
            
            selected_matches.append(options)
        
        # 生成所有组合
        self.original_bets = []
        for combo in itertools.product(*selected_matches):
            self.original_bets.append(''.join(combo))
        
        # 更新显示
        total_bets = len(self.original_bets)
        self.bet_info_label.config(text=f"共生成 {total_bets} 注投注")
        self.status_var.set(f"投注计算完成，共 {total_bets} 注")
        
        # 显示结果
        self._display_results(self.original_bets, "原始投注")
    
    def start_shrink(self):
        """开始缩水"""
        if not self.original_bets:
            UIHelper.show_error(self, "错误", "请先计算投注")
            return
        
        def worker():
            UIHelper.show_progress(self, "正在应用过滤条件...")
            
            # 获取过滤条件
            filters = {}
            try:
                for key, var in self.filter_vars.items():
                    if var.get():
                        filters[key] = int(var.get())
            except ValueError:
                def show_error():
                    UIHelper.hide_progress(self)
                    UIHelper.show_error(self, "错误", "过滤条件必须是数字")
                self.root.after(0, show_error)
                return
            
            # 应用过滤
            self.filtered_bets = self._apply_sfc_filters(self.original_bets, filters)
            
            def update_ui():
                UIHelper.hide_progress(self)
                original_count = len(self.original_bets)
                filtered_count = len(self.filtered_bets)
                self.status_var.set(f"缩水完成: {original_count} → {filtered_count} 注")
                self._display_results(self.filtered_bets, "缩水后投注")
            
            self.root.after(0, update_ui)
        
        ThreadManager.run_in_thread(worker)
    
    def _apply_sfc_filters(self, bets, filters):
        """应用14场专用过滤条件"""
        filtered = []
        
        for bet in bets:
            # 统计胜平负
            wins = bet.count('3')
            draws = bet.count('1')
            loses = bet.count('0')
            
            # 计算积分和
            points = wins * 3 + draws * 1
            
            # 计算断点数
            breaks = sum(1 for i in range(len(bet) - 1) if bet[i] != bet[i+1])
            
            # 计算连号个数
            blocks = len(list(itertools.groupby(bet)))
            
            # 计算连续场次
            consecutive_wins = self._get_max_consecutive(bet, '3')
            consecutive_draws = self._get_max_consecutive(bet, '1')
            consecutive_loses = self._get_max_consecutive(bet, '0')
            
            # 检查过滤条件
            if 'min_wins' in filters and wins < filters['min_wins']:
                continue
            if 'max_wins' in filters and wins > filters['max_wins']:
                continue
            if 'min_draws' in filters and draws < filters['min_draws']:
                continue
            if 'max_draws' in filters and draws > filters['max_draws']:
                continue
            if 'min_loses' in filters and loses < filters['min_loses']:
                continue
            if 'max_loses' in filters and loses > filters['max_loses']:
                continue
            if 'min_points' in filters and points < filters['min_points']:
                continue
            if 'max_points' in filters and points > filters['max_points']:
                continue
            if 'min_breaks' in filters and breaks < filters['min_breaks']:
                continue
            if 'max_breaks' in filters and breaks > filters['max_breaks']:
                continue
            if 'min_blocks' in filters and blocks < filters['min_blocks']:
                continue
            if 'max_blocks' in filters and blocks > filters['max_blocks']:
                continue
            if 'min_consecutive_wins' in filters and consecutive_wins < filters['min_consecutive_wins']:
                continue
            if 'max_consecutive_wins' in filters and consecutive_wins > filters['max_consecutive_wins']:
                continue
            if 'min_consecutive_draws' in filters and consecutive_draws < filters['min_consecutive_draws']:
                continue
            if 'max_consecutive_draws' in filters and consecutive_draws > filters['max_consecutive_draws']:
                continue
            if 'min_consecutive_loses' in filters and consecutive_loses < filters['min_consecutive_loses']:
                continue
            if 'max_consecutive_loses' in filters and consecutive_loses > filters['max_consecutive_loses']:
                continue
            
            filtered.append(bet)
        
        return filtered
    
    def _get_max_consecutive(self, bet_string, target):
        """获取最大连续场次数"""
        max_len = 0
        current_len = 0
        
        for char in bet_string:
            if char == target:
                current_len += 1
                max_len = max(max_len, current_len)
            else:
                current_len = 0
        
        return max_len
    
    def start_wheel(self):
        """开始旋转矩阵"""
        source_bets = self.filtered_bets if self.filtered_bets else self.original_bets
        if not source_bets:
            UIHelper.show_error(self, "错误", "没有可旋转的投注")
            return
        
        def worker():
            UIHelper.show_progress(self, "正在执行旋转矩阵...")
            self.wheeled_bets = WheelMatrix.wheel_guarantee_8(source_bets, 'sfc')
            
            def update_ui():
                UIHelper.hide_progress(self)
                original_count = len(source_bets)
                wheeled_count = len(self.wheeled_bets)
                self.status_var.set(f"旋转完成: {original_count} → {wheeled_count} 注")
                self._display_results(self.wheeled_bets, "旋转后投注")
            
            self.root.after(0, update_ui)
        
        ThreadManager.run_in_thread(worker)
    
    def _display_results(self, bets, title):
        """显示结果"""
        self.result_text.config(state='normal')
        self.result_text.delete('1.0', tk.END)
        
        if not bets:
            self.result_text.insert(tk.END, f"{title}: 无结果")
            self.result_text.config(state='disabled')
            return
        
        # 显示统计信息
        count = len(bets)
        self.stats_label.config(text=f"{title}: {count} 注")
        
        # 显示投注内容
        self.result_text.insert(tk.END, f"{title} ({count} 注):\n\n")
        
        # 限制显示数量
        display_limit = 1000
        display_bets = bets[:display_limit]
        
        for i, bet in enumerate(display_bets, 1):
            self.result_text.insert(tk.END, f"{i:4d}: {bet}\n")
        
        if count > display_limit:
            self.result_text.insert(tk.END, f"\n... 还有 {count - display_limit} 注未显示")
        
        self.result_text.config(state='disabled')
    
    def export_results(self):
        """导出结果"""
        source_bets = self.wheeled_bets if self.wheeled_bets else (self.filtered_bets if self.filtered_bets else self.original_bets)
        if not source_bets:
            UIHelper.show_error(self, "错误", "没有可导出的结果")
            return
        
        filename = filedialog.asksaveasfilename(
            title="导出投注结果",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"14场胜负彩投注结果\n")
                    f.write(f"期号: {self.draw_id_var.get()}\n")
                    f.write(f"注数: {len(source_bets)}\n")
                    f.write(f"生成时间: {tk.datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    for i, bet in enumerate(source_bets, 1):
                        f.write(f"{i:4d}: {bet}\n")
                
                UIHelper.show_info(self, "成功", f"结果已导出到: {filename}")
            except Exception as e:
                UIHelper.show_error(self, "错误", f"导出失败: {e}")
    
    def copy_results(self):
        """复制结果到剪贴板"""
        source_bets = self.wheeled_bets if self.wheeled_bets else (self.filtered_bets if self.filtered_bets else self.original_bets)
        if not source_bets:
            UIHelper.show_error(self, "错误", "没有可复制的结果")
            return
        
        result_text = '\n'.join(source_bets)
        self.root.clipboard_clear()
        self.root.clipboard_append(result_text)
        self.status_var.set(f"已复制 {len(source_bets)} 注到剪贴板")
    
    def clear_all(self):
        """清空所有数据"""
        # 清空投注选择
        for i in range(14):
            for j in range(3):
                self.match_vars[i][j].set(0)
        
        # 清空过滤条件
        for var in self.filter_vars.values():
            var.set('')
        
        # 清空数据
        self.original_bets = []
        self.filtered_bets = []
        self.wheeled_bets = []
        
        # 清空显示
        self.result_text.config(state='normal')
        self.result_text.delete('1.0', tk.END)
        self.result_text.config(state='disabled')
        
        self.bet_info_label.config(text="请选择投注选项")
        self.stats_label.config(text="")
        self.status_var.set("已清空所有数据")

def main():
    root = tk.Tk()
    app = SFCShrinkTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()
