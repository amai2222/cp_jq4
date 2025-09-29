import tkinter as tk
from tkinter import font, scrolledtext, filedialog, ttk, messagebox
import requests
import threading
from functools import reduce
from operator import mul

# --- 核心数据定义 (V3.5) ---
GAME_TYPE_BQC = 'bqc'
GAME_TYPE_JQC = 'jqc'

GAME_CONFIG = {
    GAME_TYPE_BQC: {
        "api_num": "98", "name": "6场半全场", "list_key": "bqclist", "result_len": 12,
        "placeholder": "支持单式和复式, 例如: (01)2(13)1(03)113"
    },
    GAME_TYPE_JQC: {
        "api_num": "94", "name": "4场进球", "list_key": "jqclist", "result_len": 8,
        "placeholder": "支持单式和复式, 例如: (01)2(123)3(12)1(023)3"
    }
}

# --- 核心功能 (保持不变) ---
def parse_complex_bet(bet_string, expected_len):
    bet_string = bet_string.strip().replace(" ", ""); parts = []; i = 0
    while i < len(bet_string):
        if bet_string[i].isdigit(): parts.append(bet_string[i]); i += 1
        elif bet_string[i] == '(':
            end_index = bet_string.find(')', i)
            if end_index == -1: return None
            content = bet_string[i+1:end_index]
            if not content.isdigit(): return None
            parts.append("".join(sorted(list(set(content))))); i = end_index + 1
        else: return None
    return parts if len(parts) == expected_len else None

def calculate_stakes(parsed_bet):
    if not parsed_bet: return 0
    return reduce(mul, (len(p) for p in parsed_bet), 1)

def check_win(parsed_bet, official_result):
    if len(parsed_bet) != len(official_result): return False
    for i, official_char in enumerate(official_result):
        if official_char not in parsed_bet[i]: return False
    return True

# --- API抓取功能 (保持不变) ---
def get_draw_list_and_default(game_type, count=5):
    config = GAME_CONFIG[game_type]; url = "https://webapi.sporttery.cn/gateway/lottery/getFootBallDrawInfoV1.qry?isVerify=1&param=94,0;90,0;98,0"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10); response.raise_for_status()
        data = response.json(); draw_list = data.get('value', {}).get(config["list_key"])
        if not data.get('success') or not isinstance(draw_list, list) or not draw_list:
            return {'success': False, 'message': '解析API数据失败或列表为空。'}
        return {'success': True, 'ids': draw_list[:count], 'default_id': draw_list[0] if draw_list else None}
    except Exception as e: return {'success': False, 'message': f'网络或获取期号时出错: {e}'}

def get_draw_details(game_type, draw_id):
    config = GAME_CONFIG[game_type]; api_num = config['api_num']
    base_url = f"https://webapi.sporttery.cn/gateway/lottery/getFootBallDrawInfoByDrawNumV1.qry?isVerify=1&lotteryGameNum={api_num}&lotteryDrawNum={draw_id}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(base_url, headers=headers, timeout=10); response.raise_for_status()
        data = response.json(); value_data = data.get('value')
        if not data.get('success') or not value_data:
            return {'status': 'not_found', 'message': f"第 {draw_id} 期不存在或数据异常。"}
        draw_time = value_data.get('lotteryDrawTime', '未知日期'); raw_draw_result = value_data.get('lotteryDrawResult')
        if not raw_draw_result:
            return {'status': 'pending', 'draw_id': draw_id, 'draw_time': draw_time, 'message': f"销售截止: {value_data.get('lotterySaleEndtime', '未知')}", 'matches': value_data.get('matchList', [])}
        cleaned_numbers = str(raw_draw_result).replace(' ', '').replace('+', '').replace('＋', '')
        final_result = {'status': 'drawn', 'draw_id': draw_id, 'numbers': cleaned_numbers, 'draw_time': draw_time, 'matches': value_data.get('matchList', []), 'prize_info': []}
        for item in value_data.get('prizeLevelList', []):
            if item.get('prizeLevel') == '一等奖':
                stake_count, stake_amount_str = item.get('stakeCount', 'N/A'), item.get('stakeAmount', 'N/A')
                try: formatted_amount = f"{int(float(stake_amount_str.replace(',', ''))):,}"
                except (ValueError, TypeError): formatted_amount = stake_amount_str
                final_result['prize_info'].append(f"一等奖: {stake_count} 注, 每注 {formatted_amount} 元"); break
        return final_result
    except Exception as e: return {'status': 'error', 'message': f"处理数据时发生错误: {e}"}

# --- GUI界面和事件处理逻辑 ---
class LotteryCheckerApp:
    def __init__(self, root):
        self.root = root
        ### [V3.10 修改] 更新版本号
        self.root.title("足彩兑奖器 (半全场/进球彩) V3.10 - 支持期号不存在时手工输入 + 自动排序 + 手工兑奖")
        self.root.geometry("1000x800"); self.root.minsize(800, 600)
        self.current_game_type = tk.StringVar(value=GAME_TYPE_BQC)
        self.setup_styles_and_fonts()
        try: from ctypes import windll; windll.shcore.SetProcessDpiAwareness(1)
        except ImportError: pass
        self.setup_scrollable_area(); self._create_widgets_and_layout(); self.on_main_game_selected()

    def setup_styles_and_fonts(self):
        self.style = ttk.Style(root); self.style.theme_use('clam')
        self.default_font = font.Font(family="Microsoft YaHei UI", size=12)
        self.bold_font = font.Font(family="Microsoft YaHei UI", size=13, weight="bold")
        self.courier_font = font.Font(family="Courier New", size=13)
        self.official_numbers_font = font.Font(family="Courier New", size=14, weight="bold")
        self.highlight_font = font.Font(family="Microsoft YaHei UI", size=13, weight="bold")
        self.prize_summary_font = font.Font(family="Microsoft YaHei UI", size=14)
        self.prize_summary_bold_font = font.Font(family="Microsoft YaHei UI", size=14, weight="bold")
        self.style.configure('.', font=self.default_font)
        self.style.configure('TLabel', font=self.default_font); self.style.configure('TButton', font=self.default_font)
        self.style.configure('TRadiobutton', font=self.default_font); self.style.configure('TLabelFrame.Label', font=self.bold_font)
        self.style.configure('Treeview.Heading', font=self.bold_font); self.style.configure('Treeview', rowheight=28, font=self.courier_font)
        self.style.configure('Success.TButton', font=self.bold_font, foreground='white', background='#28a745')
        self.style.map('Success.TButton', background=[('active', '#218838')])

    def setup_scrollable_area(self):
        container = ttk.Frame(self.root); container.pack(fill='both', expand=True)
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, padding="20")
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        scrollable_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(scrollable_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set); canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.root.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self.root.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        self.root.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    def _create_widgets_and_layout(self):
        # ... 布局代码保持不变 ...
        frame1 = ttk.LabelFrame(self.scrollable_frame, text="1. 选择玩法", padding="10"); frame1.pack(fill='x', pady=5)
        frame2 = ttk.LabelFrame(self.scrollable_frame, text="2. 选择/输入查询期号", padding="10"); frame2.pack(fill='x', pady=5)
        frame3 = ttk.LabelFrame(self.scrollable_frame, text="3. 开奖详情", padding="10"); frame3.pack(fill='both', expand=True, pady=5)
        frame4 = ttk.LabelFrame(self.scrollable_frame, text="4. 核对我的投注", padding="10"); frame4.pack(fill='both', expand=True, pady=5)
        frame5 = ttk.LabelFrame(self.scrollable_frame, text="5. 对奖结果", padding="10"); frame5.pack(fill='both', expand=True, pady=5)
        ttk.Radiobutton(frame1, text="6场半全场", variable=self.current_game_type, value=GAME_TYPE_BQC, command=self.on_main_game_selected).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(frame1, text="4场进球", variable=self.current_game_type, value=GAME_TYPE_JQC, command=self.on_main_game_selected).pack(side=tk.LEFT, padx=30)
        ttk.Label(frame2, text="选择期号:").pack(side=tk.LEFT, padx=(0, 5))
        self.draw_id_combo = ttk.Combobox(frame2, width=10, font=self.default_font); self.draw_id_combo.pack(side=tk.LEFT, padx=5)
        self.draw_id_combo.bind("<<ComboboxSelected>>", lambda e: self.fetch_data_threaded())
        self.refresh_button = ttk.Button(frame2, text="刷新期号", command=self.refresh_draw_list_threaded); self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        ### [V3.7 新增] 增加期号按钮 ###
        self.add_future_draw_button = ttk.Button(frame2, text="增加期号(+)", command=self.add_future_draw)
        self.add_future_draw_button.pack(side=tk.LEFT, padx=5)

        self.fetch_button = ttk.Button(frame2, text="获取详情", command=self.fetch_data_threaded); self.fetch_button.pack(side=tk.LEFT, padx=5)
        self.manual_button = ttk.Button(frame2, text="手工兑奖", command=self.manual_check_mode); self.manual_button.pack(side=tk.LEFT, padx=5)
        self.draw_time_label = ttk.Label(frame2, text="", font=self.highlight_font); self.draw_time_label.pack(side=tk.LEFT, padx=10)
        self.status_label = ttk.Label(frame2, text="", font=self.highlight_font, foreground="blue"); self.status_label.pack(side=tk.RIGHT, padx=10)
        self.prize_info_label = ttk.Label(frame3, text="", font=self.bold_font, foreground="red", justify=tk.LEFT); self.prize_info_label.pack(fill='x', anchor='w')

        ### [V3.7 修改] 提示用户可以手动输入 ###
        ttk.Label(frame3, text="官方开奖号码 (未开奖时可手动输入):").pack(anchor='w', pady=(5,0))
        self.official_numbers_var = tk.StringVar()
        ### [V3.7 修改] 将Entry控件赋值给实例变量，以便修改其状态 ###
        self.official_numbers_entry = ttk.Entry(frame3, textvariable=self.official_numbers_var, state='readonly', font=self.official_numbers_font)
        self.official_numbers_entry.pack(fill='x', pady=5)
        
        ttk.Label(frame3, text="对阵与赛果:").pack(anchor='w', pady=(5,0))
        self.match_details_text = scrolledtext.ScrolledText(frame3, height=5, font=self.courier_font, wrap=tk.WORD, relief='solid', borderwidth=1); self.match_details_text.pack(fill='x', expand=True, pady=(2,5))
        self.user_bets_label = ttk.Label(frame4, text="", justify=tk.LEFT); self.user_bets_label.pack(anchor='w')
        self.user_bets_text = scrolledtext.ScrolledText(frame4, height=10, font=self.courier_font, wrap=tk.WORD, relief='solid', borderwidth=1); self.user_bets_text.pack(fill='x', expand=True, pady=5)
        button_frame = ttk.Frame(frame4); button_frame.pack(fill='x', pady=(5,0))
        self.import_button = ttk.Button(button_frame, text="从文件导入(.txt)", command=self.import_from_file); self.import_button.pack(side=tk.LEFT)
        self.sort_button = ttk.Button(button_frame, text="自动排序", command=self.sort_bets); self.sort_button.pack(side=tk.LEFT, padx=5)
        self.check_button = ttk.Button(button_frame, text="开始对奖 >>", style='Success.TButton', command=self.check_prizes_threaded); self.check_button.pack(side=tk.RIGHT)
        self.prize_summary_text = tk.Text(frame5, height=4, font=self.prize_summary_font, relief='flat', wrap=tk.WORD, bg=self.style.lookup('TFrame', 'background')); self.prize_summary_text.pack(fill='x', pady=(0, 10))
        self.prize_summary_text.tag_configure("red_bold", foreground="#dc3545", font=self.prize_summary_bold_font)
        self.prize_summary_text.tag_configure("green", foreground="#28a745", font=self.prize_summary_font)
        self.prize_summary_text.tag_configure("normal", foreground="black", font=self.prize_summary_font)
        self.prize_summary_text.tag_configure("blue", foreground="blue", font=self.prize_summary_font)
        self.prize_summary_text.config(state=tk.DISABLED)
        columns = ('line', 'bet', 'stakes', 'status')
        self.results_tree = ttk.Treeview(frame5, columns=columns, show='headings', height=10)
        self.results_tree.heading('line', text='原行号'); self.results_tree.column('line', width=80, anchor='center')
        self.results_tree.heading('bet', text='投注号码'); self.results_tree.column('bet', width=450)
        self.results_tree.heading('stakes', text='投注注数'); self.results_tree.column('stakes', width=100, anchor='center')
        self.results_tree.heading('status', text='结果'); self.results_tree.column('status', width=120, anchor='center')
        self.results_tree.pack(fill='x', expand=True, pady=5); self.results_tree.tag_configure('hit', background='#dff0d8', font=self.bold_font, foreground='red')
        self.results_tree.tag_configure('error', background='#f2dede')

    ### [V3.7 新增] 增加未来期号的功能 ###
    def add_future_draw(self):
        current_values = list(self.draw_id_combo['values'])
        if not current_values:
            messagebox.showwarning("提示", "请先刷新获得有效的期号列表。")
            return
        
        try:
            latest_id = int(current_values[0])
            new_id = str(latest_id + 1)
            
            # 防止重复添加
            if new_id in current_values:
                self.draw_id_combo.set(new_id)
                self.fetch_data_threaded()
                return

            new_list = [new_id] + current_values
            self.draw_id_combo['values'] = new_list
            self.draw_id_combo.set(new_id)
            self.fetch_data_threaded() # 自动获取新期号信息
        except (ValueError, IndexError):
            messagebox.showerror("错误", "无法根据当前列表推算下一期号，请确保列表包含有效的数字期号。")

    def manual_check_mode(self):
        """手工兑奖模式 - 清空期号，直接进入手工输入状态"""
        # 清空期号
        self.draw_id_combo.set("")
        
        # 清空相关显示
        self.draw_time_label.config(text="")
        self.prize_info_label.config(text="")  # 清空奖金信息
        self.match_details_text.config(state=tk.NORMAL)
        self.match_details_text.delete('1.0', tk.END)
        self.match_details_text.config(state=tk.DISABLED)
        
        # 清空开奖信息显示
        self.prize_summary_text.config(state=tk.NORMAL)
        self.prize_summary_text.delete('1.0', tk.END)
        self.prize_summary_text.config(state=tk.DISABLED)
        if self.results_tree.get_children():
            self.results_tree.delete(*self.results_tree.get_children())
        
        # 设置手工输入状态
        config = GAME_CONFIG[self.current_game_type.get()]
        self.status_label.config(text="手工兑奖模式 - 请手动输入开奖号码", foreground="orange")
        self.official_numbers_var.set("") # 清空内容，方便用户输入
        self.official_numbers_entry.config(state='normal') # 允许编辑
        self.user_bets_label.config(text=f"粘贴投注号码(每行一票)，或从文件导入:\n{config['placeholder']}")
        
        # 启用对奖相关控件
        self.check_button.config(state=tk.NORMAL)
        self.import_button.config(state=tk.NORMAL)
        self.user_bets_text.config(state=tk.NORMAL)
        
        messagebox.showinfo("手工兑奖模式", f"已进入手工兑奖模式！\n\n请手动输入开奖号码（{config['result_len']}位数字），然后输入投注号码进行兑奖。")

    def on_main_game_selected(self):
        # 检查是否在手工兑奖模式下
        is_manual_mode = self.status_label.cget("text").startswith("手工兑奖模式")
        
        # 如果在手工兑奖模式下切换玩法，自动退出手工模式并刷新
        if is_manual_mode:
            # 退出手工兑奖模式，恢复正常状态
            config = GAME_CONFIG[self.current_game_type.get()]
            self.status_label.config(text=f"已选 {config['name']}，正获取期号...", foreground="blue")
            self.official_numbers_var.set("")
            self.official_numbers_entry.config(state='readonly')
            
            # 清空开奖数据，准备重新获取
            self.prize_info_label.config(text="")
            self.draw_time_label.config(text="")
            self.match_details_text.config(state=tk.NORMAL)
            self.match_details_text.delete('1.0', tk.END)
            self.match_details_text.config(state=tk.DISABLED)
            
            # 清空对奖结果
            self.prize_summary_text.config(state=tk.NORMAL)
            self.prize_summary_text.delete('1.0', tk.END)
            self.prize_summary_text.config(state=tk.DISABLED)
            if self.results_tree.get_children():
                self.results_tree.delete(*self.results_tree.get_children())
        
        # 正常处理玩法切换
        self.draw_id_combo['values'] = []; self.draw_id_combo.set('')
        config = GAME_CONFIG[self.current_game_type.get()]
        if not is_manual_mode:  # 只有在非手工模式下才显示状态
            self.status_label.config(text=f"已选 {config['name']}，正获取期号...", foreground="blue")
        self.refresh_draw_list_threaded()

    def _execute_in_thread(self, target_func, *args):
        self.fetch_button.config(state=tk.DISABLED); self.refresh_button.config(state=tk.DISABLED)
        ### [V3.7 新增] 禁用增加期号按钮，防止并发操作
        self.add_future_draw_button.config(state=tk.DISABLED)
        threading.Thread(target=target_func, args=args, daemon=True).start()

    def refresh_draw_list_threaded(self):
        if game_type := self.current_game_type.get(): self._execute_in_thread(self._worker_refresh_draw_list, game_type)

    def _worker_refresh_draw_list(self, game_type):
        self.root.after(0, self.update_ui, {'status': 'loading'})
        result = get_draw_list_and_default(game_type, 5)
        self.root.after(0, self._process_refresh_result, result)

    def _process_refresh_result(self, result):
        if result['success']: self.draw_id_combo['values'] = result['ids']
        if result.get('default_id'):
            self.draw_id_combo.set(result['default_id']); self.fetch_data_threaded()
        else:
            self.fetch_button.config(state=tk.NORMAL); self.refresh_button.config(state=tk.NORMAL)
            self.add_future_draw_button.config(state=tk.NORMAL) # 别忘了启用回来
            self.status_label.config(text=result.get('message', '期号列表刷新失败！'), foreground="red")

    def fetch_data_threaded(self):
        game_type, draw_id = self.current_game_type.get(), self.draw_id_combo.get().strip()
        if not game_type or not draw_id.isdigit():
            self.status_label.config(text="请选择玩法并选择有效数字期号！", foreground="red"); return
        self.status_label.config(text=f"正在查询第 {draw_id} 期...", foreground="blue")
        self.draw_time_label.config(text=""); self._execute_in_thread(self._worker_fetch_details, game_type, draw_id)

    def _worker_fetch_details(self, game_type, draw_id):
        result = get_draw_details(game_type, draw_id)
        self.root.after(0, self.update_ui, result)

    def update_ui(self, result):
        ### [V3.7 修改] 启用所有按钮
        self.fetch_button.config(state=tk.NORMAL)
        self.refresh_button.config(state=tk.NORMAL)
        self.add_future_draw_button.config(state=tk.NORMAL)
        
        status = result.get('status'); self.prize_info_label.config(text="")
        if self.results_tree.get_children(): self.results_tree.delete(*self.results_tree.get_children())
        self.match_details_text.config(state=tk.NORMAL); self.match_details_text.delete('1.0', tk.END)
        config = GAME_CONFIG[self.current_game_type.get()]

        if matches := result.get('matches', []):
            game_type = self.current_game_type.get()
            for match in matches:
                if game_type == GAME_TYPE_BQC:
                    result_info = f"半:{match.get('czHalfScore','?')} 全:{match.get('czScore','?')} 赛果:{match.get('result', ',')}"
                else:
                    parts = match.get('result', ',').split(','); home, away = (parts[0], parts[1]) if len(parts) > 1 else ('?', '?')
                    result_info = f"主队进球: {home}  客队进球: {away}"
                line = f"场次{match.get('matchNum', '?'):>2}: {match.get('masterTeamName', '主')} vs {match.get('guestTeamName', '客'):<15}\t{result_info}\n"
                self.match_details_text.insert(tk.END, line)
        self.match_details_text.config(state=tk.DISABLED)

        if status == 'drawn':
            self.status_label.config(text=f"第 {result['draw_id']} 期已开奖!", foreground='red')
            self.draw_time_label.config(text=f"开奖: {result.get('draw_time', '')}", foreground='red')
            
            self.prize_info_label.config(text="\n".join(result['prize_info']))
            self.official_numbers_var.set(result['numbers'])
            
            ### [V3.7 修改] 已开奖，输入框设为只读
            self.official_numbers_entry.config(state='readonly')
            self.user_bets_label.config(text=f"粘贴投注号码(每行一票)，或从文件导入:\n{config['placeholder']}")
            self.check_button.config(state=tk.NORMAL); self.import_button.config(state=tk.NORMAL); self.user_bets_text.config(state=tk.NORMAL)
        
        elif status == 'pending':
            self.status_label.config(text=f"第 {result['draw_id']} 期尚未开奖", foreground='green')
            self.draw_time_label.config(text=result.get('message', ''), foreground='green')
            
            ### [V3.7 修改] 未开奖时，允许手动输入和对奖
            self.official_numbers_var.set("") # 清空内容，方便用户输入
            self.official_numbers_entry.config(state='normal') # 允许编辑
            self.user_bets_label.config(text=f"粘贴投注号码(每行一票)，或从文件导入:\n{config['placeholder']}")
            # 启用对奖相关控件
            self.check_button.config(state=tk.NORMAL)
            self.import_button.config(state=tk.NORMAL)
            self.user_bets_text.config(state=tk.NORMAL)
        
        else: # loading, error, not_found
            message = "正在加载..." if status == 'loading' else result.get('message', "发生未知错误")
            self.status_label.config(text=message, foreground='red')
            self.draw_time_label.config(text="")
            
            if status == 'not_found':
                ### [V3.8 修改] 期号不存在时，允许手工输入开奖号码进行兑奖
                self.official_numbers_var.set("") # 清空内容，方便用户输入
                self.official_numbers_entry.config(state='normal') # 允许编辑
                self.user_bets_label.config(text=f"粘贴投注号码(每行一票)，或从文件导入:\n{config['placeholder']}")
                # 启用对奖相关控件
                self.check_button.config(state=tk.NORMAL)
                self.import_button.config(state=tk.NORMAL)
                self.user_bets_text.config(state=tk.NORMAL)
            else:
                ### [V3.7 修改] 其他错误状态下，输入框设为只读
                self.official_numbers_var.set("---")
                self.official_numbers_entry.config(state='readonly')
                self.check_button.config(state=tk.DISABLED); self.import_button.config(state=tk.DISABLED); self.user_bets_text.config(state=tk.DISABLED)

    def check_prizes_threaded(self):
        ### [V3.7 修改] 对用户手动输入的数据进行校验
        official_result = self.official_numbers_var.get().strip()
        config = GAME_CONFIG[self.current_game_type.get()]
        
        # 校验长度和是否为纯数字
        if not official_result.isdigit() or len(official_result) != config['result_len']:
            messagebox.showerror("错误", f"开奖号码格式无效！\n\n- 必须是 {config['result_len']} 位纯数字。\n- 请检查您的手动输入。")
            return

        if not (user_bets_text := self.user_bets_text.get('1.0', tk.END).strip()):
            messagebox.showinfo("提示", "请输入或导入投注号码。"); return
        self.check_button.config(state=tk.DISABLED); self.root.update_idletasks()
        if self.results_tree.get_children(): self.results_tree.delete(*self.results_tree.get_children())
        self.prize_summary_text.config(state=tk.NORMAL); self.prize_summary_text.delete('1.0', tk.END)
        self.prize_summary_text.insert(tk.END, "正在后台计算...", "blue"); self.prize_summary_text.config(state=tk.DISABLED)
        threading.Thread(target=self._perform_prize_check, args=(user_bets_text, official_result, config), daemon=True).start()

    def _perform_prize_check(self, user_bets_text, official_result, config):
        valid_bets, invalid_bets, total_stakes, winning_line_count = [], [], 0, 0
        for i, line in enumerate(user_bets_text.split('\n')):
            if not(bet_raw := line.strip()): continue
            parsed_bet = parse_complex_bet(bet_raw, config['result_len'])
            if parsed_bet is None:
                invalid_bets.append({'line': i + 1, 'bet': bet_raw, 'stakes': 'N/A', 'status': '格式错误'}); continue
            stakes = calculate_stakes(parsed_bet); total_stakes += stakes
            bet_info = {'line': i + 1, 'bet': bet_raw, 'stakes': stakes}
            if check_win(parsed_bet, official_result):
                bet_info['status'] = '中奖'; winning_line_count += 1
            else: bet_info['status'] = '未中奖'
            valid_bets.append(bet_info)
        self.root.after(0, self.update_results_ui, {"total_stakes": total_stakes, "winning_line_count": winning_line_count, "invalid_count": len(invalid_bets), "valid_bets": valid_bets, "invalid_bets": invalid_bets})
    
    def update_results_ui(self, results):
        self.check_button.config(state=tk.NORMAL)
        total_stakes, winning_line_count, invalid_count = results['total_stakes'], results['winning_line_count'], results['invalid_count']
        valid_bets, invalid_bets = results['valid_bets'], results['invalid_bets']
        self.prize_summary_text.config(state=tk.NORMAL); self.prize_summary_text.delete('1.0', tk.END)
        self.prize_summary_text.insert(tk.END, "核对总注数: ", "normal"); self.prize_summary_text.insert(tk.END, f"{total_stakes} 注\n", "normal")
        self.prize_summary_text.insert(tk.END, "中奖票数 (一等奖): ", "normal"); self.prize_summary_text.insert(tk.END, f"{winning_line_count} 票\n", "red_bold" if winning_line_count > 0 else "normal")
        summary_msg = f"\n处理完毕: 共 {total_stakes} 注有效投注。" + (f" 其中 {invalid_count} 票格式不符。" if invalid_count > 0 else "")
        self.prize_summary_text.insert(tk.END, summary_msg, "normal")
        self.prize_summary_text.config(state=tk.DISABLED)
        # 只显示中奖和格式错误的
        for item in valid_bets:
            if item['status'] == '中奖': self.results_tree.insert('', tk.END, values=(item['line'], item['bet'], item['stakes'], item['status']), tags=('hit',))
        for item in invalid_bets: self.results_tree.insert('', tk.END, values=(item['line'], item['bet'], item['stakes'], item['status']), tags=('error',))
        if winning_line_count > 0: messagebox.showinfo("中奖提醒", f"恭喜您！\n\n发现 {winning_line_count} 张中奖彩票！")

    def sort_bets(self):
        """自动排序投注号码"""
        content = self.user_bets_text.get('1.0', tk.END).strip()
        if not content:
            messagebox.showinfo("提示", "请先输入或导入投注号码。")
            return
        
        # 按行分割，去除空行，排序
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if not lines:
            messagebox.showinfo("提示", "没有找到有效的投注号码。")
            return
        
        # 按投注号码字符串排序
        sorted_lines = sorted(lines)
        
        # 更新文本框内容
        self.user_bets_text.delete('1.0', tk.END)
        self.user_bets_text.insert('1.0', '\n'.join(sorted_lines))
        
        messagebox.showinfo("排序完成", f"已对 {len(sorted_lines)} 条投注号码进行排序。")

    def import_from_file(self):
        if not (filepath := filedialog.askopenfilename(title="选择投注文件", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))): return
        try:
            with open(filepath, 'r', encoding='utf-8') as f: self.user_bets_text.delete('1.0', tk.END); self.user_bets_text.insert('1.0', f.read())
        except Exception as e: messagebox.showerror("文件读取失败", f"错误: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LotteryCheckerApp(root)
    root.mainloop()
