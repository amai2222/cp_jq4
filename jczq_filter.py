import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime, timedelta
import threading
import json


class JCZQFilter:
    def __init__(self, root):
        self.root = root
        self.root.title("竞彩足球投注过滤器")
        self.root.geometry("1400x800")
        
        # API配置 - 基于bifen.py的逻辑
        self.API_MATCH_LIST = "https://sports.163.com/caipiao/api/web/match/list/jingcai/matchList/1?days={}"
        self.API_LIVE_SCORES = "https://sports.163.com/caipiao/api/web/match/list/getMatchInfoList/1?matchInfoIds={}"
        
        # 备用API - 体彩官方API
        self.API_SPORTTERY_JCZQ = "https://webapi.sporttery.cn/gateway/lottery/getFootBallMatchV1.qry"
        
        # 数据存储
        self.match_data = []
        self.betting_data = []
        self.filtered_data = []
        self.operation_history = []
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧面板 - 对阵信息
        left_frame = ttk.LabelFrame(main_frame, text="对阵信息", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 对阵控制区域
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 日期选择
        ttk.Label(control_frame, text="比赛日期:").pack(side=tk.LEFT, padx=(0, 5))
        self.date_var = tk.StringVar()
        self.date_combo = ttk.Combobox(control_frame, textvariable=self.date_var, width=12, state="readonly")
        self.date_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # 刷新按钮
        ttk.Button(control_frame, text="刷新对阵", command=self.refresh_matches).pack(side=tk.LEFT, padx=(0, 10))
        
        # 对阵表格
        self.create_match_table(left_frame)
        
        # 右侧面板 - 投注和过滤
        right_frame = ttk.LabelFrame(main_frame, text="投注过滤", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 投注区域
        betting_frame = ttk.LabelFrame(right_frame, text="投注区域", padding="5")
        betting_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 投注文本框
        self.betting_text = tk.Text(betting_frame, height=8, font=('Consolas', 10))
        betting_scroll = ttk.Scrollbar(betting_frame, orient=tk.VERTICAL, command=self.betting_text.yview)
        self.betting_text.configure(yscrollcommand=betting_scroll.set)
        
        self.betting_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        betting_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 过滤控制区域
        self.create_filter_controls(right_frame)
        
        # 状态栏
        self.status_var = tk.StringVar(value="准备就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 初始化日期
        self.init_date_options()
        
    def create_match_table(self, parent):
        """创建对阵表格"""
        # 表格框架
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        columns = ("场次", "主队", "客队", "开赛时间", "状态", "胜平负", "让球胜平负", "比分", "总进球", "半全场")
        self.match_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # 设置列标题和宽度
        column_widths = {"场次": 60, "主队": 120, "客队": 120, "开赛时间": 120, "状态": 80, 
                        "胜平负": 100, "让球胜平负": 100, "比分": 100, "总进球": 100, "半全场": 100}
        
        for col in columns:
            self.match_tree.heading(col, text=col)
            self.match_tree.column(col, width=column_widths[col], anchor="center")
        
        # 滚动条
        match_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.match_tree.yview)
        self.match_tree.configure(yscrollcommand=match_scroll.set)
        
        # 布局
        self.match_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        match_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.match_tree.bind("<<TreeviewSelect>>", self.on_match_select)
        self.match_tree.bind("<Double-1>", self.on_match_double_click)
        
    def create_filter_controls(self, parent):
        """创建过滤控制区域"""
        # 过滤按钮框架
        filter_btn_frame = ttk.Frame(parent)
        filter_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 过滤按钮
        ttk.Button(filter_btn_frame, text="开始过滤", command=self.start_filter, 
                  style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(filter_btn_frame, text="比分频率缩水", command=self.show_frequency_filter, 
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(filter_btn_frame, text="自由缩水", command=self.show_free_shrink_dialog, 
                  style='Success.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(filter_btn_frame, text="一键恢复", command=self.undo_last_operation, 
                  style='Secondary.TButton').pack(side=tk.LEFT)
        
        # 过滤结果显示
        result_frame = ttk.LabelFrame(parent, text="过滤结果", padding="5")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_text = tk.Text(result_frame, height=6, font=('Consolas', 10))
        result_scroll = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=result_scroll.set)
        
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
    def init_date_options(self):
        """初始化日期选项"""
        dates = []
        for i in range(7):  # 未来7天
            date = datetime.now() + timedelta(days=i)
            dates.append(date.strftime("%Y-%m-%d"))
        
        self.date_combo['values'] = dates
        self.date_combo.current(0)
        
    def refresh_matches(self):
        """刷新对阵信息"""
        date = self.date_var.get()
        if not date:
            messagebox.showwarning("警告", "请选择比赛日期")
            return
            
        self.status_var.set("正在获取对阵信息...")
        
        # 在新线程中获取数据
        threading.Thread(target=self.fetch_matches_worker, args=(date,), daemon=True).start()
        
    def fetch_matches_worker(self, date):
        """获取对阵信息的工作线程"""
        try:
            # 计算days参数（相对于今天的天数差）
            target_date = datetime.strptime(date, "%Y-%m-%d")
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            days_diff = (target_date - today).days
            
            # 调用API获取对阵列表
            list_url = self.API_MATCH_LIST.format(days_diff)
            print(f"请求URL: {list_url}")
            
            # 添加请求头，模拟浏览器请求
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://sports.163.com/',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }
            
            list_response = requests.get(list_url, headers=headers, timeout=10)
            list_response.raise_for_status()
            list_data = list_response.json()
            
            print(f"API响应状态码: {list_response.status_code}")
            print(f"API响应内容: {list_data}")
            
            # 处理不同的响应码
            if list_data.get('code') == 200:
                matches = list_data.get('data', [])
                if matches and isinstance(matches, list):
                    # 处理网易API的竞彩数据
                    processed_matches = []
                    for i, match in enumerate(matches):
                        match_info = self.process_163_jczq_data(match, i + 1)
                        processed_matches.append(match_info)
                    
                    # 更新界面
                    self.root.after(0, self.update_match_table, processed_matches)
                    return
            elif list_data.get('code') == 405:
                # 405错误，可能是API限制，尝试使用体彩官方API
                self.root.after(0, lambda: messagebox.showwarning("警告", "网易API访问受限，尝试使用体彩官方API"))
                self.try_sporttery_api(date)
                return
            else:
                error_msg = f"获取对阵失败：{list_data.get('msg', '未知错误')} (code: {list_data.get('code')})"
                print(f"API错误: {error_msg}")
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
                return
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"获取对阵失败：{e}"))
        finally:
            self.root.after(0, lambda: self.status_var.set("准备就绪"))
            
    def try_sporttery_api(self, date):
        """尝试使用体彩官方API获取竞彩数据"""
        try:
            # 体彩官方API参数
            params = {
                'param': '90,0',  # 竞彩足球参数
                'lotteryDrawNum': '',  # 期号，空表示当前期
                'sellStatus': '0',  # 销售状态
                'termLimits': '10'  # 期数限制
            }
            
            print(f"尝试体彩官方API: {self.API_SPORTTERY_JCZQ}")
            response = requests.get(self.API_SPORTTERY_JCZQ, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            print(f"体彩API响应: {data}")
            
            if 'value' in data and 'sfcMatch' in data['value']:
                # 体彩API返回的是胜负彩数据，不是竞彩数据
                sfc_data = data['value']['sfcMatch']
                match_list = sfc_data.get('matchList', [])
                
                if match_list:
                    # 处理体彩API的数据格式
                    processed_matches = []
                    for i, match in enumerate(match_list):
                        match_info = self.process_sporttery_match_data(match, i + 1)
                        processed_matches.append(match_info)
                    
                    # 更新界面
                    self.root.after(0, self.update_match_table, processed_matches)
                    return
                    
            self.root.after(0, lambda: messagebox.showinfo("提示", "体彩官方API也没有找到竞彩数据"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"体彩官方API获取失败：{e}"))
            
    def process_sporttery_match_data(self, match, sequence):
        """处理体彩官方API的比赛数据"""
        match_id = str(match.get('infohubMatchId', ''))
        home_team = match.get('masterTeamName', 'N/A')
        away_team = match.get('guestTeamName', 'N/A')
        start_time = match.get('startTime', '')
        match_num = match.get('matchNum', str(sequence))
        
        # 格式化开赛时间
        if start_time:
            try:
                dt = datetime.strptime(start_time, "%Y-%m-%d")
                start_time = dt.strftime("%m-%d")
            except:
                pass
        
        return {
            'match_id': match_id,
            'sequence': sequence,
            'match_num': match_num,
            'home_team': home_team,
            'away_team': away_team,
            'start_time': start_time,
            'status': '未开赛',
            'status_category': 'not_started',
            'raw_data': match
        }
        
    def process_163_jczq_data(self, match, sequence):
        """处理网易体育竞彩数据"""
        match_id = str(match.get('matchInfoId', ''))
        home_team = match.get('homeTeam', {}).get('teamName', 'N/A')
        away_team = match.get('guestTeam', {}).get('teamName', 'N/A')
        start_time = match.get('startTime', '')
        
        # 获取API返回的实际场次号
        api_match_num = match.get('jcNum') or match.get('matchNum', '')
        if api_match_num:
            match_num = str(api_match_num)
        else:
            match_num = str(sequence)
        
        # 获取比赛状态
        live_score_details = match.get('footballLiveScore', {})
        status_text, status_category = self.get_status_info(live_score_details)
        
        # 格式化开赛时间
        if start_time:
            try:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                start_time = dt.strftime("%m-%d %H:%M")
            except:
                pass
        
        return {
            'match_id': match_id,
            'sequence': sequence,
            'match_num': match_num,
            'home_team': home_team,
            'away_team': away_team,
            'start_time': start_time,
            'status': status_text,
            'status_category': status_category,
            'raw_data': match
        }
            
    def process_match_data(self, match, live_data_map, sequence):
        """处理单场比赛数据"""
        match_id = str(match.get('matchInfoId', ''))
        home_team = match.get('homeTeam', {}).get('teamName', 'N/A')
        away_team = match.get('guestTeam', {}).get('teamName', 'N/A')
        start_time = match.get('startTime', '')
        
        # 获取API返回的实际场次号
        api_match_num = match.get('jcNum') or match.get('matchNum', '')
        if api_match_num:
            match_num = str(api_match_num)
        else:
            match_num = str(sequence)  # 如果没有场次号，使用序号
        
        # 获取比赛状态
        live_info = live_data_map.get(match_id, {})
        live_score_details = live_info.get('footballLiveScore') if live_info else match.get('footballLiveScore', {})
        
        status_text, status_category = self.get_status_info(live_score_details)
        
        # 格式化开赛时间
        if start_time:
            try:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                start_time = dt.strftime("%m-%d %H:%M")
            except:
                pass
        
        return {
            'match_id': match_id,
            'sequence': sequence,
            'match_num': match_num,  # 使用API返回的场次号
            'home_team': home_team,
            'away_team': away_team,
            'start_time': start_time,
            'status': status_text,
            'status_category': status_category,
            'raw_data': match
        }
        
    def get_status_info(self, live_score_details):
        """获取比赛状态信息"""
        if not live_score_details:
            return "未开赛", "not_started"
            
        status_text = live_score_details.get('status', '未知')
        status_enum = live_score_details.get('statusEnum')
        
        if status_enum in [2, 3, 4] or '′' in status_text:
            category = "in_progress"
        elif status_enum in [8, 5, 6, 7]:
            category = "finished"
        else:
            category = "not_started"
            
        if status_enum == 3:
            status_text = "中场"
        elif status_enum == 8:
            status_text = "完"
            
        return status_text, category
        
    def update_match_table(self, matches):
        """更新对阵表格"""
        # 清空现有数据
        for item in self.match_tree.get_children():
            self.match_tree.delete(item)
            
        self.match_data = matches
        
        # 只显示未开赛的比赛
        for match in matches:
            if match['status_category'] == 'not_started':
                # 创建投注选择变量
                match['betting_vars'] = self.create_betting_vars()
                
                # 插入表格行，使用API返回的场次号
                self.match_tree.insert("", "end", values=(
                    match['match_num'],  # 使用API返回的场次号
                    match['home_team'],
                    match['away_team'],
                    match['start_time'],
                    match['status'],
                    "请选择",  # 胜平负
                    "请选择",  # 让球胜平负
                    "请选择",  # 比分
                    "请选择",  # 总进球
                    "请选择"   # 半全场
                ))
                
    def create_betting_vars(self):
        """创建投注选择变量"""
        return {
            'spf': {'3': tk.BooleanVar(), '1': tk.BooleanVar(), '0': tk.BooleanVar()},  # 胜平负
            'rqspf': {'3': tk.BooleanVar(), '1': tk.BooleanVar(), '0': tk.BooleanVar()},  # 让球胜平负
            'bf': {},  # 比分
            'zjq': {},  # 总进球
            'bqc': {}   # 半全场
        }
        
    def on_match_select(self, event):
        """比赛选择事件处理"""
        selection = self.match_tree.selection()
        if not selection:
            return
            
        # 这里可以添加比赛详情显示或投注选择界面
        pass
        
    def on_match_double_click(self, event):
        """比赛双击事件处理 - 打开投注选择对话框"""
        selection = self.match_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.match_tree.item(item, "values")
        
        # 通过场次号找到对应的比赛
        match_num = values[0]
        match_idx = -1
        for i, match in enumerate(self.match_data):
            if match['match_num'] == match_num:
                match_idx = i
                break
        
        if match_idx >= 0 and match_idx < len(self.match_data):
            match = self.match_data[match_idx]
            self.show_betting_dialog(match, match_idx)
        
    def show_betting_dialog(self, match, match_idx):
        """显示投注选择对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"投注选择 - {match['home_team']} vs {match['away_team']}")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 主框架
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 胜平负
        spf_frame = ttk.LabelFrame(main_frame, text="胜平负", padding="5")
        spf_frame.pack(fill=tk.X, pady=(0, 10))
        
        spf_vars = {}
        for i, option in enumerate(["胜", "平", "负"]):
            var = tk.BooleanVar()
            spf_vars[option] = var
            ttk.Checkbutton(spf_frame, text=option, variable=var).grid(row=0, column=i, padx=10, sticky="w")
        
        # 让球胜平负
        rqspf_frame = ttk.LabelFrame(main_frame, text="让球胜平负", padding="5")
        rqspf_frame.pack(fill=tk.X, pady=(0, 10))
        
        rqspf_vars = {}
        for i, option in enumerate(["让胜", "让平", "让负"]):
            var = tk.BooleanVar()
            rqspf_vars[option] = var
            ttk.Checkbutton(rqspf_frame, text=option, variable=var).grid(row=0, column=i, padx=10, sticky="w")
        
        # 比分
        bf_frame = ttk.LabelFrame(main_frame, text="比分", padding="5")
        bf_frame.pack(fill=tk.X, pady=(0, 10))
        
        bf_vars = {}
        bf_options = ["1:0", "2:0", "2:1", "3:0", "3:1", "3:2", "4:0", "4:1", "4:2", "5:0", "5:1", "5:2", "胜其他",
                      "0:0", "1:1", "2:2", "3:3", "平其他",
                      "0:1", "0:2", "1:2", "0:3", "1:3", "2:3", "0:4", "1:4", "2:4", "0:5", "1:5", "2:5", "负其他"]
        
        for i, option in enumerate(bf_options):
            var = tk.BooleanVar()
            bf_vars[option] = var
            row, col = i // 6, i % 6
            ttk.Checkbutton(bf_frame, text=option, variable=var).grid(row=row, column=col, padx=5, pady=2, sticky="w")
        
        # 总进球
        zjq_frame = ttk.LabelFrame(main_frame, text="总进球", padding="5")
        zjq_frame.pack(fill=tk.X, pady=(0, 10))
        
        zjq_vars = {}
        for i, option in enumerate(["0", "1", "2", "3", "4", "5", "6", "7+"]):
            var = tk.BooleanVar()
            zjq_vars[option] = var
            ttk.Checkbutton(zjq_frame, text=option, variable=var).grid(row=0, column=i, padx=10, sticky="w")
        
        # 半全场
        bqc_frame = ttk.LabelFrame(main_frame, text="半全场", padding="5")
        bqc_frame.pack(fill=tk.X, pady=(0, 10))
        
        bqc_vars = {}
        bqc_options = ["胜胜", "胜平", "胜负", "平胜", "平平", "平负", "负胜", "负平", "负负"]
        for i, option in enumerate(bqc_options):
            var = tk.BooleanVar()
            bqc_vars[option] = var
            row, col = i // 3, i % 3
            ttk.Checkbutton(bqc_frame, text=option, variable=var).grid(row=row, column=col, padx=10, sticky="w")
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        def save_betting():
            # 保存投注选择
            match['betting_vars'] = {
                'spf': spf_vars,
                'rqspf': rqspf_vars,
                'bf': bf_vars,
                'zjq': zjq_vars,
                'bqc': bqc_vars
            }
            
            # 更新表格显示
            self.update_match_display(match_idx)
            dialog.destroy()
        
        ttk.Button(btn_frame, text="确定", command=save_betting).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT)
        
    def update_match_display(self, match_idx):
        """更新比赛显示"""
        if match_idx >= len(self.match_data):
            return
            
        match = self.match_data[match_idx]
        betting_vars = match.get('betting_vars', {})
        
        # 更新表格中的投注显示
        item_id = self.match_tree.get_children()[match_idx]
        values = list(self.match_tree.item(item_id, "values"))
        
        # 更新各列显示
        values[5] = self.get_selected_options(betting_vars.get('spf', {}), ["胜", "平", "负"])
        values[6] = self.get_selected_options(betting_vars.get('rqspf', {}), ["让胜", "让平", "让负"])
        values[7] = self.get_selected_options(betting_vars.get('bf', {}), ["1:0", "2:0", "2:1", "3:0", "3:1", "3:2", "4:0", "4:1", "4:2", "5:0", "5:1", "5:2", "胜其他", "0:0", "1:1", "2:2", "3:3", "平其他", "0:1", "0:2", "1:2", "0:3", "1:3", "2:3", "0:4", "1:4", "2:4", "0:5", "1:5", "2:5", "负其他"])
        values[8] = self.get_selected_options(betting_vars.get('zjq', {}), ["0", "1", "2", "3", "4", "5", "6", "7+"])
        values[9] = self.get_selected_options(betting_vars.get('bqc', {}), ["胜胜", "胜平", "胜负", "平胜", "平平", "平负", "负胜", "负平", "负负"])
        
        self.match_tree.item(item_id, values=values)
        
    def get_selected_options(self, vars_dict, options):
        """获取已选择的选项"""
        selected = []
        for option in options:
            if option in vars_dict and vars_dict[option].get():
                selected.append(option)
        return ",".join(selected) if selected else "未选择"
        
    def start_filter(self):
        """开始过滤"""
        if not self.match_data:
            messagebox.showwarning("警告", "请先获取对阵信息")
            return
            
        # 收集所有投注选择
        selected_matches = []
        for i, match in enumerate(self.match_data):
            betting_vars = match.get('betting_vars', {})
            if any(any(var.get() for var in game_vars.values()) for game_vars in betting_vars.values()):
                selected_matches.append(match)
        
        if not selected_matches:
            messagebox.showwarning("警告", "请先选择投注选项")
            return
            
        # 生成投注组合
        self.generate_betting_combinations(selected_matches)
        
    def generate_betting_combinations(self, selected_matches):
        """生成投注组合"""
        try:
            from itertools import product
            
            # 为每场比赛生成所有可能的投注组合
            all_combinations = []
            
            for match in selected_matches:
                match_combinations = []
                betting_vars = match.get('betting_vars', {})
                
                # 胜平负组合
                spf_selected = [opt for opt, var in betting_vars.get('spf', {}).items() if var.get()]
                if spf_selected:
                    match_combinations.append([f"SPF:{opt}" for opt in spf_selected])
                
                # 让球胜平负组合
                rqspf_selected = [opt for opt, var in betting_vars.get('rqspf', {}).items() if var.get()]
                if rqspf_selected:
                    match_combinations.append([f"RQSPF:{opt}" for opt in rqspf_selected])
                
                # 比分组合
                bf_selected = [opt for opt, var in betting_vars.get('bf', {}).items() if var.get()]
                if bf_selected:
                    match_combinations.append([f"BF:{opt}" for opt in bf_selected])
                
                # 总进球组合
                zjq_selected = [opt for opt, var in betting_vars.get('zjq', {}).items() if var.get()]
                if zjq_selected:
                    match_combinations.append([f"ZJQ:{opt}" for opt in zjq_selected])
                
                # 半全场组合
                bqc_selected = [opt for opt, var in betting_vars.get('bqc', {}).items() if var.get()]
                if bqc_selected:
                    match_combinations.append([f"BQC:{opt}" for opt in bqc_selected])
                
                if match_combinations:
                    all_combinations.append(match_combinations)
            
            if not all_combinations:
                messagebox.showwarning("警告", "没有选择任何投注选项")
                return
            
            # 生成所有可能的组合
            betting_combinations = list(product(*all_combinations))
            
            # 显示结果
            self.display_betting_results(betting_combinations, selected_matches)
            
        except Exception as e:
            messagebox.showerror("错误", f"生成投注组合失败：{e}")
            
    def display_betting_results(self, combinations, selected_matches):
        """显示投注结果"""
        # 清空投注区域
        self.betting_text.delete("1.0", tk.END)
        
        # 显示统计信息
        total_combinations = len(combinations)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, f"投注统计：\n")
        self.result_text.insert(tk.END, f"选择场次：{len(selected_matches)}场\n")
        self.result_text.insert(tk.END, f"投注组合：{total_combinations}注\n")
        self.result_text.insert(tk.END, f"投注金额：{total_combinations * 2}元\n\n")
        
        # 显示投注组合
        self.betting_text.insert(tk.END, f"投注组合（共{total_combinations}注）：\n\n")
        
        for i, combination in enumerate(combinations, 1):
            bet_line = f"第{i}注："
            for match_idx, match_bets in enumerate(combination):
                match = selected_matches[match_idx]
                bet_line += f" {match['home_team']}vs{match['away_team']}("
                bet_line += ",".join(match_bets)
                bet_line += ")"
            bet_line += "\n"
            self.betting_text.insert(tk.END, bet_line)
            
        # 保存到历史记录
        self.operation_history.append({
            'type': 'generate_betting',
            'matches': selected_matches,
            'combinations': combinations,
            'timestamp': datetime.now()
        })
        
        self.status_var.set(f"生成投注完成，共{total_combinations}注")
        
    def show_frequency_filter(self):
        """显示比分频率过滤对话框"""
        if not hasattr(self, 'betting_data') or not self.betting_data:
            messagebox.showwarning("警告", "请先生成投注")
            return
            
        # 创建频率过滤对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("比分频率过滤")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 频率设置
        freq_frame = ttk.LabelFrame(main_frame, text="频率设置", padding="10")
        freq_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(freq_frame, text="最低频率阈值:").pack(anchor="w")
        threshold_var = tk.DoubleVar(value=0.1)
        ttk.Scale(freq_frame, from_=0.01, to=1.0, variable=threshold_var, orient="horizontal").pack(fill=tk.X, pady=5)
        
        ttk.Label(freq_frame, text="过滤模式:").pack(anchor="w", pady=(10, 0))
        filter_mode = tk.StringVar(value="remove_low")
        ttk.Radiobutton(freq_frame, text="移除低频", variable=filter_mode, value="remove_low").pack(anchor="w")
        ttk.Radiobutton(freq_frame, text="保留高频", variable=filter_mode, value="keep_high").pack(anchor="w")
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        def apply_frequency_filter():
            threshold = threshold_var.get()
            mode = filter_mode.get()
            
            # 这里实现频率过滤逻辑
            messagebox.showinfo("提示", f"频率过滤功能开发中...\n阈值：{threshold}\n模式：{mode}")
            dialog.destroy()
        
        ttk.Button(btn_frame, text="应用过滤", command=apply_frequency_filter).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT)
        
    def show_free_shrink_dialog(self):
        """显示自由缩水对话框"""
        if not hasattr(self, 'betting_data') or not self.betting_data:
            messagebox.showwarning("警告", "请先生成投注")
            return
            
        # 创建自由缩水对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("自由缩水")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 缩水设置
        shrink_frame = ttk.LabelFrame(main_frame, text="缩水设置", padding="10")
        shrink_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(shrink_frame, text="目标注数:").pack(anchor="w")
        target_var = tk.IntVar(value=100)
        ttk.Entry(shrink_frame, textvariable=target_var, width=20).pack(fill=tk.X, pady=5)
        
        ttk.Label(shrink_frame, text="缩水策略:").pack(anchor="w", pady=(10, 0))
        strategy = tk.StringVar(value="random")
        ttk.Radiobutton(shrink_frame, text="随机缩水", variable=strategy, value="random").pack(anchor="w")
        ttk.Radiobutton(shrink_frame, text="智能缩水", variable=strategy, value="smart").pack(anchor="w")
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        def apply_shrink():
            target = target_var.get()
            strategy_type = strategy.get()
            
            # 这里实现缩水逻辑
            messagebox.showinfo("提示", f"自由缩水功能开发中...\n目标：{target}注\n策略：{strategy_type}")
            dialog.destroy()
        
        ttk.Button(btn_frame, text="应用缩水", command=apply_shrink).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT)
        
    def undo_last_operation(self):
        """撤销上次操作"""
        if self.operation_history:
            last_operation = self.operation_history.pop()
            if last_operation['type'] == 'generate_betting':
                # 恢复投注数据
                self.betting_text.delete("1.0", tk.END)
                self.result_text.delete("1.0", tk.END)
                self.status_var.set("已撤销上次操作")
                messagebox.showinfo("提示", "已撤销上次投注生成操作")
            else:
                messagebox.showinfo("提示", "已撤销上次操作")
        else:
            messagebox.showinfo("提示", "没有可撤销的操作")


def main():
    root = tk.Tk()
    app = JCZQFilter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
