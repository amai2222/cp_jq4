import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime, timedelta
import threading
import traceback

class ScoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # 版本号和标题更新
        self.title("网易彩票数据获取工具 (v13.0 - 终极功能版)")
        self.geometry("950x600")

        # --- API 配置 ---
        self.API_MATCH_LIST = {
            "jczq": "https://sports.163.com/caipiao/api/web/match/list/jingcai/matchList/1?days={}",
            "sfc": "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/rj?degree={}",
            "bjdc": "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/bjdc?days={}"
        }
        self.API_GET_CURRENT_ISSUE = "https://sports.163.com/caipiao/api/web/jc/queryCurrentPeriod.html?gameEn={}"
        self.API_LIVE_SCORES = "https://sports.163.com/caipiao/api/web/match/list/getMatchInfoList/1?matchInfoIds={}"
        
        self.active_timer = None

        self.create_menu()

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tabs_info = {"竞彩": {"type": "jczq"}, "北单": {"type": "bjdc"}, "胜负彩": {"type": "sfc"}}
        for name, info in self.tabs_info.items():
            frame = self.create_tab(self.notebook, name, info["type"])
            self.notebook.add(frame, text=name)

        self.status_bar = tk.Label(self, text="准备就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.after(200, self.initial_load)

    def create_menu(self):
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="退出", command=self.quit)

    def create_tab(self, parent, name, lottery_type):
        frame = ttk.Frame(parent, padding="10")
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        is_date_based = lottery_type in ['jczq', 'bjdc']
        label_text = "比赛日期:" if is_date_based else "期号:"
        issue_label = ttk.Label(control_frame, text=label_text)
        issue_label.pack(side=tk.LEFT, padx=(0, 5))
        
        issue_var = tk.StringVar()
        
        # --- 新增功能：上一期/下一期按钮 ---
        if lottery_type == 'sfc':
            prev_issue_button = ttk.Button(control_frame, text="上一期", command=lambda: self.change_issue(-1))
            prev_issue_button.pack(side=tk.LEFT)
        elif is_date_based:
            prev_day_button = ttk.Button(control_frame, text="前一天", command=lambda: self.change_date(-1))
            prev_day_button.pack(side=tk.LEFT)

        issue_entry = ttk.Entry(control_frame, textvariable=issue_var, width=15, justify='center')
        issue_entry.pack(side=tk.LEFT, padx=5)

        if lottery_type == 'sfc':
            next_issue_button = ttk.Button(control_frame, text="下一期", command=lambda: self.change_issue(1))
            next_issue_button.pack(side=tk.LEFT)
        elif is_date_based:
            next_day_button = ttk.Button(control_frame, text="后一天", command=lambda: self.change_date(1))
            next_day_button.pack(side=tk.LEFT)
        
        # --- 核心修正：简化刷新按钮的命令，使其总是读取最新值 ---
        fetch_button = ttk.Button(control_frame, text="刷新", command=lambda: self.start_fetch_thread(is_manual=True))
        fetch_button.pack(side=tk.LEFT, padx=(10, 0))
        
        auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_check = ttk.Checkbutton(control_frame, text="每分钟自动刷新", variable=auto_refresh_var, command=self.handle_auto_refresh_toggle)
        auto_refresh_check.pack(side=tk.LEFT, padx=(10,0))

        columns = ('match_num', 'home_team', 'vs', 'away_team', 'score', 'half_score', 'status')
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        tree.heading('match_num', text='场次'); tree.heading('home_team', text='主队'); tree.heading('vs', text=''); tree.heading('away_team', text='客队'); tree.heading('score', text='比分'); tree.heading('half_score', text='半场'); tree.heading('status', text='状态')
        tree.column('match_num', width=80, anchor=tk.CENTER); tree.column('home_team', width=150, anchor=tk.CENTER); tree.column('vs', width=30, anchor=tk.CENTER); tree.column('away_team', width=150, anchor=tk.CENTER); tree.column('score', width=100, anchor=tk.CENTER); tree.column('half_score', width=80, anchor=tk.CENTER); tree.column('status', width=100, anchor=tk.CENTER)
        tree.tag_configure('in_progress', foreground='red'); tree.tag_configure('finished', foreground='black'); tree.tag_configure('not_started', foreground='gray')
        tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.tabs_info[name].update({
            'issue_var': issue_var,
            'tree': tree,
            'auto_refresh_var': auto_refresh_var
        })
        
        return frame
    
    def handle_auto_refresh_toggle(self):
        self.cancel_timer() 
        current_tab_info = self.get_current_tab_info()
        if current_tab_info and current_tab_info['auto_refresh_var'].get():
            self.schedule_refresh()

    def schedule_refresh(self):
        self.cancel_timer() 
        current_tab_info = self.get_current_tab_info()
        if current_tab_info and current_tab_info['auto_refresh_var'].get():
            self.active_timer = self.after(60000, self.start_fetch_thread)
    
    def cancel_timer(self):
        if self.active_timer:
            self.after_cancel(self.active_timer)
            self.active_timer = None
            
    def get_current_tab_info(self):
        try:
            current_tab_name = self.notebook.tab(self.notebook.select(), "text")
            return self.tabs_info[current_tab_name]
        except (tk.TclError, KeyError):
            return None

    def initial_load(self):
        for name, info in self.tabs_info.items():
            if not info['issue_var'].get():
                issue = self.get_initial_issue(info['type'])
                if issue: info['issue_var'].set(issue)
        self.on_tab_change()

    def get_initial_issue(self, lottery_type):
        if lottery_type in ["jczq", "bjdc"]:
            now = datetime.now()
            if 0 <= now.hour < 12: return (now - timedelta(days=1)).strftime('%Y-%m-%d')
            else: return now.strftime('%Y-%m-%d')
        else:
            return self.get_current_issue_from_api(lottery_type)
            
    # --- 新增功能：处理上一期/下一期逻辑 ---
    def change_issue(self, delta):
        current_tab_info = self.get_current_tab_info()
        if not current_tab_info or current_tab_info['type'] != 'sfc':
            return
        
        try:
            issue_var = current_tab_info['issue_var']
            current_issue = int(issue_var.get())
            new_issue = current_issue + delta
            issue_var.set(str(new_issue))
            # 修改期号后，手动触发一次刷新
            self.start_fetch_thread(is_manual=True)
        except (ValueError, KeyError):
            messagebox.showwarning("提示", "当前期号非数字，无法进行加减操作。")

    def change_date(self, days_delta):
        current_tab_info = self.get_current_tab_info()
        if not current_tab_info or current_tab_info['type'] not in ['jczq', 'bjdc']: return
        
        try:
            issue_var = current_tab_info['issue_var']
            current_date = datetime.strptime(issue_var.get(), '%Y-%m-%d')
            new_date = current_date + timedelta(days_delta)
            issue_var.set(new_date.strftime('%Y-%m-%d'))
            self.start_fetch_thread(is_manual=True)
        except (ValueError, KeyError):
            messagebox.showwarning("提示", "日期格式错误或出现内部错误,将重置为今天。")
            current_tab_info['issue_var'].set(datetime.now().strftime('%Y-%m-%d'))
            self.start_fetch_thread(is_manual=True)

    def on_tab_change(self, event=None):
        self.cancel_timer() 
        self.start_fetch_thread(is_manual=True)

    def start_fetch_thread(self, is_manual=False):
        if is_manual: 
            self.cancel_timer()

        current_tab_info = self.get_current_tab_info()
        if not current_tab_info: return
        
        lottery_type = current_tab_info['type']
        issue_var = current_tab_info['issue_var']
        issue = issue_var.get()
        
        if not issue:
            issue = self.get_initial_issue(lottery_type)
            if not issue:
                messagebox.showwarning("提示", "无法获取期号/日期，请输入后刷新。")
                return
            else:
                issue_var.set(issue)
        
        tree_widget = current_tab_info['tree']
        threading.Thread(target=self.fetch_and_display, args=(lottery_type, issue, tree_widget), daemon=True).start()

    def fetch_and_display(self, lottery_type, issue, tree_widget):
        self.update_status(f"正在获取 {issue} 的数据...")
        result_data = self.fetch_all_data(lottery_type, issue)
        self.after(0, self.update_ui_with_results, tree_widget, result_data)

    def update_ui_with_results(self, tree, data):
        current_tab_info = self.get_current_tab_info()
        if not current_tab_info or tree != current_tab_info['tree']: return 

        for i in tree.get_children(): tree.delete(i)
        
        if isinstance(data, str):
            if "Traceback" in data: messagebox.showerror("发生未知错误", data)
            else: messagebox.showinfo("提示", data)
            self.update_status("数据获取失败或无数据！")
        else:
            for row_data in data: tree.insert('', 'end', values=row_data['values'], tags=(row_data['tag'],))
            self.update_status("数据刷新成功！")
        
        self.schedule_refresh()

    def update_status(self, message):
        self.after(0, self.status_bar.config, {'text': message})
        
    def get_status_info(self, live_score_details):
        if not live_score_details: return "未开赛", "not_started"
        status_text = live_score_details.get('status', '未知'); status_enum = live_score_details.get('statusEnum')
        if status_enum in [2, 3, 4] or '′' in status_text: category = "in_progress"
        elif status_enum in [8, 5, 6, 7]: category = "finished"
        else: category = "not_started"
        if status_enum == 3: status_text = "中场"
        elif status_enum == 8: status_text = "完"
        return status_text, category

    def get_current_issue_from_api(self, lottery_type):
        try:
            if lottery_type == 'sfc':
                url = "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/rj"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data.get('code') == 200:
                    degree_list = data.get('data', {}).get('degreeList', [])
                    for issue_info in degree_list:
                        if issue_info.get('degreeStatus') == 1:
                            return str(issue_info.get('degree'))
                    if degree_list:
                        return str(degree_list[0].get('degree'))
                return None
            else:
                url = self.API_GET_CURRENT_ISSUE.format(lottery_type)
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                data = response.json()
                if data.get('code') == 200: 
                    return data.get('data', {}).get('periodName')
        except Exception as e:
            print(f"Error getting current issue for {lottery_type}: {e}") 
            return None

    def fetch_all_data(self, lottery_type, issue):
        try:
            list_url = self.API_MATCH_LIST[lottery_type].format(issue)
            list_response = requests.get(list_url, timeout=10); list_response.raise_for_status()
            list_data = list_response.json()
            matches = []
            if list_data.get('code') == 200:
                data_content = list_data.get('data')
                if lottery_type == 'sfc' and isinstance(data_content, dict):
                    matches = data_content.get('matchList', [])
                elif isinstance(data_content, list):
                    matches = data_content
            else: return f"错误: {list_data.get('msg', '获取对阵列表失败')}"
            
            if not matches: return f"在 {issue} 未找到任何比赛信息。"
            
            match_ids = [str(m['matchInfoId']) for m in matches if 'matchInfoId' in m]
            live_data_map = {}
            if match_ids:
                try:
                    scores_url = self.API_LIVE_SCORES.format(",".join(match_ids))
                    scores_response = requests.get(scores_url, timeout=10); scores_response.raise_for_status()
                    scores_data = scores_response.json()
                    if scores_data.get('code') == 200: 
                        live_data_map = {str(item['matchInfoId']): item for item in scores_data.get('data', [])}
                except requests.exceptions.RequestException:
                    print("Live scores API failed, will use main list data only.")

            processed_data = []
            for match in matches:
                match_num = match.get('jcNum') if lottery_type in ['jczq', 'bjdc'] else match.get('matchNum', '')
                home_team = match.get('homeTeam', {}).get('teamName', 'N/A')
                away_team = match.get('guestTeam', {}).get('teamName', 'N/A')
                match_id_str = str(match.get('matchInfoId'))
                
                live_info = live_data_map.get(match_id_str, {})
                live_score_details = live_info.get('footballLiveScore') if live_info else None
                if not live_score_details:
                    live_score_details = match.get('footballLiveScore', {})
                
                status_str, status_category = self.get_status_info(live_score_details)
                score_str = '- : -'
                if status_category != 'not_started' and 'homeScore' in live_score_details and live_score_details['homeScore'] is not None:
                    score_str = f"{live_score_details.get('homeScore')} - {live_score_details.get('guestScore')}"

                half_time_str = ''
                home_half = live_score_details.get('homeHalfScore')
                guest_half = live_score_details.get('guestHalfScore')
                if home_half is not None and guest_half is not None:
                    half_time_str = f"{home_half} - {guest_half}"
                
                row_values = (match_num, home_team, 'vs', away_team, score_str, half_time_str, status_str)
                processed_data.append({'values': row_values, 'tag': status_category})
            return processed_data
        except Exception as e:
            return f"发生未知错误: {e}\n{traceback.format_exc()}"

if __name__ == "__main__":
    app = ScoreApp()
    app.mainloop()
