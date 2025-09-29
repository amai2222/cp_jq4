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
        # 版本号更新，注明核心修复逻辑
        self.title("实时比分查看工具 (v31.0 - 权威状态修复版)")
        self.geometry("1270x600")

        self.API_MATCH_LIST = {
            "jczq": "https://sports.163.com/caipiao/api/web/match/list/jingcai/matchList/1?days={}",
            "bjdc": "https://sports.163.com/caipiao/api/web/match/list/beijing/matchList/1?days={}",
            "sfc": "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/rj?degree={}",
            "jqs": "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/jqc?degree={}",
            "bqc": "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/bqc?degree={}"
        }
        self.API_BASE_DEGREE_LIST = "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/{}" 
        self.API_LIVE_SCORES = "https://sports.163.com/caipiao/api/web/match/list/getMatchInfoList/1?matchInfoIds={}"
        
        self.active_timer = None
        self.create_menu()

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tabs_info = {
            "竞彩": {"type": "jczq"}, 
            "北单": {"type": "bjdc"}, 
            "胜负彩和任九": {"type": "sfc"},
            "4场进球": {"type": "jqs"}, 
            "6场半全场": {"type": "bqc"}
        }

        for name, info in self.tabs_info.items():
            frame = self.create_tab(self.notebook, name, info["type"])
            self.notebook.add(frame, text=name)

        self.status_bar = tk.Label(self, text="准备就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.after(200, self.initial_load)
        
    def create_tab(self, parent, name, lottery_type):
        frame = ttk.Frame(parent, padding="10")
        control_frame = ttk.Frame(frame); control_frame.pack(fill=tk.X, pady=5)
        is_date_based = lottery_type in ['jczq', 'bjdc']; label_text = "比赛日期:" if is_date_based else "期号:"; issue_label = ttk.Label(control_frame, text=label_text); issue_label.pack(side=tk.LEFT, padx=(0, 5)); issue_var = tk.StringVar()
        if not is_date_based: prev_issue_button = ttk.Button(control_frame, text="上一期", command=lambda: self.change_issue(-1)); prev_issue_button.pack(side=tk.LEFT)
        else: prev_day_button = ttk.Button(control_frame, text="前一天", command=lambda: self.change_date(-1)); prev_day_button.pack(side=tk.LEFT)
        issue_entry = ttk.Entry(control_frame, textvariable=issue_var, width=15, justify='center'); issue_entry.pack(side=tk.LEFT, padx=5)
        if not is_date_based: next_issue_button = ttk.Button(control_frame, text="下一期", command=lambda: self.change_issue(1)); next_issue_button.pack(side=tk.LEFT)
        else: next_day_button = ttk.Button(control_frame, text="后一天", command=lambda: self.change_date(1)); next_day_button.pack(side=tk.LEFT)
        fetch_button = ttk.Button(control_frame, text="刷新", command=lambda: self.start_fetch_thread(is_manual=True)); fetch_button.pack(side=tk.LEFT, padx=(10, 0))
        auto_refresh_var = tk.BooleanVar(value=True); auto_refresh_check = ttk.Checkbutton(control_frame, text="每分钟自动刷新", variable=auto_refresh_var, command=self.handle_auto_refresh_toggle); auto_refresh_check.pack(side=tk.LEFT, padx=(10,0))
        result_string_var = tk.StringVar(); result_string_label = ttk.Label(control_frame, textvariable=result_string_var, font=('Helvetica', 12, 'bold'), foreground='red'); result_string_label.pack(side=tk.LEFT, padx=(20, 0)); result_string_label.config(cursor="hand2"); result_string_label.bind("<Button-1>", self.copy_to_clipboard)
        tree_frame = ttk.Frame(frame); tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        columns = ('match_num', 'match_time', 'sequence', 'home_team', 'vs', 'away_team', 'half_score', 'score', 'status', 'result')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings'); scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side=tk.RIGHT, fill=tk.Y); tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree.heading('match_num', text='场次'); tree.heading('match_time', text='时间'); tree.heading('sequence', text='次序'); tree.heading('home_team', text='主队'); tree.heading('vs', text=''); tree.heading('away_team', text='客队'); tree.heading('half_score', text='半场'); tree.heading('score', text='比分'); tree.heading('status', text='状态'); tree.heading('result', text='赛果')
        tree.column('match_num', width=80, anchor=tk.CENTER); tree.column('match_time', width=110, anchor=tk.CENTER); tree.column('sequence', width=50, anchor=tk.CENTER); tree.column('home_team', width=160, anchor=tk.E); tree.column('vs', width=30, anchor=tk.CENTER); tree.column('away_team', width=160, anchor=tk.W); tree.column('half_score', width=80, anchor=tk.CENTER); tree.column('score', width=100, anchor=tk.CENTER); tree.column('status', width=80, anchor=tk.CENTER); tree.column('result', width=120, anchor=tk.CENTER)
        tree.tag_configure('in_progress', foreground='red'); tree.tag_configure('finished', foreground='black'); tree.tag_configure('not_started', foreground='gray'); tree.tag_configure('cancelled', foreground='blue')
        self.tabs_info[name].update({'issue_var': issue_var, 'tree': tree, 'auto_refresh_var': auto_refresh_var, 'result_string_var': result_string_var})
        return frame
        
    def copy_to_clipboard(self, event): text_to_copy = event.widget.cget("text"); text_to_copy and text_to_copy != " " and (self.clipboard_clear(), self.clipboard_append(text_to_copy), self.update_status(f"已复制: {text_to_copy}"))

    def fetch_all_data(self, lottery_type, issue):
        try:
            list_url = self.API_MATCH_LIST[lottery_type].format(issue) + f"&_={int(time.time() * 1000)}"; list_response = requests.get(list_url, timeout=10); list_response.raise_for_status(); list_data = list_response.json(); matches = []
            if list_data.get('code') == 200:
                data_content = list_data.get('data')
                if lottery_type in ['sfc', 'jqs', 'bqc'] and isinstance(data_content, dict): matches = data_content.get('matchList', [])
                elif isinstance(data_content, list): matches = data_content
            elif 'degree' in list_data.get('msg', ''): return f"期号 {issue} 不存在或已过期。"
            else: return f"错误: {list_data.get('msg', '获取对阵列表失败')}"
            if not matches: return f"在 {issue} 未找到任何比赛信息。"
            match_ids = [str(m['matchInfoId']) for m in matches if 'matchInfoId' in m]; live_data_map = {}
            if match_ids and lottery_type in ['jczq', 'bjdc']:
                try: scores_url = self.API_LIVE_SCORES.format(','.join(match_ids)) + f"&_={int(time.time() * 1000)}"; scores_data = requests.get(scores_url, timeout=10).json(); scores_data.get('code') == 200 and (live_data_map := {str(item['matchInfoId']): item for item in scores_data.get('data', [])})
                except: pass
            
            processed_data = []
            for i, match in enumerate(matches, 1):
                live_data = live_data_map.get(str(match.get('matchInfoId')), {}); final_match_data = {**live_data, **match}; status_str, status_category = self.get_status_info(final_match_data)
                match_num, match_time_display = self._get_basic_info(final_match_data, lottery_type, i, issue); home_team = final_match_data.get('homeTeam', {}).get('teamName', 'N/A'); away_team = final_match_data.get('guestTeam', {}).get('teamName', 'N/A')
                score_source = final_match_data.get('footballLiveScore', final_match_data); home_score, guest_score, home_half, guest_half = score_source.get('homeScore'), score_source.get('guestScore'), score_source.get('homeHalfScore'), score_source.get('guestHalfScore')
                score_str = "- : -" if status_category == 'cancelled' else f"{home_score} - {guest_score}" if home_score is not None else '- : -'; half_time_str = "" if status_category == 'cancelled' else f"{home_half} - {guest_half}" if home_half is not None else ''
                let_ball = '0';
                if lottery_type == 'jczq': let_ball = str(final_match_data.get('playMap', {}).get('HHDA', {}).get('concede', '0'))
                elif lottery_type == 'bjdc': let_ball = str(final_match_data.get('playMap', {}).get('BJ_HDA', {}).get('concede', '0'))
                result_str = self._calculate_results(home_score, guest_score, let_ball, status_category, lottery_type, home_half, guest_half); display_handicap = ""
                if lottery_type in ['jczq', 'bjdc'] and let_ball and let_ball != '0' and let_ball != '0.0':
                    try: handicap_val = int(float(let_ball)); display_handicap = f"({handicap_val:+d})"
                    except (ValueError, TypeError): pass
                home_team_display = f"{home_team} {display_handicap}".strip()
                row_values = (match_num, match_time_display, str(match.get('sort', i)), home_team_display, 'vs', away_team, half_time_str, score_str, status_str, result_str)
                processed_data.append({'values': row_values, 'tag': status_category})
            return processed_data
        except Exception as e: return f"获取或处理数据时发生错误: {traceback.format_exc()}"

    def _get_basic_info(self, match_data, lottery_type, index, issue):
        if lottery_type == 'bjdc': jc_num_val = match_data.get('jcNum'); match_num = f"北单{int(jc_num_val) - 11}" if jc_num_val else "无北单号"
        else: match_num = str(match_data.get('matchNum') or match_data.get('jcNum') or index)
        match_time_full = match_data.get('matchTime', ''); time_format = '%m-%d %H:%M'
        if isinstance(match_time_full, str) and match_time_full and lottery_type in ['jczq', 'bjdc']:
            try: return match_num, datetime.strptime(f"{issue} {match_time_full}", '%Y-%m-%d %H:%M').strftime(time_format)
            except: return match_num, '时间错误' 
        elif isinstance(match_time_full, int):
            try: return match_num, datetime.fromtimestamp(match_time_full / 1000).strftime(time_format)
            except: return match_num, '时间错误'
        return match_num, ''

    # ======================= v31.0 核心修复 =========================
    def get_status_info(self, match_details):
        """
        根据权威状态（顶层matchStatus）决定判断逻辑，建立防火墙。
        """
        # 优先1：检查顶层 'matchStatus' 是否为取消
        if match_details.get('matchStatus') == -1:
            return "取消", "cancelled"

        # 优先2：检查顶层 'matchStatus' 是否为未开赛 (值0和1都代表未开始)
        # 这是“防火墙”，如果满足此条件，则绝不查看 'footballLiveScore' 里的状态。
        if match_details.get('matchStatus') in [0, 1]:
            return "未开赛", "not_started"
            
        # 只有通过了上述检查（即比赛已开始或已结束），我们才查看详细信息
        score_source = match_details.get('footballLiveScore', match_details)
        status_enum = score_source.get('statusEnum')

        if status_enum in [2, 4]: # 进行中
            live_time = score_source.get('liveTime')
            # 增加一个判断，避免显示-1'
            return (f"{live_time}′" if live_time is not None and live_time > 0 else "进行中"), "in_progress"
        elif status_enum == 3:  # 中场
            return "中场", "in_progress"
        elif status_enum in [8, 5, 6, 7]:  # 完赛
            return "完", "finished"
        
        # 如果有其他未知的详细状态，则返回一个安全的默认值
        return "未开赛", "not_started"
    # ======================= 核心修复结束 =========================

    def _calculate_results(self, home_score, guest_score, let_ball, status_category, lottery_type, home_half_score=None, guest_half_score=None):
        if status_category == 'cancelled': return "取消"
        if status_category != 'finished' or home_score is None or guest_score is None: return ""
        try: home_s, guest_s = int(home_score), int(guest_score)
        except (ValueError, TypeError): return ""
        spf_map, code_map = {1: "胜", 0: "平", -1: "负"}, {1: '3', 0: '1', -1: '0'}; comp = 1 if home_s > guest_s else -1 if home_s < guest_s else 0; spf_text, spf_code = spf_map.get(comp), code_map.get(comp)
        if lottery_type == 'jqs': return f"{'3' if home_s >= 3 else home_s}{'3' if guest_s >= 3 else guest_s}"
        if lottery_type == 'bqc':
            if home_half_score is None or guest_half_score is None: return ""
            try: half_h, half_g = int(home_half_score), int(guest_half_score); half_comp = 1 if half_h > half_g else -1 if half_h < half_g else 0; return f"{code_map.get(half_comp,'')}{spf_code}"
            except: return ""
        if lottery_type == 'sfc': return spf_code
        if lottery_type in ['jczq', 'bjdc']:
            try:
                let_f = float(let_ball);
                if let_f == 0.0: return spf_text
                rq_comp = 1 if (home_s + let_f) > guest_s else -1 if (home_s + let_f) < guest_s else 0; rq_spf = f"让{spf_map.get(rq_comp)}"
                return f"{spf_text} / {rq_spf}" if lottery_type == 'jczq' else rq_spf
            except: return spf_text
        return spf_text
        
    def update_ui_with_results(self, tree, data, original_issue):
        current_tab_info = self.get_current_tab_info()
        if not current_tab_info or tree != current_tab_info['tree'] or original_issue != current_tab_info['issue_var'].get(): self.schedule_refresh(); return
        for i in tree.get_children(): tree.delete(i)
        result_string_var, lottery_type = current_tab_info['result_string_var'], current_tab_info['type']
        if isinstance(data, str): messagebox.showinfo("提示", data) if "Traceback" not in data else messagebox.showerror("发生未知错误", data); self.update_status(f"获取 {original_issue} 数据失败"); result_string_var.set(" ")
        else:
            for row_data in data: tree.insert('', 'end', values=row_data['values'], tags=(row_data['tag'],))
            self.update_status(f"{original_issue} 数据刷新成功！")
            if lottery_type in ['jqs', 'bqc', 'sfc']: final_result_string = "".join([str(row['values'][9]) if row['tag'] == 'finished' else '*' for row in data]); result_string_var.set(final_result_string or " ")
            else: result_string_var.set(" ")
            if lottery_type in ['jczq', 'bjdc']: tree.yview_moveto(1.0)
        self.schedule_refresh()

    def create_menu(self): menu_bar = tk.Menu(self); self.config(menu=menu_bar); file_menu = tk.Menu(menu_bar, tearoff=0); menu_bar.add_cascade(label="文件", menu=file_menu); file_menu.add_command(label="退出", command=self.quit)
    def handle_auto_refresh_toggle(self): self.cancel_timer(); self.get_current_tab_info() and self.get_current_tab_info()['auto_refresh_var'].get() and self.schedule_refresh()
    def schedule_refresh(self): self.cancel_timer(); self.get_current_tab_info() and self.get_current_tab_info()['auto_refresh_var'].get() and setattr(self, 'active_timer', self.after(60000, lambda: self.start_fetch_thread(is_manual=False)))
    def cancel_timer(self): self.active_timer and self.after_cancel(self.active_timer); self.active_timer = None
    def get_current_tab_info(self):
        try: return self.tabs_info[self.notebook.tab(self.notebook.select(), "text")]
        except: return None
    def initial_load(self): self.notebook.update_idletasks(); self.on_tab_change()
    def get_initial_issue(self, lottery_type):
        if lottery_type in ["jczq", "bjdc"]: now = datetime.now(); return (now - timedelta(days=1) if 0 <= now.hour < 12 else now).strftime('%Y-%m-%d')
        else: return self.get_current_issue_from_api(lottery_type)
    def change_issue(self, delta):
        current_tab_info = self.get_current_tab_info();
        if not current_tab_info or current_tab_info['type'] in ['jczq', 'bjdc']: return
        try: issue_var = current_tab_info['issue_var']; issue_var.set(str(int(issue_var.get()) + delta)); self.start_fetch_thread(is_manual=True)
        except: messagebox.showwarning("提示", "当前期号非数字。"); self.start_fetch_thread(is_manual=True)
    def change_date(self, days_delta):
        current_tab_info = self.get_current_tab_info();
        if not current_tab_info or current_tab_info['type'] not in ['jczq', 'bjdc']: return
        try: issue_var = current_tab_info['issue_var']; issue_var.set((datetime.strptime(issue_var.get(), '%Y-%m-%d') + timedelta(days=days_delta)).strftime('%Y-%m-%d')); self.start_fetch_thread(is_manual=True)
        except: messagebox.showwarning("提示", "日期格式错误。"); current_tab_info['issue_var'].set(datetime.now().strftime('%Y-%m-%d')); self.start_fetch_thread(is_manual=True)
    def on_tab_change(self, event=None):
        current_tab_info = self.get_current_tab_info()
        if current_tab_info and not current_tab_info['issue_var'].get():
            issue = self.get_initial_issue(current_tab_info['type']); issue and current_tab_info['issue_var'].set(issue)
        self.start_fetch_thread(is_manual=True)
    def start_fetch_thread(self, is_manual=False):
        self.cancel_timer(); current_tab_info = self.get_current_tab_info()
        if not current_tab_info: return
        lottery_type, issue_var, tree_widget = current_tab_info['type'], current_tab_info['issue_var'], current_tab_info['tree']; issue = issue_var.get()
        if not issue: issue = self.get_initial_issue(lottery_type);
        if not issue: messagebox.showwarning("提示", "无法获取期号/日期。"); self.schedule_refresh(); return
        issue_var.get() or issue_var.set(issue)
        if is_manual: self.update_status(f"正在获取 {issue} 的数据..."); [tree.delete(i) for i in tree_widget.get_children()]
        threading.Thread(target=self.fetch_and_display, args=(lottery_type, issue, tree_widget, is_manual), daemon=True).start()
    def fetch_and_display(self, lottery_type, issue, tree_widget, is_manual):
        not is_manual and self.update_status(f"自动刷新 {issue} 数据中..."); result_data = self.fetch_all_data(lottery_type, issue); self.after(0, self.update_ui_with_results, tree_widget, result_data, issue)
    def update_status(self, message): self.after(0, self.status_bar.config, {'text': message})
    def get_current_issue_from_api(self, lottery_type):
        api_map = {"sfc": "rj", "jqs": "jqc", "bqc": "bqc"}
        if lottery_type in api_map:
            try:
                data = requests.get(self.API_BASE_DEGREE_LIST.format(api_map[lottery_type]), timeout=10).json()
                if data.get('code') == 200:
                    degree_list = data.get('data', {}).get('degreeList', [])
                    if degree_list: return str(next((i.get('degree') for i in degree_list if i.get('degreeStatus') == 1), degree_list[0].get('degree')))
            except: self.update_status("网络错误，无法获取最新期号")
        return None

if __name__ == "__main__":
    app = ScoreApp()
    app.mainloop()

