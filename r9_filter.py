#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任九过滤器
数据格式：14个位置，用特殊符号表示
符号含义：3（胜）、1（平）、0（负）、*（任选/不选）
中奖条件：9个非*位置全部猜中
示例：3*103*1*0*3*1*0*
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re
import random
import requests
import json
from datetime import datetime

class R9Filter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("任九过滤器")
        self.root.geometry("1800x900")
        
        # 数据存储
        self.original_data = []  # 原始投注数据
        self.betting_data = []   # 投注区数据
        self.filtered_data = []  # 过滤后数据
        self.history = []        # 操作历史
        
        # 过滤条件变量
        self.r9_vars = []  # 任九过滤条件
        self._init_filter_vars()
        
        # 当前期号和对阵数据
        self.current_period = ""
        self.match_data = []
        self.betting_selections = {}
        self.match_labels = {}
        
        self._create_widgets()
        self._setup_styles()
        
        # 初始化时自动获取最新期号
        self.root.after(1000, self.auto_refresh_period_and_details)
    
    def _init_filter_vars(self):
        """初始化过滤条件变量"""
        # 任九过滤条件：14个位置
        for i in range(14):
            position_vars = {}
            for result in ['3', '1', '0', '*']:
                position_vars[result] = tk.BooleanVar()
            self.r9_vars.append(position_vars)
    
    def _setup_styles(self):
        """设置界面样式"""
        self.style = ttk.Style()
        self.root.configure(bg='#F0F0F0')
        
        # 设置scrolledtext样式
        style = ttk.Style()
        style.configure('White.TScrolledtext', background='white', foreground='black')
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 三列布局
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：数据获取和投注选择
        data_frame = ttk.LabelFrame(content_frame, text="①数据获取与投注选择", padding="10")
        data_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self._create_data_acquisition_ui(data_frame)
        
        # 中间：投注数据输入区
        left_frame = ttk.LabelFrame(content_frame, text="投注数据输入", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self._create_input_ui(left_frame)
        
        # 右侧：过滤器和结果显示区
        right_frame = ttk.LabelFrame(content_frame, text="过滤器与结果", padding="10")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._create_filter_ui(right_frame)
        self._create_result_ui(right_frame)
    
    def _create_data_acquisition_ui(self, parent):
        """创建数据获取界面"""
        # 期号获取
        data_acq_frame = ttk.Frame(parent)
        data_acq_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(data_acq_frame, text="任九数据获取", font=('Microsoft YaHei UI', 12, 'bold')).pack(anchor=tk.W)
        
        # 期号输入和按钮
        period_frame = ttk.Frame(data_acq_frame)
        period_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(period_frame, text="期号:", width=6).pack(side=tk.LEFT)
        self.period_var = tk.StringVar(value="")
        self.period_combo = ttk.Combobox(period_frame, textvariable=self.period_var, width=10, state="normal")
        self.period_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        # 绑定期号变化事件，自动获取详情
        self.period_var.trace('w', self.on_period_changed)
        
        ttk.Button(period_frame, text="刷新期号", command=self.refresh_period).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(period_frame, text="获取详情", command=self.get_match_details).pack(side=tk.LEFT)
        
        # 详情显示
        ttk.Label(data_acq_frame, text="对阵详情:").pack(anchor=tk.W)
        self.details_text = scrolledtext.ScrolledText(data_acq_frame, height=8, width=50, bg='white', fg='black')
        self.details_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 投注选择
        betting_frame = ttk.LabelFrame(data_acq_frame, text="②投注选择", padding="5")
        betting_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self._create_match_table(betting_frame)
        
        # 生成投注按钮
        ttk.Button(betting_frame, text="生成投注", command=self.generate_bets, 
                  style='Success.TButton').pack(pady=(10, 0))
    
    def _create_match_table(self, parent):
        """创建对阵表格"""
        # 创建表格框架
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 表头
        headers = ["场次", "联赛", "开赛日期", "主队 VS 客队", "投注选择"]
        
        # 创建表头
        for i, header in enumerate(headers):
            label = ttk.Label(table_frame, text=header, font=('Microsoft YaHei UI', 9, 'bold'))
            label.grid(row=0, column=i, padx=1, pady=1, sticky="ew")
        
        # 创建14场比赛的行
        for i in range(14):
            self._create_match_row(table_frame, i, i + 1)
        
        # 设置列权重
        for i in range(len(headers)):
            table_frame.columnconfigure(i, weight=1)
    
    def _create_match_row(self, parent, game_idx, row):
        """创建比赛行"""
        # 场次
        match_num_label = ttk.Label(parent, text=f"{game_idx + 1}", font=('Microsoft YaHei UI', 9))
        match_num_label.grid(row=row, column=0, padx=1, pady=1, sticky="ew")
        
        # 联赛
        league_label = ttk.Label(parent, text="未知", font=('Microsoft YaHei UI', 9))
        league_label.grid(row=row, column=1, padx=1, pady=1, sticky="ew")
        
        # 开赛日期
        date_label = ttk.Label(parent, text="未知", font=('Microsoft YaHei UI', 9))
        date_label.grid(row=row, column=2, padx=1, pady=1, sticky="ew")
        
        # 主队 VS 客队
        teams_label = ttk.Label(parent, text="未知 VS 未知", font=('Microsoft YaHei UI', 9))
        teams_label.grid(row=row, column=3, padx=1, pady=1, sticky="ew")
        
        # 投注选择
        selection_frame = ttk.Frame(parent)
        selection_frame.grid(row=row, column=4, padx=1, pady=1, sticky="ew")
        
        # 投注选项：3（胜）、1（平）、0（负）、*（任选）
        r9_options = ['3', '1', '0', '*']
        for j, option in enumerate(r9_options):
            var = tk.BooleanVar()
            cb = tk.Checkbutton(selection_frame, text=option, variable=var, 
                               font=('Microsoft YaHei UI', 8))
            cb.grid(row=0, column=j, padx=1, pady=1)
            
            if game_idx not in self.betting_selections:
                self.betting_selections[game_idx] = {}
            self.betting_selections[game_idx][option] = var
        
        # 保存标签引用以便后续更新
        if game_idx not in self.match_labels:
            self.match_labels[game_idx] = {}
        self.match_labels[game_idx] = {
            'match_num': match_num_label,
            'league': league_label,
            'date': date_label,
            'teams': teams_label
        }
    
    def _create_input_ui(self, parent):
        """创建输入界面"""
        # 输入说明
        ttk.Label(parent, text="请输入任九投注结果，每行一个投注，格式如：3*103*1*0*3*1*0*", 
                 font=('Microsoft YaHei UI', 10)).pack(anchor=tk.W, pady=(0, 5))
        
        # 输入文本框
        self.input_text = scrolledtext.ScrolledText(parent, height=15, bg='white', fg='black')
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 按钮框架
        input_btn_frame = ttk.Frame(parent)
        input_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(input_btn_frame, text="加载数据到投注区", command=self.load_data).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(input_btn_frame, text="清空", command=self.clear_input).pack(side=tk.LEFT)
        
        # 数据统计
        self.stats_label = ttk.Label(parent, text="数据统计：0 条", 
                                   font=('Microsoft YaHei UI', 10))
        self.stats_label.pack(anchor=tk.W)
        
        # 投注区
        betting_frame = ttk.LabelFrame(parent, text="投注区", padding="5")
        betting_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.betting_text = scrolledtext.ScrolledText(betting_frame, height=10, bg='white', fg='black')
        self.betting_text.pack(fill=tk.BOTH, expand=True)
        
        self.betting_stats = ttk.Label(betting_frame, text="投注数据：0 条", 
                                     font=('Microsoft YaHei UI', 10))
        self.betting_stats.pack(anchor=tk.W, pady=(5, 0))
    
    def _create_filter_ui(self, parent):
        """创建过滤器界面"""
        # 任九过滤器
        filter_frame = ttk.LabelFrame(parent, text="任九过滤器", padding="10")
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建14个位置的任九过滤
        for i in range(14):
            position_frame = ttk.LabelFrame(filter_frame, text=f"第{i+1}场", padding="5")
            position_frame.grid(row=i//4, column=i%4, padx=2, pady=2, sticky="ew")
            
            # 投注选项
            r9_options = ['3', '1', '0', '*']
            for j, option in enumerate(r9_options):
                cb = tk.Checkbutton(position_frame, text=option, 
                                  variable=self.r9_vars[i][option],
                                  font=('Microsoft YaHei UI', 8))
                cb.grid(row=0, column=j, padx=2, pady=2)
        
        # 设置列权重
        for i in range(4):
            filter_frame.columnconfigure(i, weight=1)
        
        # 操作按钮
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="应用过滤", command=self.apply_filter).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="清空结果", command=self.clear_result).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="比分频率缩水", command=self.show_frequency_filter).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="自由缩水", command=self.show_free_shrink_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="一键恢复", command=self.undo_last_operation).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="复制结果", command=self.copy_result).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="导出文本", command=self.export_result).pack(side=tk.LEFT)
    
    def _create_result_ui(self, parent):
        """创建结果显示界面"""
        result_frame = ttk.LabelFrame(parent, text="过滤结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=20, bg='white', fg='black')
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        self.result_stats = ttk.Label(result_frame, text="结果数据：0 条", 
                                    font=('Microsoft YaHei UI', 10))
        self.result_stats.pack(anchor=tk.W, pady=(5, 0))
    
    def load_data(self):
        """加载数据到投注区"""
        try:
            input_data = self.input_text.get("1.0", tk.END).strip()
            if not input_data:
                messagebox.showwarning("警告", "请输入投注数据")
                return
            
            lines = input_data.split('\n')
            valid_data = []
            
            for line in lines:
                line = line.strip()
                if line and self._check_bet_format(line):
                    valid_data.append(line)
            
            if not valid_data:
                messagebox.showwarning("警告", "没有有效的投注数据")
                return
            
            # 更新投注区
            self.betting_text.delete("1.0", tk.END)
            self.betting_text.insert("1.0", '\n'.join(valid_data))
            
            # 更新数据
            self.betting_data = valid_data.copy()
            self.original_data = valid_data.copy()
            self.filtered_data = valid_data.copy()
            
            # 更新统计
            self.stats_label.config(text=f"数据统计：{len(valid_data)} 条")
            self.betting_stats.config(text=f"投注数据：{len(valid_data)} 条")
            self.result_stats.config(text=f"结果数据：{len(valid_data)} 条")
            
            messagebox.showinfo("成功", f"成功加载 {len(valid_data)} 条投注数据到投注区")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败：{e}")
    
    def _check_bet_format(self, bet):
        """检查投注格式"""
        # 任九：14个位置，每个位置是3、1、0或*
        if len(bet) != 14:
            return False
        
        for char in bet:
            if char not in ['3', '1', '0', '*']:
                return False
        
        return True
    
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
        self.result_stats.config(text="结果数据：0 条")
    
    def apply_filter(self):
        """应用过滤器"""
        if not self.betting_data:
            messagebox.showwarning("警告", "请先加载投注数据")
            return
        
        # 保存当前状态到历史
        self.history.append(self.filtered_data.copy())
        
        # 应用过滤
        filtered_data = []
        for bet in self.betting_data:
            if self._check_r9_filter(bet):
                filtered_data.append(bet)
        
        # 更新结果
        self.filtered_data = filtered_data
        self._display_results()
        
        original_count = len(self.betting_data)
        filtered_count = len(filtered_data)
        messagebox.showinfo("过滤完成", f"从 {original_count} 条投注数据中筛选出 {filtered_count} 条结果")
    
    def _check_r9_filter(self, bet):
        """检查任九过滤条件"""
        # 解析投注数据（14个位置）
        for i in range(14):
            position_result = bet[i]
            
            # 检查是否有任何投注选项被选中
            any_selected = any(self.r9_vars[i][result].get() for result in ['3', '1', '0', '*'])
            
            if any_selected:  # 如果有选项被选中
                if not self.r9_vars[i][position_result].get():
                    return False
        
        return True
    
    def _display_results(self):
        """显示过滤结果"""
        self.result_text.delete("1.0", tk.END)
        
        if self.filtered_data:
            # 按升序排列
            sorted_data = sorted(self.filtered_data)
            self.result_text.insert("1.0", '\n'.join(sorted_data))
            self.result_stats.config(text=f"结果数据：{len(sorted_data)} 条")
        else:
            self.result_stats.config(text="结果数据：0 条")
    
    def clear_result(self):
        """清空结果"""
        self.result_text.delete("1.0", tk.END)
        self.filtered_data = []
        self.result_stats.config(text="结果数据：0 条")
    
    def copy_result(self):
        """复制结果"""
        if self.filtered_data:
            # 按升序排列
            sorted_data = sorted(self.filtered_data)
            result_text = '\n'.join(sorted_data)
            self.root.clipboard_clear()
            self.root.clipboard_append(result_text)
            messagebox.showinfo("成功", f"已复制 {len(sorted_data)} 条结果到剪贴板")
        elif self.betting_data:
            # 如果没有过滤结果，复制投注数据
            sorted_data = sorted(self.betting_data)
            result_text = '\n'.join(sorted_data)
            self.root.clipboard_clear()
            self.root.clipboard_append(result_text)
            messagebox.showinfo("成功", f"已复制 {len(sorted_data)} 条投注数据到剪贴板")
        else:
            messagebox.showwarning("警告", "没有数据可复制")
    
    def export_result(self):
        """导出结果"""
        if self.filtered_data:
            # 按升序排列
            sorted_data = sorted(self.filtered_data)
            filename = f"任九过滤结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"任九过滤结果\n")
                f.write(f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"结果数量：{len(sorted_data)} 条\n")
                f.write("=" * 50 + "\n")
                f.write('\n'.join(sorted_data))
            messagebox.showinfo("成功", f"已导出 {len(sorted_data)} 条结果到 {filename}")
        elif self.betting_data:
            # 如果没有过滤结果，导出投注数据
            sorted_data = sorted(self.betting_data)
            filename = f"任九投注数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"任九投注数据\n")
                f.write(f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"数据数量：{len(sorted_data)} 条\n")
                f.write("=" * 50 + "\n")
                f.write('\n'.join(sorted_data))
            messagebox.showinfo("成功", f"已导出 {len(sorted_data)} 条投注数据到 {filename}")
        else:
            messagebox.showwarning("警告", "没有数据可导出")
    
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
                
        except Exception as e:
            messagebox.showerror("错误", f"刷新期号失败：{e}")
    
    def get_match_details(self):
        """获取对阵详情"""
        try:
            period = self.period_var.get().strip()
            if not period:
                messagebox.showwarning("警告", "请先选择期号")
                return
            
            # 调用体彩API获取对阵详情
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
                
        except Exception as e:
            messagebox.showerror("错误", f"获取详情失败：{e}")
    
    def _display_match_details(self, match_info):
        """显示对阵详情"""
        try:
            # 清空详情显示
            self.details_text.delete("1.0", tk.END)
            
            # 获取基本信息
            period = match_info.get('lotteryDrawNum', '未知')
            sell_end_time = match_info.get('sellEndTime', '未知')
            
            details = f"第{period}期尚未开奖\n"
            details += f"销售截止: {sell_end_time}\n"
            details += f"对阵信息:\n"
            
            # 显示对阵信息
            match_list = match_info.get('matchList', [])
            self.match_data = match_list
            
            for match in match_list[:14]:  # 显示前14场
                # 正确解析API数据
                match_num = match.get('matchNum', '未知')
                master_team = match.get('masterTeamName', '未知')
                guest_team = match.get('guestTeamName', '未知')
                league = match.get('matchName', '未知')  # 联赛名称
                match_time = match.get('startTime', '未知')  # 开赛时间
                
                print(f"解析第{match_num}场: matchNum={match_num}, 主队={master_team}, 客队={guest_team}, 联赛={league}")
                
                details += f"第{match_num}场: {master_team} vs {guest_team} -\n"
                
                # 更新表格显示
                self._update_match_table(match_num, master_team, guest_team, league, match_time)
            
            self.details_text.insert("1.0", details)
            
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
                
                print(f"更新第{game_idx+1}场: {teams_text} ({league})")
                
        except Exception as e:
            print(f"更新表格失败：{e}")
    
    def generate_bets(self):
        """生成投注"""
        try:
            # 收集所有选择的投注
            all_selections = []
            for game_idx in range(14):
                game_selections = []
                for option in ['3', '1', '0', '*']:
                    if self.betting_selections[game_idx][option].get():
                        game_selections.append(option)
                
                if not game_selections:
                    messagebox.showwarning("警告", f"请为第{game_idx+1}场选择至少一个投注选项")
                    return
                
                all_selections.append(game_selections)
            
            # 生成所有可能的投注组合
            bet_combinations = self._generate_all_combinations(all_selections)
            
            # 格式化投注数据
            bet_strings = []
            for combination in bet_combinations:
                bet_string = ''.join(combination)
                bet_strings.append(bet_string)
            
            # 更新投注区
            self.betting_text.delete("1.0", tk.END)
            self.betting_text.insert("1.0", '\n'.join(bet_strings))
            
            # 更新数据
            self.betting_data = bet_strings.copy()
            self.original_data = bet_strings.copy()
            self.filtered_data = bet_strings.copy()
            
            # 更新统计
            self.betting_stats.config(text=f"投注数据：{len(bet_strings)} 条")
            self.result_stats.config(text=f"结果数据：{len(bet_strings)} 条")
            
            messagebox.showinfo("成功", f"已生成 {len(bet_strings)} 条投注数据")
            
        except Exception as e:
            messagebox.showerror("错误", f"生成投注失败：{e}")
    
    def _generate_all_combinations(self, selections):
        """生成所有投注组合"""
        if not selections:
            return []
        
        if len(selections) == 1:
            return [[option] for option in selections[0]]
        
        result = []
        for option in selections[0]:
            for sub_combination in self._generate_all_combinations(selections[1:]):
                result.append([option] + sub_combination)
        
        return result
    
    def show_frequency_filter(self):
        """显示比分频率缩水窗口"""
        if not self.betting_data and not self.filtered_data:
            messagebox.showwarning("警告", "请先加载投注数据")
            return
        
        # 使用过滤结果，如果没有则使用投注数据
        data_source = self.filtered_data if self.filtered_data else self.betting_data
        
        # 创建频率统计
        freq_stats = {}
        for bet in data_source:
            for i in range(14):
                position_result = bet[i]
                key = f"第{i+1}场_{position_result}"
                freq_stats[key] = freq_stats.get(key, 0) + 1
        
        # 创建频率调整窗口
        freq_window = tk.Toplevel(self.root)
        freq_window.title("任九频率缩水")
        freq_window.geometry("1000x700")
        freq_window.transient(self.root)
        freq_window.grab_set()
        
        # 主框架
        main_frame = ttk.Frame(freq_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="任九频率缩水",
                               font=('Microsoft YaHei UI', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 频率调整区域
        freq_frame = ttk.LabelFrame(main_frame, text="频率调整", padding="10")
        freq_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 创建频率调整控件
        freq_vars = {}
        for i in range(14):
            game_frame = ttk.LabelFrame(freq_frame, text=f"第{i+1}场", padding="5")
            game_frame.grid(row=i//4, column=i%4, padx=5, pady=5, sticky="ew")
            
            r9_options = ['3', '1', '0', '*']
            for j, option in enumerate(r9_options):
                key = f"第{i+1}场_{option}"
                current_freq = freq_stats.get(key, 0)
                
                option_frame = ttk.Frame(game_frame)
                option_frame.grid(row=0, column=j, padx=2, pady=2)
                
                ttk.Label(option_frame, text=option, font=('Microsoft YaHei UI', 8)).pack()
                ttk.Label(option_frame, text=f"当前:{current_freq}", font=('Microsoft YaHei UI', 7)).pack()
                
                var = tk.StringVar(value=str(current_freq))
                freq_vars[key] = var
                
                entry = ttk.Entry(option_frame, textvariable=var, width=6)
                entry.pack()
        
        # 设置列权重
        for i in range(4):
            freq_frame.columnconfigure(i, weight=1)
        
        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="应用频率缩水", 
                  command=lambda: self._apply_frequency_filter(freq_vars, freq_window)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=freq_window.destroy).pack(side=tk.LEFT)
    
    def _apply_frequency_filter(self, freq_vars, window):
        """应用频率过滤"""
        try:
            # 保存当前状态到历史
            self.history.append(self.filtered_data.copy())
            
            # 使用过滤结果，如果没有则使用投注数据
            data_source = self.filtered_data if self.filtered_data else self.betting_data
            
            filtered_data = []
            for bet in data_source:
                include_bet = True
                for i in range(14):
                    position_result = bet[i]
                    key = f"第{i+1}场_{position_result}"
                    target_freq = int(freq_vars[key].get() or 0)
                    
                    # 计算当前该结果的频率
                    current_count = sum(1 for b in filtered_data if b[i] == position_result)
                    
                    if current_count >= target_freq:
                        include_bet = False
                        break
                
                if include_bet:
                    filtered_data.append(bet)
            
            # 更新结果
            self.filtered_data = filtered_data
            self._display_results()
            
            window.destroy()
            messagebox.showinfo("成功", f"频率缩水完成，剩余 {len(filtered_data)} 条数据")
            
        except Exception as e:
            messagebox.showerror("错误", f"频率缩水失败：{e}")
    
    def show_free_shrink_dialog(self):
        """显示自由缩水对话框"""
        if not self.betting_data and not self.filtered_data:
            messagebox.showwarning("警告", "请先加载投注数据")
            return
        
        # 使用过滤结果，如果没有则使用投注数据
        data_source = self.filtered_data if self.filtered_data else self.betting_data
        current_count = len(data_source)
        
        # 创建对话框
        shrink_window = tk.Toplevel(self.root)
        shrink_window.title("自由缩水")
        shrink_window.geometry("400x300")
        shrink_window.transient(self.root)
        shrink_window.grab_set()
        
        # 主框架
        main_frame = ttk.Frame(shrink_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="自由缩水", font=('Microsoft YaHei UI', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 当前数据量
        current_label = ttk.Label(main_frame, text=f"当前数据量：{current_count} 条", 
                                font=('Microsoft YaHei UI', 12))
        current_label.pack(pady=(0, 20))
        
        # 目标数量输入
        ttk.Label(main_frame, text="目标数量：", font=('Microsoft YaHei UI', 10)).pack(anchor=tk.W)
        target_var = tk.StringVar()
        target_entry = ttk.Entry(main_frame, textvariable=target_var, width=20)
        target_entry.pack(pady=(5, 20))
        
        # 选择方法
        method_var = tk.StringVar(value="random")
        methods = [
            ("random", "随机选择"),
            ("odd", "奇数序号选择"),
            ("even", "偶数序号选择"),
            ("uniform", "均匀选择(保持频率分布)")
        ]
        
        ttk.Label(main_frame, text="选择方法：", font=('Microsoft YaHei UI', 10)).pack(anchor=tk.W)
        for value, text in methods:
            ttk.Radiobutton(main_frame, text=text, variable=method_var, value=value).pack(anchor=tk.W)
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(btn_frame, text="应用缩水", 
                  command=lambda: self._apply_free_shrink(target_var.get(), method_var.get(), shrink_window)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=shrink_window.destroy).pack(side=tk.LEFT)
    
    def _apply_free_shrink(self, target_str, method, window):
        """应用自由缩水"""
        try:
            target_count = int(target_str)
            if target_count <= 0:
                messagebox.showerror("错误", "目标数量必须大于0")
                return
            
            # 使用过滤结果，如果没有则使用投注数据
            data_source = self.filtered_data if self.filtered_data else self.betting_data
            current_count = len(data_source)
            
            if target_count >= current_count:
                messagebox.showwarning("警告", "目标数量不能大于等于当前数量")
                return
            
            # 保存当前状态到历史
            self.history.append(self.filtered_data.copy())
            
            # 根据方法选择数据
            if method == "random":
                selected_data = random.sample(data_source, target_count)
            elif method == "odd":
                selected_data = [data_source[i] for i in range(0, len(data_source), 2)][:target_count]
            elif method == "even":
                selected_data = [data_source[i] for i in range(1, len(data_source), 2)][:target_count]
            elif method == "uniform":
                # 均匀选择，保持频率分布
                selected_data = self._uniform_select(data_source, target_count)
            else:
                selected_data = random.sample(data_source, target_count)
            
            # 更新结果
            self.filtered_data = selected_data
            self._display_results()
            
            window.destroy()
            messagebox.showinfo("成功", f"自由缩水完成，从 {current_count} 条减少到 {len(selected_data)} 条")
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
        except Exception as e:
            messagebox.showerror("错误", f"自由缩水失败：{e}")
    
    def _uniform_select(self, data, target_count):
        """均匀选择，保持频率分布"""
        if target_count >= len(data):
            return data
        
        # 按升序排列
        sorted_data = sorted(data)
        
        # 均匀选择
        step = len(sorted_data) / target_count
        selected = []
        for i in range(target_count):
            index = int(i * step)
            selected.append(sorted_data[index])
        
        return selected
    
    def undo_last_operation(self):
        """撤销上一次操作"""
        if not self.history:
            messagebox.showwarning("警告", "没有可撤销的操作")
            return
        
        # 恢复上一次状态
        self.filtered_data = self.history.pop()
        self._display_results()
        
        messagebox.showinfo("成功", "已撤销上一次操作")
    
    def run(self):
        """运行程序"""
        self.root.mainloop()

if __name__ == "__main__":
    app = R9Filter()
    app.run()
