import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime
import threading
import traceback

class ScoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("网易彩票数据获取工具 (v8.0 - 精装修版)")
        self.geometry("800x600") # 窗口加宽以适应新表格

        # --- API 配置 ---
        self.API_GET_CURRENT_ISSUE = "https://sports.163.com/caipiao/api/web/jc/queryCurrentPeriod.html?gameEn={}"
        self.API_MATCH_LIST = {
            "jczq": "https://sports.163.com/caipiao/api/web/match/list/jingcai/matchList/1?days={}",
            "sfc": "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/sfc?degree={}",
            "bjdc": "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/bjdc?degree={}"
        }
        self.API_LIVE_SCORES = "https://sports.163.com/caipiao/api/web/match/list/getMatchInfoList/1?matchInfoIds={}"
        
        self.create_menu()

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tabs_info = {"竞彩": {"type": "jczq"}, "胜负彩": {"type": "sfc"}, "北单": {"type": "bjdc"}}
        for name, info in self.tabs_info.items():
            frame = self.create_tab(self.notebook, name, info["type"])
            self.notebook.add(frame, text=name)

        self.status_bar = tk.Label(self, text="准备就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        # 优化4：程序启动后延迟一点时间，自动加载第一个标签页的数据
        self.after(200, self.on_tab_change)

    def create_menu(self):
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="退出", command=self.quit)

    def create_tab(self, parent, name, lottery_type):
        frame = ttk.Frame(parent, padding="10")
        
        # --- Top control frame ---
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=5)
        label_text = "比赛日期:" if lottery_type == 'jczq' else "期号:"
        issue_label = ttk.Label(control_frame, text=label_text)
        issue_label.pack(side=tk.LEFT, padx=(0, 5))
        issue_var = tk.StringVar()
        issue_entry = ttk.Entry(control_frame, textvariable=issue_var, width=20)
        issue_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        fetch_button = ttk.Button(control_frame, text="刷新", 
                                  command=lambda: self.start_fetch_thread(lottery_type, issue_var))
        fetch_button.pack(side=tk.LEFT, padx=(10, 0))

        # --- Table/Treeview frame ---
        # 优化1：使用 ttk.Treeview 创建美观的表格
        columns = ('match_num', 'home_team', 'vs', 'away_team', 'score', 'status')
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        
        # 定义表头
        tree.heading('match_num', text='场次')
        tree.heading('home_team', text='主队')
        tree.heading('vs', text='')
        tree.heading('away_team', text='客队')
        tree.heading('score', text='比分')
        tree.heading('status', text='状态')
        
        # 定义列宽和对齐
        tree.column('match_num', width=80, anchor=tk.CENTER)
        tree.column('home_team', width=150, anchor=tk.CENTER)
        tree.column('vs', width=30, anchor=tk.CENTER)
        tree.column('away_team', width=150, anchor=tk.CENTER)
        tree.column('score', width=100, anchor=tk.CENTER)
        tree.column('status', width=100, anchor=tk.CENTER)
        
        # 优化2：为不同状态定义颜色标签
        tree.tag_configure('in_progress', foreground='red')
        tree.tag_configure('finished', foreground='black')
        tree.tag_configure('not_started', foreground='gray')
        
        tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.tabs_info[name]['issue_var'] = issue_var
        self.tabs_info[name]['tree'] = tree # 保存Treeview控件引用
        
        # 自动更新期号
        threading.Thread(target=self.update_issue, args=(lottery_type, issue_var), daemon=True).start()
        
        return frame

    def on_tab_change(self, event=None):
        # 优化4：当标签页改变时，自动触发数据获取
        try:
            current_tab_name = self.notebook.tab(self.notebook.select(), "text")
            info = self.tabs_info[current_tab_name]
            self.start_fetch_thread(info["type"], info['issue_var'])
        except (tk.TclError, KeyError):
            # 初始启动或窗口销毁时可能出错，忽略
            pass

    def update_issue(self, lottery_type, issue_var):
        current_issue = issue_var.get()
        # 只有在输入框为空时才自动获取，避免覆盖用户输入
        if not current_issue:
            issue = self.get_current_issue(lottery_type)
            if issue:
                self.after(0, issue_var.set, issue)

    def start_fetch_thread(self, lottery_type, issue_var):
        issue = issue_var.get()
        if not issue and lottery_type != 'jczq':
            messagebox.showwarning("提示", "请输入有效的期号！")
            return
        
        tab_name = self.notebook.tab(self.notebook.select(), "text")
        tree_widget = self.tabs_info[tab_name]['tree']

        threading.Thread(target=self.fetch_and_display, 
                         args=(lottery_type, issue, tree_widget), 
                         daemon=True).start()

    def fetch_and_display(self, lottery_type, issue, tree_widget):
        self.update_status(f"正在获取 {issue} 的数据...")
        result_data = self.fetch_all_data(lottery_type, issue)
        self.after(0, self.update_ui_with_results, tree_widget, result_data)

    def update_ui_with_results(self, tree, data):
        # 清空旧数据
        for i in tree.get_children():
            tree.delete(i)
            
        if isinstance(data, str): # 如果返回的是错误信息字符串
            messagebox.showerror("错误", data)
            self.update_status("数据获取失败！")
            return

        # 插入新数据
        for row_data in data:
            tree.insert('', 'end', values=row_data['values'], tags=(row_data['tag'],))
        
        self.update_status("数据刷新成功！")

    def update_status(self, message):
        self.after(0, self.status_bar.config, {'text': message})
        
    def get_status_info(self, live_score_details):
        """返回状态文本和状态类别(用于颜色标签)"""
        if not live_score_details:
            return "未开赛", "not_started"
        
        status_text = live_score_details.get('status', '未知')
        status_enum = live_score_details.get('statusEnum')
        
        # 定义状态类别
        if status_enum in [2, 3, 4] or '′' in status_text: # 上半场, 中场, 下半场, 或带分钟
            category = "in_progress"
        elif status_enum in [8, 5, 6, 7]: # 完赛
            category = "finished"
        elif status_enum in [1, 9, 10, 13]: # 未开赛, 延期, 取消, 待定
            category = "not_started"
        else:
            category = "not_started" # 默认归为未开赛
        
        # 优化状态显示文本
        if status_enum == 3: status_text = "中场"
        elif status_enum == 8: status_text = "完"

        return status_text, category

    def get_current_issue(self, lottery_type):
        if lottery_type == "jczq":
            return datetime.now().strftime('%Y-%m-%d')
        try:
            url = self.API_GET_CURRENT_ISSUE.format(lottery_type)
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                return data.get('data', {}).get('periodName')
        except Exception:
            return None

    def fetch_all_data(self, lottery_type, issue):
        try:
            # ... (API URL a and data fetching logic remains the same) ...
            if lottery_type == 'jczq':
                date_to_fetch = issue if issue else datetime.now().strftime('%Y-%m-%d')
                list_url = self.API_MATCH_LIST['jczq'].format(date_to_fetch)
            else:
                list_url = self.API_MATCH_LIST[lottery_type].format(issue)
            
            list_response = requests.get(list_url, timeout=10)
            list_response.raise_for_status()
            list_data = list_response.json()

            matches = []
            if list_data.get('code') == 200:
                data_content = list_data.get('data', [])
                if isinstance(data_content, list): matches = data_content
                elif isinstance(data_content, dict): matches = data_content.get('matchList', [])
            else:
                 return f"错误: {list_data.get('msg', '获取对阵列表失败')}"
            
            if not matches:
                return f"在 {issue} 未找到任何比赛信息。"
            
            match_ids = [str(m['matchInfoId']) for m in matches if 'matchInfoId' in m]
            live_data_map = {}
            if match_ids:
                scores_url = self.API_LIVE_SCORES.format(",".join(match_ids))
                scores_response = requests.get(scores_url, timeout=10)
                scores_response.raise_for_status()
                scores_data = scores_response.json()
                if scores_data.get('code') == 200:
                    live_data_map = {str(item['matchInfoId']): item for item in scores_data.get('data', [])}

            processed_data = []
            for match in matches:
                match_num = match.get('jcNum') if lottery_type == 'jczq' else match.get('matchNum', '')
                home_team = match.get('homeTeam', {}).get('teamName', 'N/A')
                away_team = match.get('guestTeam', {}).get('teamName', 'N/A')
                
                match_id_str = str(match.get('matchInfoId'))
                live_info = live_data_map.get(match_id_str, {})
                live_score_details = live_info.get('footballLiveScore', {})
                if not live_score_details: 
                    live_score_details = match.get('footballLiveScore', {})
                
                status_str, status_category = self.get_status_info(live_score_details)

                # 优化3: 未开赛比分格式化
                if status_category == 'not_started':
                    score_str = '- : -'
                else:
                    home_score = live_score_details.get('homeScore', '-')
                    away_score = live_score_details.get('guestScore', '-')
                    score_str = f"{home_score} - {away_score}"

                row_values = (match_num, home_team, 'vs', away_team, score_str, status_str)
                processed_data.append({'values': row_values, 'tag': status_category})
            
            return processed_data

        except Exception as e:
            return f"发生未知错误: {e}\n{traceback.format_exc()}"

if __name__ == "__main__":
    app = ScoreApp()
    app.mainloop()
