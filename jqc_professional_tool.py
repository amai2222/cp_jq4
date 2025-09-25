"""
专业进球彩缩水工具
参考赢彩进球彩1.6界面设计，实现完整的进球彩缩水功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
import threading
import itertools
import random
import math
import datetime
from common_api import LotteryAPI, ThreadManager, UIHelper

class JQCProfessionalTool:
    def __init__(self, root):
        self.root = root
        self.root.title("进球彩 2.0 - 专业缩水工具")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # 初始化API
        self.api = LotteryAPI()
        
        # 数据存储
        self.current_draw_data = None
        self.original_bets = []
        self.filtered_bets = []
        self.wheeled_bets = []
        
        # UI变量
        self.match_vars = [[tk.StringVar() for _ in range(3)] for _ in range(8)]  # 8场，每场3个数字输入
        self.draw_id_var = tk.StringVar(value="2025181")
        self.status_var = tk.StringVar(value="欢迎使用专业进球彩缩水工具")
        
        # 过滤条件变量
        self.filter_vars = {
            'min_0_goals': tk.StringVar(value='1'),
            'max_0_goals': tk.StringVar(value='4'),
            'min_1_goals': tk.StringVar(value='1'),
            'max_1_goals': tk.StringVar(value='4'),
            'min_2_goals': tk.StringVar(value='0'),
            'max_2_goals': tk.StringVar(value='4'),
            'min_3_goals': tk.StringVar(value='0'),
            'max_3_goals': tk.StringVar(value='4'),
            'min_total_goals': tk.StringVar(value='6'),
            'max_total_goals': tk.StringVar(value='18'),
            'min_breaks': tk.StringVar(value='4'),
            'max_breaks': tk.StringVar(value='7'),
            'min_consecutive_0': tk.StringVar(value='1'),
            'max_consecutive_0': tk.StringVar(value='3'),
            'min_consecutive_1': tk.StringVar(value='1'),
            'max_consecutive_1': tk.StringVar(value='3'),
            'min_consecutive_2': tk.StringVar(value='1'),
            'max_consecutive_2': tk.StringVar(value='3'),
            'min_consecutive_3': tk.StringVar(value='0'),
            'max_consecutive_3': tk.StringVar(value='2'),
            'min_neighbor_sum': tk.StringVar(value='6'),
            'max_neighbor_sum': tk.StringVar(value='12'),
            'min_ac_value': tk.StringVar(value='3'),
            'max_ac_value': tk.StringVar(value='4'),
            'min_goal_diff_sum': tk.StringVar(value='4'),
            'max_goal_diff_sum': tk.StringVar(value='9'),
            'min_position_sum': tk.StringVar(value='20'),
            'max_position_sum': tk.StringVar(value='60')
        }
        
        # 容错变量
        self.tolerance_vars = [tk.IntVar() for _ in range(14)]  # 14个过滤条件的容错
        self.total_tolerance_var = tk.StringVar(value='0')
        
        # 投注方式变量
        self.betting_method_var = tk.StringVar(value="全排组合(中8保8)")
        self.betting_type_var = tk.StringVar(value="全排")
        
        self._create_widgets()
        self._setup_styles()
        
        # 自动加载最新期号
        self.root.after(100, self.refresh_draw_list)
    
    def _setup_styles(self):
        """设置样式"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 配置样式
        self.style.configure('Title.TLabel', font=('Microsoft YaHei UI', 12, 'bold'))
        self.style.configure('Header.TLabel', font=('Microsoft YaHei UI', 10, 'bold'))
        self.style.configure('Success.TButton', foreground='white', background='#28a745')
        self.style.configure('Warning.TButton', foreground='white', background='#ffc107')
        self.style.configure('Danger.TButton', foreground='white', background='#dc3545')
        self.style.configure('Info.TButton', foreground='white', background='#17a2b8')
        
        self.style.map('Success.TButton', background=[('active', '#218838')])
        self.style.map('Warning.TButton', background=[('active', '#e0a800')])
        self.style.map('Danger.TButton', background=[('active', '#c82333')])
        self.style.map('Info.TButton', background=[('active', '#138496')])
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建三个主要区域
        self._create_left_panel(main_frame)
        self._create_middle_panel(main_frame)
        self._create_right_panel(main_frame)
        
        # 状态栏
        self.status_label = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)
    
    def _create_left_panel(self, parent):
        """创建左侧面板 - 投注设置"""
        left_frame = ttk.Frame(parent)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 2), pady=5)
        
        # 投注设置标签页
        notebook = ttk.Notebook(left_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 设置投注复式标签页
        betting_frame = ttk.Frame(notebook, padding="10")
        notebook.add(betting_frame, text="① 设置投注复式并投注")
        
        # 期号选择
        period_frame = ttk.Frame(betting_frame)
        period_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(period_frame, text="彩票期号:", style='Header.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        self.draw_id_combo = ttk.Combobox(period_frame, textvariable=self.draw_id_var, width=12, state='readonly')
        self.draw_id_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(period_frame, text="首次", command=self.go_to_first).pack(side=tk.LEFT, padx=2)
        ttk.Button(period_frame, text="三", command=self.go_to_third).pack(side=tk.LEFT, padx=2)
        ttk.Button(period_frame, text="末", command=self.go_to_last).pack(side=tk.LEFT, padx=2)
        ttk.Button(period_frame, text="数字", command=self.input_number).pack(side=tk.LEFT, padx=2)
        
        # 截止时间显示
        self.deadline_label = ttk.Label(period_frame, text="2025-09-21 截止", foreground="red")
        self.deadline_label.pack(side=tk.RIGHT)
        
        # 对阵表格 - 参考截图1的表格结构
        table_frame = ttk.Frame(betting_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 表头
        headers = ["场次", "联赛", "开赛日期", "主队 VS 客队", "主/客", "0", "1", "2", "3+"]
        for col, header in enumerate(headers):
            ttk.Label(table_frame, text=header, style='Header.TLabel').grid(row=0, column=col, padx=3, pady=3, sticky='ew')
        
        # 对阵数据 - 参考截图1的欧罗巴联赛数据
        self.match_data = [
            ("1", "欧罗巴", "2025-09-26", "里尔 VS 布兰"),
            ("2", "欧罗巴", "2025-09-26", "维拉 VS 博洛尼"),
            ("3", "欧罗巴", "2025-09-26", "斯图加 VS 塞尔塔"),
            ("4", "欧罗巴", "2025-09-26", "乌德勒 VS 里昂")
        ]
        
        # 进球选择变量 - 每场主队和客队各4个选项(0,1,2,3+)
        self.goal_vars = [[[tk.BooleanVar() for _ in range(4)] for _ in range(2)] for _ in range(8)]
        
        for i in range(8):
            # 场次号
            if i < len(self.match_data):
                ttk.Label(table_frame, text=self.match_data[i][0]).grid(row=i*2+1, column=0, padx=3, pady=3, rowspan=2)
                # 联赛
                ttk.Label(table_frame, text=self.match_data[i][1]).grid(row=i*2+1, column=1, padx=3, pady=3, rowspan=2)
                # 开赛日期
                ttk.Label(table_frame, text=self.match_data[i][2]).grid(row=i*2+1, column=2, padx=3, pady=3, rowspan=2)
                # 对阵信息
                ttk.Label(table_frame, text=self.match_data[i][3]).grid(row=i*2+1, column=3, padx=3, pady=3, rowspan=2)
            else:
                ttk.Label(table_frame, text=f"{i+1}").grid(row=i*2+1, column=0, padx=3, pady=3, rowspan=2)
                ttk.Label(table_frame, text="欧罗巴").grid(row=i*2+1, column=1, padx=3, pady=3, rowspan=2)
                ttk.Label(table_frame, text="2025-09-26").grid(row=i*2+1, column=2, padx=3, pady=3, rowspan=2)
                ttk.Label(table_frame, text=f"第{i+1}场对阵").grid(row=i*2+1, column=3, padx=3, pady=3, rowspan=2)
            
            # 主队进球选择
            ttk.Label(table_frame, text="主").grid(row=i*2+1, column=4, padx=3, pady=3)
            for j in range(4):
                goal_text = "3+" if j == 3 else str(j)
                ttk.Checkbutton(table_frame, text=goal_text, variable=self.goal_vars[i][0][j]).grid(
                    row=i*2+1, column=5+j, padx=3, pady=3)
            
            # 客队进球选择
            ttk.Label(table_frame, text="客").grid(row=i*2+2, column=4, padx=3, pady=3)
            for j in range(4):
                goal_text = "3+" if j == 3 else str(j)
                ttk.Checkbutton(table_frame, text=goal_text, variable=self.goal_vars[i][1][j]).grid(
                    row=i*2+2, column=5+j, padx=3, pady=3)
        
        # 配置列权重
        for i in range(9):
            table_frame.grid_columnconfigure(i, weight=1)
        
        # 底部投注选项
        bottom_frame = ttk.Frame(betting_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 投注方式选择
        method_frame = ttk.Frame(bottom_frame)
        method_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Radiobutton(method_frame, text="● 全排组合 (中8保8)", variable=self.betting_method_var, 
                       value="全排组合(中8保8)").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(method_frame, text="○ 胆拖组合 (中8保7)", variable=self.betting_method_var, 
                       value="胆拖组合(中8保7)").pack(side=tk.LEFT)
        
        # 投注类型选择
        type_frame = ttk.Frame(bottom_frame)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(type_frame, text="投注方式:").pack(side=tk.LEFT, padx=(0, 5))
        self.method_combo = ttk.Combobox(type_frame, textvariable=self.betting_type_var, 
                                        values=["全排", "胆拖", "缩水", "注水"], width=15, state='readonly')
        self.method_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.method_combo.set("全排")
        
        ttk.Button(type_frame, text="投注 >>", command=self.calculate_bets, style='Success.TButton').pack(side=tk.LEFT)
    
    def _create_middle_panel(self, parent):
        """创建中间面板 - 过滤设置"""
        middle_frame = ttk.Frame(parent)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=5)
        
        # 过滤设置标签页
        notebook = ttk.Notebook(middle_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 设置过滤条件标签页
        filter_frame = ttk.Frame(notebook, padding="10")
        notebook.add(filter_frame, text="② 设置过滤条件并过滤")
        
        # 过滤条件标签页
        filter_notebook = ttk.Notebook(filter_frame)
        filter_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 常规过滤
        regular_frame = ttk.Frame(filter_notebook, padding="5")
        filter_notebook.add(regular_frame, text="常规")
        
        # 过滤条件列表
        self._create_filter_conditions(regular_frame)
        
        # 过滤操作区域
        operation_frame = ttk.Frame(filter_frame)
        operation_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 总容错设置
        tolerance_frame = ttk.Frame(operation_frame)
        tolerance_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(tolerance_frame, text="选择").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(tolerance_frame, textvariable=self.total_tolerance_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(tolerance_frame, text="< 总容错 ≤").pack(side=tk.LEFT, padx=2)
        ttk.Entry(tolerance_frame, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Button(tolerance_frame, text="过滤 >>", command=self.start_filter, style='Warning.TButton').pack(side=tk.LEFT, padx=(10, 0))
        
        # 投注数显示
        self.bet_count_label = ttk.Label(operation_frame, text="投注数: 0 注", style='Header.TLabel')
        self.bet_count_label.pack(side=tk.LEFT, padx=(0, 20))
    
    def _create_filter_conditions(self, parent):
        """创建过滤条件列表"""
        # 过滤条件定义
        filter_conditions = [
            ("进0球个数", "min_0_goals", "max_0_goals"),
            ("进1球个数", "min_1_goals", "max_1_goals"),
            ("进2球个数", "min_2_goals", "max_2_goals"),
            ("进3球个数", "min_3_goals", "max_3_goals"),
            ("进球和值", "min_total_goals", "max_total_goals"),
            ("断点数", "min_breaks", "max_breaks"),
            ("连0个数", "min_consecutive_0", "max_consecutive_0"),
            ("连1个数", "min_consecutive_1", "max_consecutive_1"),
            ("连2个数", "min_consecutive_2", "max_consecutive_2"),
            ("连3个数", "min_consecutive_3", "max_consecutive_3"),
            ("邻号间距和", "min_neighbor_sum", "max_neighbor_sum"),
            ("数字AC值", "min_ac_value", "max_ac_value"),
            ("进球差绝对和", "min_goal_diff_sum", "max_goal_diff_sum"),
            ("号码位积和", "min_position_sum", "max_position_sum")
        ]
        
        # 创建过滤条件行
        for i, (name, min_key, max_key) in enumerate(filter_conditions):
            row_frame = ttk.Frame(parent)
            row_frame.pack(fill=tk.X, pady=2)
            
            # 选择复选框
            ttk.Checkbutton(row_frame, text="").pack(side=tk.LEFT, padx=(0, 5))
            
            # 最小值输入
            ttk.Entry(row_frame, textvariable=self.filter_vars[min_key], width=5).pack(side=tk.LEFT, padx=2)
            
            # 操作符
            ttk.Label(row_frame, text="<").pack(side=tk.LEFT, padx=2)
            
            # 条件名称
            ttk.Label(row_frame, text=name, width=12, anchor='w').pack(side=tk.LEFT, padx=2)
            
            # 操作符
            ttk.Label(row_frame, text="≤").pack(side=tk.LEFT, padx=2)
            
            # 最大值输入
            ttk.Entry(row_frame, textvariable=self.filter_vars[max_key], width=5).pack(side=tk.LEFT, padx=2)
            
            # 容错复选框
            ttk.Checkbutton(row_frame, text="", variable=self.tolerance_vars[i]).pack(side=tk.LEFT, padx=(10, 0))
    
    def _create_right_panel(self, parent):
        """创建右侧面板 - 结果显示"""
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 5), pady=5)
        
        # 结果显示标签页
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 投注结果标签页
        result_frame = ttk.Frame(notebook, padding="10")
        notebook.add(result_frame, text="③投注结果")
        
        # 结果处理下拉框 - 参考截图2
        process_frame = ttk.Frame(result_frame)
        process_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(process_frame, text="结果处理:").pack(side=tk.LEFT, padx=(0, 5))
        self.process_combo = ttk.Combobox(process_frame, values=[
            "调出投注结果", "保存投注结果 F12", "自由缩水", "投注结果缩水", 
            "24注校验选注", "复制选中注(C)", "投注编辑(E)", "删除选中注", 
            "添加投注", "投注结果替换", "全部清除", "自由选注 Ctrl+Alt+R", 
            "投注结果排序", "号码分布统计", "分解复式", "合成复式"
        ], width=20, state='readonly')
        self.process_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.process_combo.set("调出投注结果")
        
        # 结果表格
        columns = ('注号', '投注结果')
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=20)
        
        self.result_tree.heading('注号', text='注号')
        self.result_tree.heading('投注结果', text='投注结果')
        
        self.result_tree.column('注号', width=80, anchor='center')
        self.result_tree.column('投注结果', width=200, anchor='center')
        
        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 分页控制 - 参考截图2
        page_frame = ttk.Frame(result_frame)
        page_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 分页变量
        self.current_page = 1
        self.items_per_page = 50
        self.total_pages = 1
        
        self.prev_button = ttk.Button(page_frame, text="<<上页", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(page_frame, text="跳到").pack(side=tk.LEFT, padx=(0, 5))
        self.page_entry = ttk.Entry(page_frame, width=5)
        self.page_entry.pack(side=tk.LEFT, padx=2)
        self.page_entry.bind('<Return>', self.jump_to_page)
        
        self.page_label = ttk.Label(page_frame, text="页 / 0 页")
        self.page_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.next_button = ttk.Button(page_frame, text="下页>>", command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(page_frame, text="打印", style='Info.TButton', command=self.print_results).pack(side=tk.RIGHT)
    
    def refresh_draw_list(self):
        """刷新期号列表"""
        def worker():
            UIHelper.show_progress(self, "正在获取期号列表...")
            result = self.api.get_draw_list('jqc', 10)
            
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
    
    def fetch_draw_details(self):
        """获取开奖详情"""
        draw_id = self.draw_id_var.get()
        if not draw_id:
            return
        
        def worker():
            UIHelper.show_progress(self, f"正在获取第{draw_id}期详情...")
            result = self.api.get_draw_details('jqc', draw_id)
            
            def update_ui():
                UIHelper.hide_progress(self)
                self.current_draw_data = result
                
                if result['status'] == 'error':
                    UIHelper.show_error(self, "错误", result['message'])
                    self.status_var.set("详情获取失败")
                    return
                
                # 更新截止时间
                if result['status'] == 'pending':
                    self.deadline_label.config(text=f"{result.get('message', '未知')} 截止", foreground="red")
                else:
                    self.deadline_label.config(text=f"{result.get('draw_time', '未知')} 已开奖", foreground="green")
                
                self.status_var.set(f"第{draw_id}期详情获取成功")
            
            self.root.after(0, update_ui)
        
        ThreadManager.run_in_thread(worker)
    
    def go_to_first(self):
        """跳转到第一期"""
        if hasattr(self, 'draw_id_combo') and self.draw_id_combo['values']:
            self.draw_id_var.set(self.draw_id_combo['values'][-1])
            self.fetch_draw_details()
    
    def go_to_third(self):
        """跳转到第三期"""
        if hasattr(self, 'draw_id_combo') and len(self.draw_id_combo['values']) >= 3:
            self.draw_id_var.set(self.draw_id_combo['values'][-3])
            self.fetch_draw_details()
    
    def go_to_last(self):
        """跳转到最后一期"""
        if hasattr(self, 'draw_id_combo') and self.draw_id_combo['values']:
            self.draw_id_var.set(self.draw_id_combo['values'][0])
            self.fetch_draw_details()
    
    def input_number(self):
        """手动输入期号"""
        period = tk.simpledialog.askstring("输入期号", "请输入期号:")
        if period:
            self.draw_id_var.set(period)
            self.fetch_draw_details()
    
    def calculate_bets(self):
        """计算投注组合"""
        # 检查输入 - 每场主队和客队都必须至少选择一个进球数
        selected_matches = []
        for i in range(8):
            home_options = []
            away_options = []
            
            # 检查主队选择
            for j in range(4):
                if self.goal_vars[i][0][j].get():
                    home_options.append(j)
            
            # 检查客队选择
            for j in range(4):
                if self.goal_vars[i][1][j].get():
                    away_options.append(j)
            
            if not home_options:
                UIHelper.show_error(self, "错误", f"第{i+1}场主队必须至少选择一个进球数")
                return
            
            if not away_options:
                UIHelper.show_error(self, "错误", f"第{i+1}场客队必须至少选择一个进球数")
                return
            
            # 进球彩是8场，每场主队和客队各选一个进球数
            # 所以每场有 home_options × away_options 种组合
            match_combos = []
            for h in home_options:
                for a in away_options:
                    match_combos.append((h, a))
            
            selected_matches.append(match_combos)
        
        # 生成所有组合
        self.original_bets = []
        for combo in itertools.product(*selected_matches):
            # 将每场的(主队进球, 客队进球)转换为8位数字串
            bet_str = ''.join([f"{h}{a}" for h, a in combo])
            self.original_bets.append(bet_str)
        
        # 更新显示
        total_bets = len(self.original_bets)
        self.bet_count_label.config(text=f"投注数: {total_bets} 注")
        self.status_var.set(f"投注计算完成，共 {total_bets} 注")
        
        # 显示结果
        self._display_results(self.original_bets, "原始投注")
    
    def start_filter(self):
        """开始过滤"""
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
            
            # 获取总容错数
            try:
                total_tolerance = int(self.total_tolerance_var.get())
            except ValueError:
                total_tolerance = 0
            
            # 应用过滤
            self.filtered_bets = self._apply_jqc_filters(self.original_bets, filters, total_tolerance)
            
            def update_ui():
                UIHelper.hide_progress(self)
                original_count = len(self.original_bets)
                filtered_count = len(self.filtered_bets)
                self.bet_count_label.config(text=f"投注数: {filtered_count} 注")
                self.status_var.set(f"过滤完成: {original_count} → {filtered_count} 注")
                self._display_results(self.filtered_bets, "过滤后投注")
            
            self.root.after(0, update_ui)
        
        ThreadManager.run_in_thread(worker)
    
    def _apply_jqc_filters(self, bets, filters, total_tolerance):
        """应用进球彩过滤条件"""
        filtered = []
        
        for bet in bets:
            # 将字符串转换为数字列表进行分析
            bet_digits = [int(d) for d in bet]
            
            # 计算各种统计指标
            stats = self._calculate_bet_stats(bet_digits)
            
            # 检查过滤条件
            errors = 0
            failed = False
            
            # 进球数统计
            if 'min_0_goals' in filters and stats['0_goals'] < filters['min_0_goals']:
                if self.tolerance_vars[0].get():
                    errors += 1
                else:
                    failed = True
            if 'max_0_goals' in filters and stats['0_goals'] > filters['max_0_goals']:
                if self.tolerance_vars[0].get():
                    errors += 1
                else:
                    failed = True
            
            if 'min_1_goals' in filters and stats['1_goals'] < filters['min_1_goals']:
                if self.tolerance_vars[1].get():
                    errors += 1
                else:
                    failed = True
            if 'max_1_goals' in filters and stats['1_goals'] > filters['max_1_goals']:
                if self.tolerance_vars[1].get():
                    errors += 1
                else:
                    failed = True
            
            if 'min_2_goals' in filters and stats['2_goals'] < filters['min_2_goals']:
                if self.tolerance_vars[2].get():
                    errors += 1
                else:
                    failed = True
            if 'max_2_goals' in filters and stats['2_goals'] > filters['max_2_goals']:
                if self.tolerance_vars[2].get():
                    errors += 1
                else:
                    failed = True
            
            if 'min_3_goals' in filters and stats['3_goals'] < filters['min_3_goals']:
                if self.tolerance_vars[3].get():
                    errors += 1
                else:
                    failed = True
            if 'max_3_goals' in filters and stats['3_goals'] > filters['max_3_goals']:
                if self.tolerance_vars[3].get():
                    errors += 1
                else:
                    failed = True
            
            # 其他条件检查...
            if 'min_total_goals' in filters and stats['total_goals'] < filters['min_total_goals']:
                if self.tolerance_vars[4].get():
                    errors += 1
                else:
                    failed = True
            if 'max_total_goals' in filters and stats['total_goals'] > filters['max_total_goals']:
                if self.tolerance_vars[4].get():
                    errors += 1
                else:
                    failed = True
            
            # 检查总容错
            if not failed and errors > total_tolerance:
                failed = True
            
            if not failed:
                filtered.append(bet)
        
        return filtered
    
    def _calculate_bet_stats(self, bet):
        """计算投注统计指标"""
        stats = {
            '0_goals': bet.count(0),
            '1_goals': bet.count(1),
            '2_goals': bet.count(2),
            '3_goals': bet.count(3),
            'total_goals': sum(bet),
            'breaks': sum(1 for i in range(len(bet) - 1) if bet[i] != bet[i+1]),
            'consecutive_0': self._get_max_consecutive(bet, 0),
            'consecutive_1': self._get_max_consecutive(bet, 1),
            'consecutive_2': self._get_max_consecutive(bet, 2),
            'consecutive_3': self._get_max_consecutive(bet, 3),
            'neighbor_sum': sum(abs(bet[i] - bet[i+1]) for i in range(len(bet) - 1)),
            'ac_value': self._calculate_ac_value(bet),
            'goal_diff_sum': sum(abs(bet[i] - bet[j]) for i in range(len(bet)) for j in range(i+1, len(bet))),
            'position_sum': sum((i+1) * bet[i] for i in range(len(bet)))
        }
        return stats
    
    def _get_max_consecutive(self, bet, target):
        """获取最大连续次数"""
        max_len = 0
        current_len = 0
        
        for num in bet:
            if num == target:
                current_len += 1
                max_len = max(max_len, current_len)
            else:
                current_len = 0
        
        return max_len
    
    def _calculate_ac_value(self, bet):
        """计算AC值"""
        diffs = set()
        for i in range(len(bet)):
            for j in range(i+1, len(bet)):
                diffs.add(abs(bet[i] - bet[j]))
        return len(diffs)
    
    def _display_results(self, bets, title):
        """显示结果"""
        # 清空现有结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        if not bets:
            self.current_page = 1
            self.total_pages = 1
            self._update_page_info()
            return
        
        # 计算分页信息
        self.total_pages = max(1, (len(bets) + self.items_per_page - 1) // self.items_per_page)
        self.current_page = min(self.current_page, self.total_pages)
        
        # 计算当前页显示的数据
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(bets))
        display_bets = bets[start_idx:end_idx]
        
        # 显示当前页数据
        for i, bet in enumerate(display_bets, start_idx + 1):
            self.result_tree.insert('', tk.END, values=(i, bet))
        
        # 更新分页信息
        self._update_page_info()
        
        self.status_var.set(f"{title}: 显示第 {self.current_page}/{self.total_pages} 页，共 {len(bets)} 注")
    
    def _update_page_info(self):
        """更新分页信息"""
        self.page_label.config(text=f"页 / {self.total_pages} 页")
        self.page_entry.delete(0, tk.END)
        self.page_entry.insert(0, str(self.current_page))
        
        # 更新按钮状态
        self.prev_button.config(state='normal' if self.current_page > 1 else 'disabled')
        self.next_button.config(state='normal' if self.current_page < self.total_pages else 'disabled')
    
    def prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            if hasattr(self, 'filtered_bets') and self.filtered_bets:
                self._display_results(self.filtered_bets, "过滤后投注")
            elif hasattr(self, 'original_bets') and self.original_bets:
                self._display_results(self.original_bets, "原始投注")
    
    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            if hasattr(self, 'filtered_bets') and self.filtered_bets:
                self._display_results(self.filtered_bets, "过滤后投注")
            elif hasattr(self, 'original_bets') and self.original_bets:
                self._display_results(self.original_bets, "原始投注")
    
    def jump_to_page(self, event=None):
        """跳转到指定页"""
        try:
            page = int(self.page_entry.get())
            if 1 <= page <= self.total_pages:
                self.current_page = page
                if hasattr(self, 'filtered_bets') and self.filtered_bets:
                    self._display_results(self.filtered_bets, "过滤后投注")
                elif hasattr(self, 'original_bets') and self.original_bets:
                    self._display_results(self.original_bets, "原始投注")
            else:
                messagebox.showerror("错误", f"页码必须在 1 到 {self.total_pages} 之间")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的页码")
    
    def print_results(self):
        """打印结果"""
        if not hasattr(self, 'original_bets') or not self.original_bets:
            messagebox.showwarning("警告", "没有可打印的结果")
            return
        
        # 选择要打印的数据
        data_to_print = self.filtered_bets if hasattr(self, 'filtered_bets') and self.filtered_bets else self.original_bets
        
        # 创建打印窗口
        print_window = tk.Toplevel(self.root)
        print_window.title("打印投注结果")
        print_window.geometry("600x500")
        
        # 创建文本框
        text_widget = scrolledtext.ScrolledText(print_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 添加打印内容
        text_widget.insert(tk.END, f"进球彩投注结果\n")
        text_widget.insert(tk.END, f"期号: {self.draw_id_var.get()}\n")
        text_widget.insert(tk.END, f"投注时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        text_widget.insert(tk.END, f"总注数: {len(data_to_print)}\n")
        text_widget.insert(tk.END, "="*50 + "\n\n")
        
        for i, bet in enumerate(data_to_print, 1):
            text_widget.insert(tk.END, f"{i:4d}. {bet}\n")
        
        # 添加打印按钮
        button_frame = ttk.Frame(print_window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="保存到文件", command=lambda: self.save_to_file(text_widget.get(1.0, tk.END))).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=print_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def save_to_file(self, content):
        """保存到文件"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", f"结果已保存到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")

def main():
    root = tk.Tk()
    app = JQCProfessionalTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()
