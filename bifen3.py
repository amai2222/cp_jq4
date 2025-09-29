import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime, timedelta
import threading
import traceback
import time
import json

class ScoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # 更新版本号
        self.title("实时比分查看工具 (v43.1 - 优化进行中颜色)")
        self.geometry("1530x600")
        self.match_data_map = {}
        self.API_MATCH_LIST = {"jczq": "https://sports.163.com/caipiao/api/web/match/list/jingcai/matchList/1?days={}", "bjdc": "https://sports.163.com/caipiao/api/web/match/list/beijing/matchList/1?days={}", "sfc": "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/rj?degree={}", "jqs": "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/jqc?degree={}", "bqc": "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/bqc?degree={}"}
        self.API_BASE_DEGREE_LIST = "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/{}" 
        self.API_LIVE_SCORES = "https://sports.163.com/caipiao/api/web/match/list/getMatchInfoList/1?matchInfoIds={}"
        self.active_timer = None
        self.create_menu()
        main_frame = ttk.Frame(self, padding="10"); main_frame.pack(fill=tk.BOTH, expand=True)
        self.notebook = ttk.Notebook(main_frame); self.notebook.pack(fill=tk.BOTH, expand=True)
        self.tabs_info = {"竞彩": {"type": "jczq"}, "北单": {"type": "bjdc"}, "胜负彩和任九": {"type": "sfc"}, "4场进球": {"type": "jqs"}, "6场半全场": {"type": "bqc"}}
        for name, info in self.tabs_info.items():
            frame = self.create_tab(self.notebook, name, info["type"]); self.notebook.add(frame, text=name)
        self.status_bar = tk.Label(self, text="准备就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W); self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.after(200, self.initial_load)
        
    def create_tab(self, parent, name, lottery_type):
        frame = ttk.Frame(parent, padding="10"); control_frame = ttk.Frame(frame); control_frame.pack(fill=tk.X, pady=5)
        is_date_based = lottery_type in ['jczq', 'bjdc']; label_text = "比赛日期:" if is_date_based else "期号:"; ttk.Label(control_frame, text=label_text).pack(side=tk.LEFT, padx=(0, 5)); issue_var = tk.StringVar()
        if not is_date_based: ttk.Button(control_frame, text="上一期", command=lambda: self.change_issue(-1)).pack(side=tk.LEFT)
        else: ttk.Button(control_frame, text="前一天", command=lambda: self.change_date(-1)).pack(side=tk.LEFT)
        ttk.Entry(control_frame, textvariable=issue_var, width=15, justify='center').pack(side=tk.LEFT, padx=5)
        if not is_date_based: ttk.Button(control_frame, text="下一期", command=lambda: self.change_issue(1)).pack(side=tk.LEFT)
        else: ttk.Button(control_frame, text="后一天", command=lambda: self.change_date(1)).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="刷新", command=lambda: self.start_fetch_thread(is_manual=True)).pack(side=tk.LEFT, padx=(10, 0))
        auto_refresh_var = tk.BooleanVar(value=True); ttk.Checkbutton(control_frame, text="每分钟自动刷新", variable=auto_refresh_var, command=self.handle_auto_refresh_toggle).pack(side=tk.LEFT, padx=(10,0))
        result_string_var = tk.StringVar(); result_string_label = ttk.Label(control_frame, textvariable=result_string_var, font=('Helvetica', 12, 'bold'), foreground='red'); result_string_label.pack(side=tk.LEFT, padx=(20, 0)); result_string_label.config(cursor="hand2"); result_string_label.bind("<Button-1>", self.copy_to_clipboard)
        tree_frame = ttk.Frame(frame); tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        columns = ('match_num', 'match_time', 'sequence', 'home_team', 'vs', 'away_team', 'half_score', 'score', 'status', 'result', 'home_sp', 'draw_sp', 'away_sp', 'path')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings'); scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side=tk.RIGHT, fill=tk.Y); tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree.bind("<Double-1>", self.on_match_double_click)
        
        headings = {'match_num': '场次', 'match_time': '时间', 'sequence': '次序', 'home_team': '主队', 'vs': '', 'away_team': '客队', 'half_score': '半场', 'score': '比分', 'status': '状态', 'result': '赛果', 'home_sp': '正', 'draw_sp': '平', 'away_sp': '负', 'path': '正反路'}
        widths = {'match_num': 80, 'match_time': 110, 'sequence': 50, 'home_team': 150, 'vs': 30, 'away_team': 150, 'half_score': 80, 'score': 100, 'status': 80, 'result': 120, 'home_sp': 60, 'draw_sp': 60, 'away_sp': 60, 'path': 60}
        anchors = {'match_num': tk.CENTER, 'match_time': tk.CENTER, 'sequence': tk.CENTER, 'home_team': tk.E, 'vs': tk.CENTER, 'away_team': tk.W, 'half_score': tk.CENTER, 'score': tk.CENTER, 'status': tk.CENTER, 'result': tk.CENTER, 'home_sp': tk.CENTER, 'draw_sp': tk.CENTER, 'away_sp': tk.CENTER, 'path': tk.CENTER}
        
        for col in columns: tree.heading(col, text=headings[col]); tree.column(col, width=widths[col], anchor=anchors[col])
        
        # ======================= v43.1 修改：将“进行中”的颜色改为绿色 ========================
        tree.tag_configure('in_progress', foreground='green') # 进行中 (绿色)
        tree.tag_configure('finished', foreground='black')      # 已完赛 (黑色)
        tree.tag_configure('not_started', foreground='gray')     # 未开赛 (灰色)
        tree.tag_configure('cancelled', foreground='blue')       # 已取消 (蓝色)
        tree.tag_configure('path_alert', foreground='red')       # 路径警示 (红色，高优先级)

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
                live_data = live_data_map.get(str(match.get('matchInfoId')), {}); final_match_data = {**match, **live_data}; status_str, status_category = self.get_status_info(final_match_data)
                match_num, match_time_display = self._get_basic_info(final_match_data, lottery_type, i, issue); home_team = final_match_data.get('homeTeam', {}).get('teamName', 'N/A'); away_team = final_match_data.get('guestTeam', {}).get('teamName', 'N/A')
                score_source = final_match_data.get('footballLiveScore', final_match_data); home_score, guest_score, home_half, guest_half = score_source.get('homeScore'), score_source.get('guestScore'), score_source.get('homeHalfScore'), score_source.get('guestHalfScore')
                score_str = "- : -" if status_category == 'cancelled' else f"{home_score} - {guest_score}" if home_score is not None else '- : -'; half_time_str = "" if status_category == 'cancelled' else f"{home_half} - {guest_half}" if home_half is not None else ''

                let_ball = '0';
                if final_match_data.get('playMap'):
                    if lottery_type == 'jczq': let_ball = str(final_match_data.get('playMap', {}).get('HHDA', {}).get('concede', '0'))
                    elif lottery_type == 'bjdc': let_ball = str(final_match_data.get('playMap', {}).get('BJ_HDA', {}).get('concede', '0'))
                
                result_str = self._calculate_results(home_score, guest_score, let_ball, status_category, lottery_type, home_half, guest_half);
                hda_odds = self._get_hda_odds(final_match_data); home_sp, draw_sp, away_sp = hda_odds.get('主胜', '-'), hda_odds.get('平', '-'), hda_odds.get('客胜', '-'); path_str = self._calculate_path(home_score, guest_score, status_category, hda_odds)

                display_handicap = ""
                if lottery_type in ['jczq', 'bjdc'] and let_ball and let_ball != '0' and let_ball != '0.0':
                    try: handicap_val = int(float(let_ball)); display_handicap = f"({handicap_val:+d})"
                    except (ValueError, TypeError): pass
                home_team_display = f"{home_team} {display_handicap}".strip()
                row_values = (match_num, match_time_display, str(match.get('sort', i)), home_team_display, 'vs', away_team, half_time_str, score_str, status_str, result_str, home_sp, draw_sp, away_sp, path_str)
                
                current_tags = []
                is_path_alert = path_str in ["反路", "平"]

                if is_path_alert:
                    # 如果需要高亮，就只用 'path_alert' 标签来决定颜色 (红色)
                    current_tags.append('path_alert')
                else:
                    # 如果不需要高亮，就用常规的状态标签决定颜色 (例如, 'in_progress' 会是绿色)
                    current_tags.append(status_category)

                processed_data.append({'values': row_values, 'tags': tuple(current_tags), 'full_data': final_match_data, 'status_category': status_category})
            return processed_data
        except Exception: return f"获取或处理数据时发生错误: {traceback.format_exc()}"

    def update_ui_with_results(self, tree, data, original_issue):
        current_tab_info = self.get_current_tab_info()
        if not current_tab_info or tree != current_tab_info['tree'] or original_issue != current_tab_info['issue_var'].get(): self.schedule_refresh(); return
        tree.delete(*tree.get_children()); self.match_data_map.clear()
        result_string_var, lottery_type = current_tab_info['result_string_var'], current_tab_info['type']
        if isinstance(data, str): 
            messagebox.showinfo("提示", data) if "Traceback" not in data else messagebox.showerror("发生未知错误", data)
            self.update_status(f"获取 {original_issue} 数据失败"); result_string_var.set(" ")
        else:
            for row_data in data:
                item_id = tree.insert('', 'end', values=row_data['values'], tags=row_data['tags'])
                self.match_data_map[item_id] = row_data['full_data']
            self.update_status(f"{original_issue} 数据刷新成功！")
            
            if lottery_type in ['jqs', 'bqc', 'sfc']:
                final_result_string = "".join([str(row['values'][9]) if row.get('status_category') == 'finished' else '*' for row in data])
                result_string_var.set(final_result_string or " ")
            else:
                result_string_var.set(" ")

            if lottery_type in ['jczq', 'bjdc']: tree.yview_moveto(1.0)
        self.schedule_refresh()

    def on_match_double_click(self, event):
        item_id = event.widget.focus(); item_id and (lambda data: self.show_odds_popup(data) if data else messagebox.showinfo("提示", "未找到该比赛的详细数据。"))(self.match_data_map.get(item_id))

    def show_debug_window(self, data, parent_popup):
        debug_popup = tk.Toplevel(self); debug_popup.title("原始数据 (JSON)"); debug_popup.geometry("600x600"); debug_popup.transient(parent_popup); debug_popup.grab_set()
        text_frame = ttk.Frame(debug_popup, padding=10); text_frame.pack(fill=tk.BOTH, expand=True)
        text_widget = tk.Text(text_frame, wrap=tk.WORD, undo=True); scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview); text_widget.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side=tk.RIGHT, fill=tk.Y); text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        try: text_widget.insert(tk.END, json.dumps(data, indent=4, ensure_ascii=False))
        except Exception as e: text_widget.insert(tk.END, f"无法格式化JSON数据: {e}\n\n原始数据:\n{data}")
        text_widget.config(state=tk.DISABLED)
        button_frame = ttk.Frame(debug_popup, padding=(10,0,10,10)); button_frame.pack(fill=tk.X); ttk.Button(button_frame, text="关闭", command=debug_popup.destroy).pack()

    def show_odds_popup(self, match_data):
        popup = tk.Toplevel(self); popup.transient(self); popup.grab_set(); popup.resizable(False, False)
        home_team, away_team = match_data.get('homeTeam', {}).get('teamName', '主队'), match_data.get('guestTeam', {}).get('teamName', '客队'); popup.title(f"{home_team} vs {away_team} - 赔率详情")
        main_frame = ttk.Frame(popup, padding=10); main_frame.pack(fill=tk.BOTH, expand=True)
        content_frame = ttk.Frame(main_frame); content_frame.pack(fill=tk.X, expand=True)
        has_odds_displayed = False
        play_map = match_data.get('playMap', {}); hda_data_node = play_map.get('HDA') or play_map.get('BJ_HDA')
        if hda_data_node:
            odds_list = hda_data_node.get('playItemList') or hda_data_node.get('options')
            if odds_list:
                has_odds_displayed = True
                frame = ttk.LabelFrame(content_frame, text="胜平负 (在售)", padding=10); frame.pack(fill=tk.X, pady=5)
                name_map = {"Home": "主胜", "Draw": "平", "Away": "客胜"}; parsed_odds = []
                for item in odds_list:
                    name = item.get('playItemName'); sp = item.get('odds')
                    if name is None: name = name_map.get(item.get('name'))
                    if sp is None: sp = item.get('sp')
                    if name in ["主胜", "平", "客胜"]: parsed_odds.append({'name': name, 'sp': sp})
                for a_odd in sorted(parsed_odds, key=lambda x: ["主胜", "平", "客胜"].index(x['name'])):
                    ttk.Label(frame, text=f"{a_odd['name']}: {a_odd['sp']}", width=15).pack(side=tk.LEFT, padx=5)
        if not has_odds_displayed:
            spf_items = [i for i in match_data.get('playItemList', []) if i.get('playName') == '胜负']
            if spf_items:
                has_odds_displayed = True
                frame = ttk.LabelFrame(content_frame, text="胜平负 (最终)", padding=10); frame.pack(fill=tk.X, pady=5)
                for item in sorted(spf_items, key=lambda x: ['主胜', '平', '客胜'].index(x.get('playItemName', '')) if x.get('playItemName') in ['主胜', '平', '客胜'] else 99):
                    is_result = item.get('result') == 1
                    ttk.Label(frame, text=f"{item.get('playItemName')}: {item.get('odds', 'N/A')}", width=15, foreground='red' if is_result else 'black').pack(side=tk.LEFT, padx=5)
        if not has_odds_displayed: ttk.Label(content_frame, text="无“胜平负”赔率数据。").pack(padx=20, pady=10)
        separator = ttk.Separator(main_frame, orient='horizontal'); separator.pack(fill='x', pady=10)
        button_frame = ttk.Frame(main_frame); button_frame.pack(fill=tk.X, expand=True)
        ttk.Button(button_frame, text="显示原始数据", command=lambda: self.show_debug_window(match_data, popup)).pack(side=tk.LEFT, padx=(5,5))
        ttk.Button(button_frame, text="关闭", command=popup.destroy).pack(side=tk.RIGHT, padx=(5,5))
    
    def _get_basic_info(self, match_data, lottery_type, index, issue):
        if lottery_type == 'bjdc':
            jc_num_val = match_data.get('jcNum')
            if jc_num_val:
                numeric_part = "".join(filter(str.isdigit, str(jc_num_val)))
                if numeric_part:
                    try: calculated_num = int(numeric_part) - 11; match_num = f"北单{calculated_num}"
                    except ValueError: match_num = str(jc_num_val)
                else: match_num = str(jc_num_val)
            else: match_num = "无北单号"
        else: match_num = str(match_data.get('matchNum') or match_data.get('jcNum') or index)
        match_time_full = match_data.get('matchTime', ''); time_format = '%m-%d %H:%M'
        if isinstance(match_time_full, str) and match_time_full and lottery_type in ['jczq', 'bjdc']:
            try: return match_num, datetime.strptime(f"{issue} {match_time_full}", '%Y-%m-%d %H:%M').strftime(time_format)
            except: return match_num, '时间错误' 
        elif isinstance(match_time_full, int):
            try: return match_num, datetime.fromtimestamp(match_time_full / 1000).strftime(time_format)
            except: return match_num, '时间错误'
        return match_num, ''

    def get_status_info(self, match_details):
        if match_details.get('matchStatus') == -1: return "取消", "cancelled"
        if match_details.get('matchStatus') in [0, 1]: return "未开赛", "not_started"
        score_source = match_details.get('footballLiveScore', match_details); status_enum = score_source.get('statusEnum')
        if status_enum in [2, 4]: live_time = score_source.get('liveTime'); return (f"{live_time}′" if live_time is not None and live_time > 0 else "进行中"), "in_progress"
        elif status_enum == 3:  return "中场", "in_progress"
        elif status_enum in [8, 5, 6, 7]:  return "完", "finished"
        return "未开赛", "not_started"

    def _get_hda_odds(self, match_data):
        odds_dict = {}; play_map = match_data.get('playMap', {}); hda_data_node = play_map.get('HDA') or play_map.get('BJ_HDA')
        if hda_data_node:
            odds_list = hda_data_node.get('playItemList') or hda_data_node.get('options')
            if odds_list:
                name_map = {"Home": "主胜", "Draw": "平", "Away": "客胜"}
                for item in odds_list:
                    name = item.get('playItemName'); sp = item.get('odds')
                    if name is None: name = name_map.get(item.get('name'))
                    if sp is None: sp = item.get('sp')
                    if name in ["主胜", "平", "客胜"]: odds_dict[name] = sp
        if not odds_dict:
            spf_items = [i for i in match_data.get('playItemList', []) if i.get('playName') == '胜负']
            for item in spf_items:
                name = item.get('playItemName')
                if name in ["主胜", "平", "客胜"]: odds_dict[name] = item.get('odds', '-')
        return odds_dict

    def _calculate_path(self, home_score, guest_score, status_category, odds_dict):
        if status_category not in ['in_progress', 'finished']: return ""
        try: home_s, guest_s = int(home_score), int(guest_score)
        except (ValueError, TypeError): return ""
        if home_s > guest_s: actual_result = "主胜"
        elif home_s < guest_s: actual_result = "客胜"
        else: return "平"
        if not odds_dict: return ""
        float_odds = {};
        for name, sp in odds_dict.items():
            try: float_odds[name] = float(sp)
            except (ValueError, TypeError): continue
        if not float_odds: return ""
        favorite_result = min(float_odds, key=float_odds.get)
        return "正路" if actual_result == favorite_result else "反路"

    def _calculate_results(self, home_score, guest_score, let_ball, status_category, lottery_type, home_half_score=None, guest_half_score=None):
        spf_map, code_map = {1: "胜", 0: "平", -1: "负"}, {1: '3', 0: '1', -1: '0'}
        if status_category == 'cancelled': return "取消"
        if status_category != 'finished' or home_score is None or guest_score is None: return ""
        try: home_s, guest_s = int(home_score), int(guest_score)
        except (ValueError, TypeError): return ""
        comp = 1 if home_s > guest_s else -1 if home_s < guest_s else 0
        spf_text, spf_code = spf_map.get(comp), code_map.get(comp)
        if lottery_type == 'jqs': return f"{'3' if home_s >= 3 else home_s}{'3' if guest_s >= 3 else guest_s}"
        if lottery_type == 'bqc':
            if home_half_score is None or guest_half_score is None: return ""
            try: 
                half_h, half_g = int(home_half_score), int(guest_half_score)
                half_comp = 1 if half_h > half_g else -1 if half_h < half_g else 0
                return f"{code_map.get(half_comp,'')}{spf_code}"
            except: return ""
        if lottery_type == 'sfc': return spf_code
        if lottery_type in ['jczq', 'bjdc']:
            try:
                let_f = float(let_ball)
                rqspf_map = {1: "让胜", 0: "让平", -1: "让负"}
                rq_comp = 1 if (home_s + let_f) > guest_s else -1 if (home_s + let_f) < guest_s else 0
                rq_spf = rqspf_map.get(rq_comp)
                if lottery_type == 'bjdc': return rq_spf
                return f"{spf_text} / {rq_spf}" if let_f != 0.0 else spf_text
            except: return spf_text
        return spf_text

    def create_menu(self): menu_bar = tk.Menu(self); self.config(menu=menu_bar); file_menu = tk.Menu(menu_bar, tearoff=0); menu_bar.add_cascade(label="文件", menu=file_menu); file_menu.add_command(label="退出", command=self.quit)
    def handle_auto_refresh_toggle(self): self.cancel_timer(); self.get_current_tab_info() and self.get_current_tab_info()['auto_refresh_var'].get() and self.schedule_refresh()
    def schedule_refresh(self): self.cancel_timer(); info = self.get_current_tab_info(); info and info['auto_refresh_var'].get() and setattr(self, 'active_timer', self.after(60000, lambda: self.start_fetch_thread(is_manual=False)))
    def cancel_timer(self): self.active_timer and self.after_cancel(self.active_timer); self.active_timer = None
    def get_current_tab_info(self):
        try: return self.tabs_info[self.notebook.tab(self.notebook.select(), "text")]
        except: return None
    def initial_load(self): self.notebook.update_idletasks(); self.on_tab_change()
    def get_initial_issue(self, lottery_type):
        if lottery_type in ["jczq", "bjdc"]: now = datetime.now(); return (now - timedelta(days=1) if 0 <= now.hour < 12 else now).strftime('%Y-%m-%d')
        else: return self.get_current_issue_from_api(lottery_type)
    def change_issue(self, delta):
        info = self.get_current_tab_info();
        if not info or info['type'] in ['jczq', 'bjdc']: return
        try: var = info['issue_var']; var.set(str(int(var.get()) + delta)); self.start_fetch_thread(is_manual=True)
        except: messagebox.showwarning("提示", "当前期号非数字。"); self.start_fetch_thread(is_manual=True)
    def change_date(self, days_delta):
        info = self.get_current_tab_info();
        if not info or info['type'] not in ['jczq', 'bjdc']: return
        try: var = info['issue_var']; var.set((datetime.strptime(var.get(), '%Y-%m-%d') + timedelta(days=days_delta)).strftime('%Y-%m-%d')); self.start_fetch_thread(is_manual=True)
        except: messagebox.showwarning("提示", "日期格式错误。"); info['issue_var'].set(datetime.now().strftime('%Y-%m-%d')); self.start_fetch_thread(is_manual=True)
    def on_tab_change(self, event=None):
        info = self.get_current_tab_info()
        if info and not info['issue_var'].get():
            issue = self.get_initial_issue(info['type']); issue and info['issue_var'].set(issue)
        self.start_fetch_thread(is_manual=True)

    def start_fetch_thread(self, is_manual=False):
        self.cancel_timer(); info = self.get_current_tab_info()
        if not info: return
        lottery_type, issue_var, tree = info['type'], info['issue_var'], info['tree']; issue = issue_var.get()
        if not issue: issue = self.get_initial_issue(lottery_type) or (issue_var.set(""),"")[1]; issue_var.set(issue)
        if not issue: messagebox.showwarning("提示", "无法获取期号/日期。"); self.schedule_refresh(); return
        if is_manual: self.update_status(f"正在获取 {issue} 的数据..."); tree.delete(*tree.get_children())
        threading.Thread(target=self.fetch_and_display, args=(lottery_type, issue, tree, is_manual), daemon=True).start()

    def fetch_and_display(self, lottery_type, issue, tree_widget, is_manual):
        if not is_manual: self.update_status(f"自动刷新 {issue} 数据中...")
        result_data = self.fetch_all_data(lottery_type, issue); self.after(0, self.update_ui_with_results, tree_widget, result_data, issue)

    def update_status(self, message): self.status_bar.config(text=message)

    def get_current_issue_from_api(self, lottery_type):
        api_map = {"sfc": "rj", "jqs": "jqc", "bqc": "bqc"}
        if lottery_type in api_map:
            try:
                data = requests.get(self.API_BASE_DEGREE_LIST.format(api_map[lottery_type]), timeout=10).json()
                if data.get('code') != 200: return None
                degree_list = data.get('data', {}).get('degreeList', [])
                if not degree_list: return None
                current = next((item for item in degree_list if item.get('degreeStatus') == 1), None)
                if current: return str(current.get('degree'))
                future = next((item for item in degree_list if item.get('degreeStatus') == 2), None)
                if future: return str(future.get('degree'))
                latest = max(degree_list, key=lambda x: int(x.get('degree', 0)))
                return str(latest.get('degree'))
            except Exception as e: self.update_status(f"网络错误，无法获取最新期号: {e}")
        return None

if __name__ == "__main__":
    app = ScoreApp()
    app.mainloop()
