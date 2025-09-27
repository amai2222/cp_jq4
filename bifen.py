import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
from datetime import datetime
import threading
import urllib.parse
import traceback

class DebugWindow(tk.Toplevel):
    """一个独立的调试日志窗口"""
    def __init__(self, master=None):
        super().__init__(master)
        self.title("调试日志")
        self.geometry("800x600")
        self.log_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=("Consolas", 10))
        self.log_text.pack(expand=True, fill=tk.BOTH)
        self.log_text.config(state=tk.DISABLED)
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

    def log(self, message):
        """向日志窗口追加消息"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def show(self):
        self.deiconify()

    def hide_window(self):
        self.withdraw()

class ScoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("网易彩票数据获取工具 (v7.0 - Final Fix)")
        self.geometry("700x500")

        # --- API 配置 ---
        self.API_GET_CURRENT_ISSUE = "https://sports.163.com/caipiao/api/web/jc/queryCurrentPeriod.html?gameEn={}"
        self.API_MATCH_LIST = {
            "jczq": "https://sports.163.com/caipiao/api/web/match/list/jingcai/matchList/1?days={}",
            "sfc": "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/sfc?degree={}",
            "bjdc": "https://sports.163.com/caipiao/api/web/match/list/zucai/matchList/bjdc?degree={}"
        }
        self.API_LIVE_SCORES = "https://sports.163.com/caipiao/api/web/match/list/getMatchInfoList/1?matchInfoIds={}"
        
        self.debug_window = DebugWindow(self)
        self.debug_window.withdraw()

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
        self.after(100, self.on_tab_change)

    def log_to_debug_window(self, message):
        self.after(0, self.debug_window.log, message)

    def create_menu(self):
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="退出", command=self.quit)
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="显示调试窗口", command=self.debug_window.show)

    def create_tab(self, parent, name, lottery_type):
        frame = ttk.Frame(parent, padding="10")
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=5)
        label_text = "比赛日期 (自动刷新):" if lottery_type == 'jczq' else "期号:"
        issue_label = ttk.Label(control_frame, text=label_text)
        issue_label.pack(side=tk.LEFT, padx=(0, 5))
        issue_var = tk.StringVar()
        issue_entry = ttk.Entry(control_frame, textvariable=issue_var, width=20)
        issue_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        fetch_button = ttk.Button(control_frame, text="获取/刷新", 
                                  command=lambda: self.start_fetch_thread(lottery_type, issue_var))
        fetch_button.pack(side=tk.LEFT, padx=(10, 0))
        result_text = scrolledtext.ScrolledText(frame, wrap="none", font=("Courier New", 10))
        result_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.tabs_info[name]['issue_var'] = issue_var
        self.tabs_info[name]['result_text'] = result_text
        return frame

    def on_tab_change(self, event=None):
        try:
            current_tab_name = self.notebook.tab(self.notebook.select(), "text")
            info = self.tabs_info[current_tab_name]
            threading.Thread(target=self.update_issue, args=(info["type"], info['issue_var']), daemon=True).start()
        except tk.TclError:
            pass

    def update_issue(self, lottery_type, issue_var):
        issue = self.get_current_issue(lottery_type)
        if issue:
            self.after(0, issue_var.set, issue)
            self.update_status(f"自动获取 {lottery_type} 最新期号成功！")
        else:
            self.update_status(f"自动获取 {lottery_type} 期号失败，请手动输入。")

    def start_fetch_thread(self, lottery_type, issue_var):
        issue = issue_var.get()
        if not issue and lottery_type != 'jczq':
            messagebox.showwarning("提示", "请输入有效的期号！")
            return
        tab_name = self.notebook.tab(self.notebook.select(), "text")
        result_text_widget = self.tabs_info[tab_name]['result_text']
        threading.Thread(target=self.fetch_and_display, 
                         args=(lottery_type, issue, result_text_widget), 
                         daemon=True).start()

    def fetch_and_display(self, lottery_type, issue, result_text_widget):
        self.update_status(f"正在获取 {issue} 的数据...")
        result_data = self.fetch_all_data(lottery_type, issue)
        self.after(0, self.update_ui_with_results, result_text_widget, result_data)

    def update_ui_with_results(self, result_text_widget, data):
        result_text_widget.config(state=tk.NORMAL)
        result_text_widget.delete("1.0", tk.END)
        result_text_widget.insert("1.0", data)
        result_text_widget.config(state=tk.DISABLED)
        if "错误" in data or "失败" in data or "未找到" in data:
            self.update_status("数据获取失败，详情请查看调试窗口。")
        else:
            self.update_status("数据获取/刷新成功！")

    def update_status(self, message):
        self.after(0, self.status_bar.config, {'text': message})

    def get_status_text(self, live_score_details):
        """根据传入的实时比分详情字典返回状态文本"""
        if not live_score_details:
            return "未知状态"
        
        # 优先使用 liveTime 和 status 字段，它们包含更生动的信息（如分钟数）
        live_time = live_score_details.get('liveTime', -1)
        status_text = live_score_details.get('status')
        if status_text and live_time > 0 and '′' in status_text:
            return status_text # e.g., "35′"

        # 如果没有分钟数信息，则使用 statusEnum 状态码
        status_enum = live_score_details.get('statusEnum')
        status_map = {1:"未开赛", 2:"上半场", 3:"中场", 8:"完", 9:"延期", 10:"取消", 13:"待定"}
        # 用 statusEnum 映射，如果还没有，用 status 映射
        return status_map.get(status_enum, status_text or "未知")

    def get_current_issue(self, lottery_type):
        if lottery_type == "jczq":
            return datetime.now().strftime('%Y-%m-%d')
        else:
            try:
                url = self.API_GET_CURRENT_ISSUE.format(lottery_type)
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                data = response.json()
                if data.get('code') == 200:
                    return data.get('data', {}).get('periodName')
            except Exception as e:
                self.log_to_debug_window(f"获取期号失败: {e}")
                return None

    def fetch_all_data(self, lottery_type, issue):
        try:
            if lottery_type == 'jczq':
                # 注意：这里我们使用用户输入的日期，而不是当前时间，以保持一致性
                # 如果输入框为空，则使用当前日期
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

            header = f"{'场次':<5}{'主队':<15} vs {'客队':<15}{'比分':<12}{'状态':<10}\n"
            separator = "-" * 70 + "\n"
            result_text = header + separator
            for match in matches:
                match_num = match.get('jcNum') if lottery_type == 'jczq' else match.get('matchNum', '')
                home_team = match.get('homeTeam', {}).get('teamName', 'N/A')
                away_team = match.get('guestTeam', {}).get('teamName', 'N/A')
                
                # --- 最终比分和状态解析逻辑 ---
                match_id_str = str(match.get('matchInfoId'))
                live_info = live_data_map.get(match_id_str, {})
                live_score_details = live_info.get('footballLiveScore', {})

                # 如果live_score_details 为空，说明实时数据里没有这场，也用原始match数据
                if not live_score_details: 
                    live_score_details = match.get('footballLiveScore', {})
                
                home_score = live_score_details.get('homeScore', '-')
                #  !!!!!!!!!!  核心BUG修复 !!!!!!!!!!!
                away_score = live_score_details.get('guestScore', '-') # Key是'guestScore'，不是'awayScore'
                #  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

                score_str = f"{home_score} - {away_score}"
                status_str = self.get_status_text(live_score_details)

                row = f"{match_num:<6}{home_team:<16} vs {away_team:<16}{score_str:<12}{status_str:<10}\n"
                result_text += row
            
            return result_text

        except Exception as e:
            error_trace = traceback.format_exc()
            self.log_to_debug_window(f"发生严重错误: {e}\n{error_trace}")
            return f"发生未知错误: {e}\n(详情请查看调试窗口)"

if __name__ == "__main__":
    app = ScoreApp()
    app.mainloop()

