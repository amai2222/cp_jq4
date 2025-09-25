"""
进球4场缩水工具
支持自动获取期号对阵、投注选择、缩水过滤、旋转矩阵
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
from common_api import LotteryAPI, ShrinkAlgorithm, WheelMatrix, ThreadManager, UIHelper

class JQCShrinkTool:
    def __init__(self, root):
        self.root = root
        self.root.title("进球4场专业缩水工具 V1.0")
        self.root.geometry("1200x900")
        self.root.minsize(1000, 700)
        
        # 初始化API
        self.api = LotteryAPI()
        
        # 数据存储
        self.current_draw_data = None
        self.original_bets = []
        self.filtered_bets = []
        self.wheeled_bets = []
        
        # UI变量
        self.match_vars = [[tk.IntVar(value=0) for _ in range(5)] for _ in range(4)]  # 4场，每场5个选项(0,1,2,3,4+)
        self.draw_id_var = tk.StringVar()
        self.status_var = tk.StringVar(value="欢迎使用进球4场缩水工具")
        
        # 过滤条件变量
        self.filter_vars = {
            'min_total_goals': tk.StringVar(),
            'max_total_goals': tk.StringVar(),
            'min_high_goals': tk.StringVar(),  # 高进球场次(3+)
            'max_high_goals': tk.StringVar(),
            'min_low_goals': tk.StringVar(),   # 低进球场次(0-1)
            'max_low_goals': tk.StringVar()
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
        title_label = ttk.Label(main_frame, text="进球4场专业缩水工具", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # 创建三个主要区域
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
        self.match_info_text = scrolledtext.ScrolledText(data_frame, height=6, wrap=tk.WORD, state='disabled')
        self.match_info_text.pack(fill=tk.X, pady=(10, 0))
    
    def _create_betting_area(self, parent):
        """创建投注选择区域"""
        betting_frame = ttk.LabelFrame(parent, text="② 投注选择", padding="10")
        betting_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 投注表格
        table_frame = ttk.Frame(betting_frame)
        table_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 表头
        headers = ["场次", "主队", "客队", "0球", "1球", "2球", "3球", "4+球"]
        for col, header in enumerate(headers):
            ttk.Label(table_frame, text=header, style='Header.TLabel').grid(row=0, column=col, padx=5, pady=5, sticky='ew')
        
        # 投注选项
        self.match_labels = []
        for i in range(4):
            # 场次号
            ttk.Label(table_frame, text=f"第{i+1}场").grid(row=i+1, column=0, padx=5, pady=5)
            
            # 队伍名称（占位）
            ttk.Label(table_frame, text="主队", width=15).grid(row=i+1, column=1, padx=5, pady=5)
            ttk.Label(table_frame, text="客队", width=15).grid(row=i+1, column=2, padx=5, pady=5)
            
            # 投注选项
            for j in range(5):
                cb = ttk.Checkbutton(table_frame, variable=self.match_vars[i][j])
                cb.grid(row=i+1, column=j+3, padx=5, pady=5)
        
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
        
        # 过滤条件
        filter_frame = ttk.Frame(shrink_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第一行过滤条件
        row1 = ttk.Frame(filter_frame)
        row1.pack(fill=tk.X, pady=5)
        
        ttk.Label(row1, text="总进球数:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(row1, textvariable=self.filter_vars['min_total_goals'], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(row1, text="≤").pack(side=tk.LEFT, padx=2)
        ttk.Entry(row1, textvariable=self.filter_vars['max_total_goals'], width=5).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(row1, text="高进球场次(3+):").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Entry(row1, textvariable=self.filter_vars['min_high_goals'], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(row1, text="≤").pack(side=tk.LEFT, padx=2)
        ttk.Entry(row1, textvariable=self.filter_vars['max_high_goals'], width=5).pack(side=tk.LEFT, padx=2)
        
        # 第二行过滤条件
        row2 = ttk.Frame(filter_frame)
        row2.pack(fill=tk.X, pady=5)
        
        ttk.Label(row2, text="低进球场次(0-1):").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(row2, textvariable=self.filter_vars['min_low_goals'], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(row2, text="≤").pack(side=tk.LEFT, padx=2)
        ttk.Entry(row2, textvariable=self.filter_vars['max_low_goals'], width=5).pack(side=tk.LEFT, padx=2)
        
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
            result = self.api.get_draw_details('jqc', draw_id)
            
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
            for i, match in enumerate(matches[:4]):  # 只显示前4场
                home = match.get('masterTeamName', '主队')
                away = match.get('guestTeamName', '客队')
                result = match.get('result', '未开奖')
                self.match_info_text.insert(tk.END, f"第{i+1}场: {home} vs {away} - {result}\n")
        
        self.match_info_text.config(state='disabled')
    
    def calculate_bets(self):
        """计算投注组合"""
        # 检查选择
        selected_matches = []
        for i in range(4):
            options = []
            for j in range(5):
                if self.match_vars[i][j].get():
                    options.append(str(j))
            if not options:
                UIHelper.show_error(self, "错误", f"第{i+1}场必须选择至少一个选项")
                return
            selected_matches.append(options)
        
        # 生成所有组合
        import itertools
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
                if self.filter_vars['min_total_goals'].get():
                    filters['min_total_goals'] = int(self.filter_vars['min_total_goals'].get())
                if self.filter_vars['max_total_goals'].get():
                    filters['max_total_goals'] = int(self.filter_vars['max_total_goals'].get())
                if self.filter_vars['min_high_goals'].get():
                    filters['min_high_goals'] = int(self.filter_vars['min_high_goals'].get())
                if self.filter_vars['max_high_goals'].get():
                    filters['max_high_goals'] = int(self.filter_vars['max_high_goals'].get())
                if self.filter_vars['min_low_goals'].get():
                    filters['min_low_goals'] = int(self.filter_vars['min_low_goals'].get())
                if self.filter_vars['max_low_goals'].get():
                    filters['max_low_goals'] = int(self.filter_vars['max_low_goals'].get())
            except ValueError:
                def show_error():
                    UIHelper.hide_progress(self)
                    UIHelper.show_error(self, "错误", "过滤条件必须是数字")
                self.root.after(0, show_error)
                return
            
            # 应用过滤
            self.filtered_bets = self._apply_jqc_filters(self.original_bets, filters)
            
            def update_ui():
                UIHelper.hide_progress(self)
                original_count = len(self.original_bets)
                filtered_count = len(self.filtered_bets)
                self.status_var.set(f"缩水完成: {original_count} → {filtered_count} 注")
                self._display_results(self.filtered_bets, "缩水后投注")
            
            self.root.after(0, update_ui)
        
        ThreadManager.run_in_thread(worker)
    
    def _apply_jqc_filters(self, bets, filters):
        """应用进球4场专用过滤条件"""
        filtered = []
        
        for bet in bets:
            # 计算进球数
            goals = [int(x) for x in bet]
            total_goals = sum(goals)
            high_goals = sum(1 for g in goals if g >= 3)
            low_goals = sum(1 for g in goals if g <= 1)
            
            # 检查过滤条件
            if 'min_total_goals' in filters and total_goals < filters['min_total_goals']:
                continue
            if 'max_total_goals' in filters and total_goals > filters['max_total_goals']:
                continue
            if 'min_high_goals' in filters and high_goals < filters['min_high_goals']:
                continue
            if 'max_high_goals' in filters and high_goals > filters['max_high_goals']:
                continue
            if 'min_low_goals' in filters and low_goals < filters['min_low_goals']:
                continue
            if 'max_low_goals' in filters and low_goals > filters['max_low_goals']:
                continue
            
            filtered.append(bet)
        
        return filtered
    
    def start_wheel(self):
        """开始旋转矩阵"""
        source_bets = self.filtered_bets if self.filtered_bets else self.original_bets
        if not source_bets:
            UIHelper.show_error(self, "错误", "没有可旋转的投注")
            return
        
        def worker():
            UIHelper.show_progress(self, "正在执行旋转矩阵...")
            self.wheeled_bets = WheelMatrix.wheel_guarantee_8(source_bets, 'jqc')
            
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
                    f.write(f"进球4场投注结果\n")
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
        for i in range(4):
            for j in range(5):
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
    app = JQCShrinkTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()
