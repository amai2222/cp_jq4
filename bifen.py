import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime, timedelta
import threading
import traceback
import time

class ScoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("网易彩票数据获取工具 (v24.1 - 北单数据处理修正版)")
        self.geometry("1150x600")

        self.API_MATCH_LIST = {
            "jczq": "https://sports.163.com/caipiao/api/web/match/list/jingcai/matchList/1?days={}",
            "bjdc": "https://sports.163.com/caipiao/api/web/match/list/beijing/matchList/1?days={}",
            "sfc": "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/rj?degree={}",
            "jqs": "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/jqc?degree={}",
            "bqc": "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/bqc?degree={}"
        }
        self.API_JC_CURRENT_ISSUE = "https://sports.163.com/caipiao/api/web/jc/queryCurrentPeriod.html?gameEn={}"
        self.API_BASE_DEGREE_LIST = "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/{}" 
        self.API_LIVE_SCORES = "https://sports.163.com/caipiao/api/web/match/list/getMatchInfoList/1?matchInfoIds={}"
        
        self.active_timer = None
        self.create_menu()

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tabs_info = {
            "竞彩": {"type": "jczq"}, "北单": {"type": "bjdc"}, "胜负彩": {"type": "sfc"},
            "4场进球": {"type": "jqs"}, "6场半全场": {"type": "bqc"}
        }

        for name, info in self.tabs_info.items():
            frame = self.create_tab(self.notebook, name, info["type"])
            self.notebook.add(frame, text=name)

        self.status_bar = tk.Label(self, text="准备就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.after(200, self.initial_load)

    # --- v24.1 核心修正: fetch_all_data 方法 ---
    def fetch_all_data(self, lottery_type, issue):
        try:
            base_url = self.API_MATCH_LIST[lottery_type].format(issue)
            timestamp = int(time.time() * 1000)
            separator = "&" if "?" in base_url else "?"
            list_url = f"{base_url}{separator}_={timestamp}"

            list_response = requests.get(list_url, timeout=10)
            list_response.raise_for_status()
            list_data = list_response.json()
            matches = []
            if list_data.get('code') == 200:
                data_content = list_data.get('data')
                if lottery_type in ['sfc', 'jqs', 'bqc'] and isinstance(data_content, dict):
                    matches = data_content.get('matchList', [])
                elif isinstance(data_content, list):
                    matches = data_content
            elif list_data.get('code') == 400 and 'degree' in list_data.get('msg', ''):
                 return f"期号 {issue} 不存在或已过期。"
            else:
                 return f"错误: {list_data.get('msg', '获取对阵列表失败')}"
            
            if not matches: return f"在 {issue} 未找到任何比赛信息。"
            
            match_ids = [str(m['matchInfoId']) for m in matches if 'matchInfoId' in m]
            live_data_map = {}
            # 只有竞彩和北单需要调用第二个API获取实时比分
            if match_ids and lottery_type in ['jczq', 'bjdc']:
                try:
                    ts_scores = int(time.time() * 1000)
                    scores_url = self.API_LIVE_SCORES.format(",".join(match_ids)) + f"&_={ts_scores}"
                    scores_response = requests.get(scores_url, timeout=10)
                    scores_response.raise_for_status()
                    scores_data = scores_response.json()
                    if scores_data.get('code') == 200: 
                        live_data_map = {str(item['matchInfoId']): item for item in scores_data.get('data', [])}
                except requests.exceptions.RequestException:
                    pass

            processed_data = []
            for i, match in enumerate(matches, 1):
                match_id_str = str(match.get('matchInfoId'))
                live_info = live_data_map.get(match_id_str, {})
                
                # final_match_data 优先使用 live_info 的数据, 但 match 的数据作为补充
                final_match_data = {**match, **live_info}

                # v24.1 修正: 重新梳理数据来源，确保信息正确
                # 场次编号: 北单用 matchNum, 竞彩用 jcNum, 其他用 matchNum 或自增
                match_num = match.get('matchNum') or final_match_data.get('jcNum') or str(i)
                # 次序: 数字彩用 sort，其他用自增
                sequence_num = str(match.get('sort', i))
                
                # 队伍名称: 优先用 live_info, 其次用 match
                home_team = final_match_data.get('homeTeam', {}).get('teamName', 'N/A')
                away_team = final_match_data.get('guestTeam', {}).get('teamName', 'N/A')
                
                # 让球数: 竞彩和北单逻辑不同
                let_ball = '0'
                if lottery_type == 'jczq':
                    # 竞彩让球在 playMap.HHDA.concede
                    let_ball = str(final_match_data.get('playMap', {}).get('HHDA', {}).get('concede', '0'))
                elif lottery_type == 'bjdc':
                    # 北单让球在原始 match 数据的 odds.letBall
                    let_ball = str(match.get('odds', {}).get('letBall', '0'))

                # 比分和状态: 从 live_info (或合并后的 final_match_data) 中获取
                # footbalLiveScore 可能不存在, 直接从 final_match_data 根获取
                score_source = final_match_data.get('footballLiveScore', final_match_data)
                
                status_str, status_category = self.get_status_info(score_source)
                
                home_score = score_source.get('homeScore')
                guest_score = score_source.get('guestScore')
                home_half = score_source.get('homeHalfScore')
                guest_half = score_source.get('guestHalfScore')

                score_str = '- : -'
                if home_score is not None and guest_score is not None:
                    score_str = f"{home_score} - {guest_score}"

                half_time_str = ''
                if home_half is not None and guest_half is not None:
                    half_time_str = f"{home_half} - {guest_half}"
                
                result_str = self._calculate_results(home_score, guest_score, let_ball, status_category, lottery_type, home_half, guest_half)
                
                # 让球盘口显示
                display_handicap = ""
                try:
                    let_ball_float = float(let_ball)
                    # 只有竞彩和北单需要显示让球
                    if lottery_type in ['jczq', 'bjdc'] and let_ball_float != 0:
                        handicap_val = int(let_ball_float)
                        display_handicap = f"({handicap_val:+d})"
                except (ValueError, TypeError): pass
                
                home_team_display = f"{home_team} {display_handicap}".strip()

                row_values = (match_num, sequence_num, home_team_display, 'vs', away_team, half_time_str, score_str, status_str, result_str)
                processed_data.append({'values': row_values, 'tag': status_category})
            
            return processed_data
        except Exception as e:
            return f"获取或处理数据时发生错误: {type(e).__name__} at line {e.__traceback__.tb_lineno}: {e}\n{traceback.format_exc()}"

    # --- 以下代码与 v24.0 (即v23.3-JQC修正版) 完全一致, 为了完整性全部保留 ---
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
        
        if not is_date_based:
            prev_issue_button = ttk.Button(control_frame, text="上一期", command=lambda: self.change_issue(-1))
            prev_issue_button.pack(side=tk.LEFT)
        else:
            prev_day_button = ttk.Button(control_frame, text="前一天", command=lambda: self.change_date(-1))
            prev_day_button.pack(side=tk.LEFT)
        
        issue_entry = ttk.Entry(control_frame, textvariable=issue_var, width=15, justify='center')
        issue_entry.pack(side=tk.LEFT, padx=5)

        if not is_date_based:
            next_issue_button = ttk.Button(control_frame, text="下一期", command=lambda: self.change_issue(1))
            next_issue_button.pack(side=tk.LEFT)
        else:
            next_day_button = ttk.Button(control_frame, text="后一天", command=lambda: self.change_date(1))
            next_day_button.pack(side=tk.LEFT)

        fetch_button = ttk.Button(control_frame, text="刷新", command=lambda: self.start_fetch_thread(is_manual=True))
        fetch_button.pack(side=tk.LEFT, padx=(10, 0))
        auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_check = ttk.Checkbutton(control_frame, text="每分钟自动刷新", variable=auto_refresh_var, command=self.handle_auto_refresh_toggle)
        auto_refresh_check.pack(side=tk.LEFT, padx=(10,0))

        columns = ('match_num', 'sequence', 'home_team', 'vs', 'away_team', 'half_score', 'score', 'status', 'result')
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        
        tree.heading('match_num', text='场次')
        tree.heading('sequence', text='次序')
        tree.heading('home_team', text='主队')
        tree.heading('vs', text='')
        tree.heading('away_team', text='客队')
        tree.heading('half_score', text='半场')
        tree.heading('score', text='比分')
        tree.heading('status', text='状态')
        tree.heading('result', text='赛果')

        tree.column('match_num', width=80, anchor=tk.CENTER)
        tree.column('sequence', width=50, anchor=tk.CENTER)
        tree.column('home_team', width=160, anchor=tk.E)
        tree.column('vs', width=30, anchor=tk.CENTER)
        tree.column('away_team', width=160, anchor=tk.W)
        tree.column('half_score', width=80, anchor=tk.CENTER)
        tree.column('score', width=100, anchor=tk.CENTER)
        tree.column('status', width=80, anchor=tk.CENTER)
        tree.column('result', width=120, anchor=tk.CENTER)
        
        tree.tag_configure('in_progress', foreground='red')
        tree.tag_configure('finished', foreground='black')
        tree.tag_configure('not_started', foreground='gray')
        tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.tabs_info[name].update({
            'issue_var': issue_var,
            'tree': tree,
            'auto_refresh_var': auto_refresh_var
        })
        return frame
        
    def _calculate_results(self, home_score, guest_score, let_ball, status_category, lottery_type, home_half_score=None, guest_half_score=None):
        if status_category != 'finished' or home_score is None or guest_score is None:
            return ""
        
        try:
            home_s = int(home_score)
            guest_s = int(guest_score)
        except (ValueError, TypeError):
             return ""

        spf_map = {1: ("胜", "3"), 0: ("平", "1"), -1: ("负", "0")}

        if lottery_type == 'jqs':
            h_res = str(home_s) if home_s < 3 else '3+'
            g_res = str(guest_s) if guest_s < 3 else '3+'
            return f"{h_res}, {g_res}"
        
        if lottery_type == 'bqc':
            if home_half_score is None or guest_half_score is None:
                return ""
            try:
                home_half_s = int(home_half_score)
                guest_half_s = int(guest_half_score)
            except (ValueError, TypeError):
                return ""

            half_comp = 1 if home_half_s > guest_half_s else (-1 if home_half_s < guest_half_s else 0)
            full_comp = 1 if home_s > guest_s else (-1 if home_s < guest_s else 0)
            
            half_result_text = spf_map[half_comp][0]
            full_result_text = spf_map[full_comp][0]
            
            return f"{half_result_text}-{full_result_text}"

        full_comp = 1 if home_s > guest_s else (-1 if home_s < guest_s else 0)
        spf_text, spf_code = spf_map[full_comp]
        
        if lottery_type == 'sfc':
            return spf_code

        try:
            let_ball_float = float(let_ball)
            if let_ball_float == 0.0:
                return spf_text
            
            if (home_s + let_ball_float) > guest_s: rqspf_text = "让胜"
            elif (home_s + let_ball_float) < guest_s: rqspf_text = "让负"
            else: rqspf_text = "让平"
            return f"{spf_text} / {rqspf_text}"
        except (ValueError, TypeError):
            return spf_text

    def get_status_info(self, match_details):
        if not match_details: return "未开赛", "not_started"
        
        status_enum = match_details.get('statusEnum')
        if status_enum is None:
            status_enum = match_details.get('matchStatus')
            if status_enum == 0: status_enum = 1
            elif status_enum == 2 or status_enum == -1: status_enum = 8
            elif status_enum == 1: status_enum = 2

        if status_enum in [2, 4]:
            live_time = match_details.get('liveTime')
            return (f"{live_time}′" if live_time is not None else "进行中"), "in_progress"
        elif status_enum == 3: return "中场", "in_progress"
        elif status_enum in [8, 5, 6, 7]: return "完", "finished"
        else: return "未开赛", "not_started"
        
    def handle_auto_refresh_toggle(self):
        self.cancel_timer() 
        current_tab_info = self.get_current_tab_info()
        if current_tab_info and current_tab_info['auto_refresh_var'].get():
            self.schedule_refresh()

    def schedule_refresh(self):
        self.cancel_timer() 
        current_tab_info = self.get_current_tab_info()
        if current_tab_info and current_tab_info['auto_refresh_var'].get():
            self.active_timer = self.after(60000, lambda: self.start_fetch_thread(is_manual=False))
    
    def cancel_timer(self):
        if self.active_timer: self.after_cancel(self.active_timer)
        self.active_timer = None
            
    def get_current_tab_info(self):
        try:
            current_tab_name = self.notebook.tab(self.notebook.select(), "text")
            return self.tabs_info[current_tab_name]
        except (tk.TclError, KeyError): return None

    def initial_load(self):
        self.notebook.update_idletasks()
        self.on_tab_change()

    def get_initial_issue(self, lottery_type):
        if lottery_type in ["jczq", "bjdc"]:
            now = datetime.now()
            return (now - timedelta(days=1) if 0 <= now.hour < 12 else now).strftime('%Y-%m-%d')
        else: return self.get_current_issue_from_api(lottery_type)

    def change_issue(self, delta):
        current_tab_info = self.get_current_tab_info()
        if not current_tab_info or current_tab_info['type'] in ['jczq', 'bjdc']: return
        try:
            issue_var = current_tab_info['issue_var']
            new_issue = int(issue_var.get()) + delta
            issue_var.set(str(new_issue))
            self.start_fetch_thread(is_manual=True)
        except (ValueError, KeyError):
            messagebox.showwarning("提示", "当前期号非数字，无法进行加减。")
            self.start_fetch_thread(is_manual=True)

    def change_date(self, days_delta):
        current_tab_info = self.get_current_tab_info()
        if not current_tab_info or current_tab_info['type'] not in ['jczq', 'bjdc']: return
        try:
            issue_var = current_tab_info['issue_var']
            new_date = datetime.strptime(issue_var.get(), '%Y-%m-%d') + timedelta(days_delta)
            issue_var.set(new_date.strftime('%Y-%m-%d'))
            self.start_fetch_thread(is_manual=True)
        except (ValueError, KeyError):
            messagebox.showwarning("提示", "日期格式错误，将重置为今天。")
            current_tab_info['issue_var'].set(datetime.now().strftime('%Y-%m-%d'))
            self.start_fetch_thread(is_manual=True)

    def on_tab_change(self, event=None):
        current_tab_info = self.get_current_tab_info()
        if current_tab_info and not current_tab_info['issue_var'].get():
             issue = self.get_initial_issue(current_tab_info['type'])
             if issue: current_tab_info['issue_var'].set(issue)
        self.start_fetch_thread(is_manual=True)

    def start_fetch_thread(self, is_manual=False):
        self.cancel_timer() 
        current_tab_info = self.get_current_tab_info()
        if not current_tab_info: return
        
        lottery_type, issue_var, tree_widget = current_tab_info['type'], current_tab_info['issue_var'], current_tab_info['tree']
        issue = issue_var.get()

        if not issue:
            issue = self.get_initial_issue(lottery_type)
            if not issue:
                messagebox.showwarning("提示", f"无法自动获取期号/日期，请手动输入。")
                self.schedule_refresh()
                return
            issue_var.set(issue)
        
        if is_manual:
            self.update_status(f"正在获取 {issue} 的数据...")
            for i in tree_widget.get_children(): tree_widget.delete(i)
        
        threading.Thread(target=self.fetch_and_display, args=(lottery_type, issue, tree_widget, is_manual), daemon=True).start()

    def fetch_and_display(self, lottery_type, issue, tree_widget, is_manual):
        if not is_manual: self.update_status(f"自动刷新 {issue} 数据中...")
        result_data = self.fetch_all_data(lottery_type, issue)
        self.after(0, self.update_ui_with_results, tree_widget, result_data, issue)

    def update_ui_with_results(self, tree, data, original_issue):
        current_tab_info = self.get_current_tab_info()
        if not current_tab_info or tree != current_tab_info['tree'] or original_issue != current_tab_info['issue_var'].get():
            self.schedule_refresh()
            return
        
        for i in tree.get_children(): tree.delete(i)
        
        if isinstance(data, str):
            if "Traceback" in data: messagebox.showerror("发生未知错误", data)
            else: messagebox.showinfo("提示", data)
            self.update_status(f"获取 {original_issue} 数据失败")
        else:
            for row_data in data: tree.insert('', 'end', values=row_data['values'], tags=(row_data['tag'],))
            self.update_status(f"{original_issue} 数据刷新成功！")
        
        self.schedule_refresh()

    def update_status(self, message):
        self.after(0, self.status_bar.config, {'text': message})
    
    def get_current_issue_from_api(self, lottery_type):
        api_map = {"sfc": "rj", "jqs": "jqc", "bqc": "bqc"}
        if lottery_type in api_map:
            try:
                url = self.API_BASE_DEGREE_LIST.format(api_map[lottery_type])
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data.get('code') == 200:
                    degree_list = data.get('data', {}).get('degreeList', [])
                    for issue_info in degree_list:
                        if issue_info.get('degreeStatus') == 1:
                            return str(issue_info.get('degree'))
                    if degree_list: return str(degree_list[0].get('degree'))
            except Exception as e:
                print(f"Error getting current issue for {lottery_type}: {e}")
                return None
        return None

if __name__ == "__main__":
    app = ScoreApp()
    app.mainloop()

