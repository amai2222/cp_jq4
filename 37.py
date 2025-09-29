import tkinter as tk
from tkinter import font, scrolledtext, filedialog, ttk, messagebox
import requests
import threading
from functools import reduce
from operator import mul
from itertools import product, combinations

# [新增] 定义所有需要被视为占位符的特殊字符
SPECIAL_CHARS_TO_ASTERISK = {'#', '%', '$', '￥'}

# --- 核心功能 (已修改) ---
def _normalize_sfc_bet_string(bet_string):
    """
    V2.0 核心修改：规范化投注字符串。
    - 自动移除所有空格。
    - 将所有定义的特殊字符 (#%$￥) 统一替换为任九占位符 '*'。
    """
    normalized_string = bet_string.strip().replace(" ", "")
    for char in SPECIAL_CHARS_TO_ASTERISK:
        normalized_string = normalized_string.replace(char, '*')
    return normalized_string

def parse_sfc_bet(bet_string):
    """解析处理14场胜负彩投注，支持复式和 '*' 占位符"""
    # [修改] 首先对输入字符串进行规范化处理
    bet_string = _normalize_sfc_bet_string(bet_string)
    
    parts, i = [], 0
    while i < len(bet_string):
        if bet_string[i] in '310*':
            parts.append(bet_string[i])
            i += 1
        elif bet_string[i] == '(':
            end_index = bet_string.find(')', i)
            if end_index == -1: return None
            content = bet_string[i+1:end_index]
            if not all(c in '310' for c in content): return None
            parts.append("".join(sorted(list(set(content)))))
            i = end_index + 1
        else:
            return None
    return parts if len(parts) == 14 else None

def calculate_stakes_sfc14(parsed_bet):
    if not parsed_bet: return 0
    return reduce(mul, (len(p) for p in parsed_bet), 1)

def calculate_stakes_r9(parsed_bet):
    if not parsed_bet: return 0
    non_star_bets = [p for p in parsed_bet if p != '*']
    if len(non_star_bets) < 9: return 0
    
    total_stakes = 0
    for combo_parts in combinations(non_star_bets, 9):
        total_stakes += reduce(mul, (len(p) for p in combo_parts), 1)
    return total_stakes

# --- API抓取功能 (保持不变) ---
def get_draw_list_and_default(count=5):
    url = "https://webapi.sporttery.cn/gateway/lottery/getFootBallDrawInfoV1.qry?isVerify=1&param=90,0"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        sfc_list = data.get('value', {}).get('sfclist')
        if not data.get('success') or not isinstance(sfc_list, list) or not sfc_list:
             return {'success': False, 'message': 'API未返回任何有效彩期。'}
        return {'success': True, 'ids': sfc_list[:count], 'default_id': sfc_list[0] if sfc_list else None}
    except Exception as e:
        return {'success': False, 'message': f'获取期号时出错: {e}'}

def get_draw_details(draw_id):
    url = f"https://webapi.sporttery.cn/gateway/lottery/getFootBallDrawInfoByDrawNumV1.qry?isVerify=1&lotteryGameNum=90&lotteryDrawNum={draw_id}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10); response.raise_for_status()
        data = response.json()
        if not data.get('success') or not data.get('value'): 
            return {'status': 'not_found', 'message': f"第 {draw_id} 期不存在。"}
        value_data = data['value']
        result = {'matches': value_data.get('matchList', []), 'draw_id': draw_id, 'draw_time': value_data.get('lotteryDrawTime', '未知')}
        winning_numbers = value_data.get('lotteryDrawResult')
        if not winning_numbers:
            result['status'] = 'pending'
            result['message'] = f"销售截止: {value_data.get('lotterySaleEndtime', '未知')}"
            return result
        result.update({'status': 'drawn', 'numbers': winning_numbers.replace(' ', ''), 'prize_info': {}})
        prize_list_all = value_data.get('prizeLevelList', [])
        def parse_prizes(prize_list, target_levels):
            info = []
            for level in target_levels:
                item = next((p for p in prize_list if p.get('prizeLevel') == level), None)
                if item:
                    stake_count, stake_amount_str = item.get('stakeCount', 'N/A'), item.get('stakeAmount', 'N/A')
                    try: formatted_amount = f"{int(float(stake_amount_str.replace(',', ''))):,}"
                    except: formatted_amount = stake_amount_str
                    info.append(f"{level}: {stake_count} 注 每注 {formatted_amount} 元")
            return info
        result['prize_info']['r9'] = parse_prizes(prize_list_all, ['任选9场'])
        result['prize_info']['sfc14'] = parse_prizes(prize_list_all, ['一等奖', '二等奖'])
        return result
    except Exception as e: 
        return {'status': 'error', 'message': f"处理数据时发生错误: {e}"}

class LotteryCheckerApp:
    def __init__(self, root):
        self.root = root
        # V2.4 修正: 更新版本号
        self.root.title("胜负彩复式兑奖器 V2.4 - 支持期号不存在时手工输入 + 自动排序 + 手工兑奖")
        self.root.geometry("1100x850"); self.root.minsize(900, 700)
        self.full_draw_data = None
        self.setup_styles_and_fonts()
        try: from ctypes import windll; windll.shcore.SetProcessDpiAwareness(1)
        except ImportError: pass
        self.setup_scrollable_area()
        self._create_widgets_and_layout()
        self.root.after(100, self.refresh_draw_list_threaded)

    # ... setup_styles_and_fonts 和 setup_scrollable_area 方法保持不变 ...
    def setup_styles_and_fonts(self):
        self.style = ttk.Style(root); self.style.theme_use('clam')
        self.default_font = font.Font(family="Microsoft YaHei UI", size=12)
        self.bold_font = font.Font(family="Microsoft YaHei UI", size=13, weight="bold")
        self.courier_font = font.Font(family="Courier New", size=13)
        self.prize_info_font = font.Font(family="Microsoft YaHei UI", size=14, weight="bold")
        self.official_numbers_font = font.Font(family="Courier New", size=14, weight="bold")
        self.prize_summary_font = font.Font(family="Microsoft YaHei UI", size=14)
        self.prize_summary_bold_font = font.Font(family="Microsoft YaHei UI", size=14, weight="bold")
        self.highlight_font = font.Font(family="Microsoft YaHei UI", size=13, weight="bold")
        self.style.configure('.', font=self.default_font)
        self.style.configure('TLabel', font=self.default_font); self.style.configure('TButton', font=self.default_font)
        self.style.configure('TRadiobutton', font=self.default_font); self.style.configure('TLabelFrame.Label', font=self.bold_font)
        self.style.configure('Treeview.Heading', font=self.bold_font); self.style.configure('Treeview', rowheight=28, font=self.courier_font)
        self.style.configure('Success.TButton', font=self.bold_font, foreground='white', background='#28a745')
        self.style.map('Success.TButton', background=[('active', '#218838')])

    def setup_scrollable_area(self):
        container = ttk.Frame(root); container.pack(fill='both', expand=True)
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, padding="20")
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        scrollable_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(scrollable_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set); canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.root.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def _create_widgets_and_layout(self):
        # 1. 玩法选择
        frame1 = ttk.LabelFrame(self.scrollable_frame, text="1. 选择玩法", padding="10"); frame1.pack(fill='x', pady=5)
        self.game_type_var = tk.StringVar(value="sfc14")
        self.sfc14_radio_button = ttk.Radiobutton(frame1, text="14场胜负", variable=self.game_type_var, value="sfc14", command=self.on_game_type_change)
        self.sfc14_radio_button.pack(side=tk.LEFT, padx=(0, 30))
        self.r9_radio_button = ttk.Radiobutton(frame1, text="任选九场", variable=self.game_type_var, value="r9", command=self.on_game_type_change)
        self.r9_radio_button.pack(side=tk.LEFT)
        # 2. 期号选择
        frame2 = ttk.LabelFrame(self.scrollable_frame, text="2. 选择/输入查询期号", padding="10"); frame2.pack(fill='x', pady=5)
        ttk.Label(frame2, text="选择期号:").pack(side=tk.LEFT, padx=(0, 5))
        self.draw_id_combo = ttk.Combobox(frame2, width=10, font=self.default_font); self.draw_id_combo.pack(side=tk.LEFT, padx=5)
        self.draw_id_combo.bind("<<ComboboxSelected>>", lambda event: self.fetch_data_threaded())
        self.refresh_button = ttk.Button(frame2, text="刷新期号", command=self.refresh_draw_list_threaded); self.refresh_button.pack(side=tk.LEFT, padx=5)
        self.fetch_button = ttk.Button(frame2, text="获取详情", command=self.fetch_data_threaded); self.fetch_button.pack(side=tk.LEFT, padx=5)
        self.manual_button = ttk.Button(frame2, text="手工兑奖", command=self.manual_check_mode); self.manual_button.pack(side=tk.LEFT, padx=5)
        self.draw_time_label = ttk.Label(frame2, text="", font=self.highlight_font); self.draw_time_label.pack(side=tk.LEFT, padx=10)
        self.status_label = ttk.Label(frame2, text="正在初始化...", font=self.highlight_font, foreground="blue"); self.status_label.pack(side=tk.RIGHT, padx=10)
        # 3. 开奖详情
        frame3 = ttk.LabelFrame(self.scrollable_frame, text="3. 开奖详情", padding="10"); frame3.pack(fill='x', pady=5)
        self.prize_info_label = ttk.Label(frame3, text="", font=self.prize_info_font, foreground="red", justify=tk.LEFT)
        self.prize_info_label.pack(anchor='w', pady=(5, 10))
        
        self.official_numbers_label = ttk.Label(frame3, text="官方开奖号码 (14场赛果):")
        self.official_numbers_label.pack(anchor='w')
        self.official_numbers_var = tk.StringVar()
        self.official_numbers_entry = ttk.Entry(frame3, textvariable=self.official_numbers_var, state='readonly', font=self.official_numbers_font)
        self.official_numbers_entry.pack(fill='x', pady=5)
        
        ttk.Label(frame3, text="对阵与赛果:").pack(anchor='w', pady=(5,0))
        self.match_details_text = scrolledtext.ScrolledText(frame3, height=14, font=self.courier_font, wrap=tk.WORD, relief='solid', borderwidth=1)
        self.match_details_text.pack(fill='both', expand=True, pady=(2,5))
        # 4. 投注输入区
        frame4 = ttk.LabelFrame(self.scrollable_frame, text="4. 核对我的投注 (支持复式)", padding="10"); frame4.pack(fill='x', pady=5)
        self.user_bets_label = ttk.Label(frame4, text="", justify=tk.LEFT); self.user_bets_label.pack(anchor='w')
        self.user_bets_text = scrolledtext.ScrolledText(frame4, height=10, font=self.courier_font, wrap=tk.WORD, relief='solid', borderwidth=1); self.user_bets_text.pack(fill='both', expand=True, pady=5)
        button_frame = ttk.Frame(frame4); button_frame.pack(fill='x', pady=(5,0))
        self.import_button = ttk.Button(button_frame, text="从文件导入(.txt)", command=self.import_from_file); self.import_button.pack(side=tk.LEFT)
        self.sort_button = ttk.Button(button_frame, text="自动排序", command=self.sort_bets); self.sort_button.pack(side=tk.LEFT, padx=5)
        self.check_button = ttk.Button(button_frame, text="开始对奖 >>", style='Success.TButton', command=self.check_prizes_threaded); self.check_button.pack(side=tk.RIGHT)
        # 5. 结果显示区
        frame5 = ttk.LabelFrame(self.scrollable_frame, text="5. 对奖结果", padding="10"); frame5.pack(fill='x', pady=5)
        self.prize_summary_text = tk.Text(frame5, height=4, font=self.prize_summary_font, relief='flat', wrap=tk.WORD, bg=self.style.lookup('TFrame', 'background')); self.prize_summary_text.pack(fill='x', pady=5)
        self.prize_summary_text.tag_configure("red_bold", foreground="red", font=self.prize_summary_bold_font); self.prize_summary_text.tag_configure("normal", foreground="black", font=self.prize_summary_font)
        self.prize_summary_text.config(state=tk.DISABLED)
        columns = ('line', 'bet', 'stakes', 'prize1', 'prize2')
        self.results_tree = ttk.Treeview(frame5, columns=columns, show='headings', height=10)
        for col, text, width in [('line','原行号',80), ('bet','投注号码',400), ('stakes','总注数',100), ('prize1','一等奖(注)',120), ('prize2','二等奖(注)',120)]:
            self.results_tree.heading(col, text=text); self.results_tree.column(col, width=width, anchor='center')
        self.results_tree.pack(fill='both', expand=True, pady=5); self.results_tree.tag_configure('hit', background='#dff0d8', font=self.bold_font, foreground='red')

    # ... _execute_in_thread, refresh_draw_list_threaded, fetch_data_threaded, _worker_refresh_draw_list, _worker_fetch_details 保持不变 ...
    def _execute_in_thread(self, target, *args):
        self.fetch_button.config(state=tk.DISABLED); self.refresh_button.config(state=tk.DISABLED)
        threading.Thread(target=target, args=args, daemon=True).start()

    def refresh_draw_list_threaded(self): self._execute_in_thread(self._worker_refresh_draw_list)
    def fetch_data_threaded(self): self._execute_in_thread(self._worker_fetch_details)

    def _worker_refresh_draw_list(self):
        self.root.after(0, lambda: self.status_label.config(text="正在刷新期号..."))
        result = get_draw_list_and_default()
        self.root.after(0, self._process_refresh_result, result)

    def _process_refresh_result(self, result):
        if result['success']:
            self.draw_id_combo['values'] = result['ids']
            if result['default_id']:
                self.draw_id_combo.set(result['default_id']); self.fetch_data_threaded()
        else:
            self.status_label.config(text=result.get('message', '刷新失败！'), foreground='red')
            self.fetch_button.config(state=tk.NORMAL); self.refresh_button.config(state=tk.NORMAL)

    def _worker_fetch_details(self):
        draw_id = self.draw_id_combo.get().strip()
        if not draw_id:
             self.root.after(0, lambda: self.status_label.config(text="请选择或输入期号", foreground="orange"))
             self.root.after(0, lambda: self.fetch_button.config(state=tk.NORMAL))
             self.root.after(0, lambda: self.refresh_button.config(state=tk.NORMAL))
             return
        self.root.after(0, lambda: self.status_label.config(text=f"正查询 {draw_id} 期..."))
        result = get_draw_details(draw_id)
        self.root.after(0, self.update_ui, result)
        
    def update_ui(self, result):
        self.fetch_button.config(state=tk.NORMAL); self.refresh_button.config(state=tk.NORMAL)
        status = result.get('status'); self.full_draw_data = None
        self.prize_info_label.config(text=""); self.draw_time_label.config(text="")
        self.prize_summary_text.config(state=tk.NORMAL); self.prize_summary_text.delete('1.0', tk.END); self.prize_summary_text.config(state=tk.DISABLED)
        self.results_tree.delete(*self.results_tree.get_children())
        self.match_details_text.config(state=tk.NORMAL); self.match_details_text.delete('1.0', tk.END)
        if matches := result.get('matches', []):
            self.match_details_text.config(height=len(matches))
            for m in matches: self.match_details_text.insert(tk.END, f"场次{m.get('matchNum', '?'):>2}: {m.get('masterTeamName', '主')} vs {m.get('guestTeamName', '客'):<20}\t赛果: {m.get('result', '-')}\n")
        self.match_details_text.config(state=tk.DISABLED)

        if status == 'drawn':
            self.full_draw_data = result
            self.status_label.config(text=f"第 {result['draw_id']} 期已开奖!", foreground="red")
            self.draw_time_label.config(text=f"开奖: {result.get('draw_time', '未知')}", foreground="red")
            self.official_numbers_label.config(text="官方开奖号码 (14场赛果):")
            self.official_numbers_var.set(result['numbers'])
            self.official_numbers_entry.config(state='readonly')
            self.user_bets_text.config(state=tk.NORMAL); self.check_button.config(state=tk.NORMAL); self.import_button.config(state=tk.NORMAL)
        elif status == 'pending':
            self.status_label.config(text=f"第 {result['draw_id']} 期尚未开奖", foreground="green")
            self.draw_time_label.config(text=result.get('message', ''), foreground="green")
            self.official_numbers_label.config(text="手动输入开奖号码 (14位赛果，输入后即可对奖):")
            self.official_numbers_var.set("")
            self.official_numbers_entry.config(state='normal')
            self.user_bets_text.config(state=tk.NORMAL); self.check_button.config(state=tk.NORMAL); self.import_button.config(state=tk.NORMAL)
        else: 
            self.status_label.config(text=result.get('message', "出错了"), foreground="red")
            
            if result.get('status') == 'not_found':
                ### [V2.2 修改] 期号不存在时，允许手工输入开奖号码进行兑奖
                self.official_numbers_label.config(text="手动输入开奖号码 (14位赛果，输入后即可对奖):")
                self.official_numbers_var.set("") # 清空内容，方便用户输入
                self.official_numbers_entry.config(state='normal') # 允许编辑
                self.user_bets_text.config(state=tk.NORMAL); self.check_button.config(state=tk.NORMAL); self.import_button.config(state=tk.NORMAL)
            else:
                ### [V2.1 修改] 其他错误状态下，输入框设为只读
                self.official_numbers_label.config(text="官方开奖号码 (14场赛果):")
                self.official_numbers_var.set("查询失败")
                self.official_numbers_entry.config(state='readonly')
                self.user_bets_text.config(state=tk.DISABLED); self.check_button.config(state=tk.DISABLED); self.import_button.config(state=tk.DISABLED)
        
        self.sfc14_radio_button.config(state=tk.NORMAL); self.r9_radio_button.config(state=tk.NORMAL)
        self.on_game_type_change()

    def manual_check_mode(self):
        """手工兑奖模式 - 清空期号，直接进入手工输入状态"""
        # 清空期号
        self.draw_id_combo.set("")
        
        # 清空开奖数据，防止切换玩法时重新显示
        self.full_draw_data = None
        
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
        self.results_tree.delete(*self.results_tree.get_children())
        
        # 设置手工输入状态
        self.status_label.config(text="手工兑奖模式 - 请手动输入开奖号码", foreground="orange")
        self.official_numbers_label.config(text="手动输入开奖号码 (14位赛果，输入后即可对奖):")
        self.official_numbers_var.set("") # 清空内容，方便用户输入
        self.official_numbers_entry.config(state='normal') # 允许编辑
        
        # 启用对奖相关控件
        self.user_bets_text.config(state=tk.NORMAL)
        self.check_button.config(state=tk.NORMAL)
        self.import_button.config(state=tk.NORMAL)
        
        # 更新投注提示（不调用on_game_type_change，避免退出手工模式）
        game_type = self.game_type_var.get()
        if game_type == 'r9':
            self.results_tree.heading('prize1', text='任九奖(注)'); self.results_tree.heading('prize2', text='-')
            placeholder = "例如: 310(31)1***(01)333*\n特殊字符#%$￥将被视为任九占位符 *"
        else:
            self.results_tree.heading('prize1', text='一等奖(注)'); self.results_tree.heading('prize2', text='二等奖(注)')
            placeholder = "例如: 33(10)3110(31)33303"
        self.user_bets_label.config(text=f"粘贴投注号码(每行一票, 支持复式), 或从文件导入:\n{placeholder}")
        
        messagebox.showinfo("手工兑奖模式", "已进入手工兑奖模式！\n\n请手动输入开奖号码（14位赛果，由3、1、0组成），然后输入投注号码进行兑奖。")

    def on_game_type_change(self):
        game_type = self.game_type_var.get()
        
        # 检查是否在手工兑奖模式下
        is_manual_mode = self.status_label.cget("text").startswith("手工兑奖模式")
        
        # 如果在手工兑奖模式下切换玩法，自动退出手工模式并刷新
        if is_manual_mode:
            # 退出手工兑奖模式，恢复正常状态
            self.status_label.config(text=f"已选 {game_type}，正获取期号...", foreground="blue")
            self.official_numbers_label.config(text="官方开奖号码 (14场赛果):")
            self.official_numbers_var.set("")
            self.official_numbers_entry.config(state='readonly')
            
            # 清空开奖数据，准备重新获取
            self.full_draw_data = None
            self.prize_info_label.config(text="")
            self.draw_time_label.config(text="")
            self.match_details_text.config(state=tk.NORMAL)
            self.match_details_text.delete('1.0', tk.END)
            self.match_details_text.config(state=tk.DISABLED)
            
            # 自动刷新期号列表
            self.refresh_draw_list_threaded()
            return
        
        # 正常模式下的处理
        if self.full_draw_data: 
            self.prize_info_label.config(text="\n".join(self.full_draw_data['prize_info'].get(game_type, [])))
        else: 
            self.prize_info_label.config(text="")
            
        if game_type == 'r9':
            self.results_tree.heading('prize1', text='任九奖(注)'); self.results_tree.heading('prize2', text='-')
            placeholder = "例如: 310(31)1***(01)333*\n特殊字符#%$￥将被视为任九占位符 *"
        else:
            self.results_tree.heading('prize1', text='一等奖(注)'); self.results_tree.heading('prize2', text='二等奖(注)')
            placeholder = "例如: 33(10)3110(31)33303"
        self.user_bets_label.config(text=f"粘贴投注号码(每行一票, 支持复式), 或从文件导入:\n{placeholder}")

    def check_prizes_threaded(self):
        # V2.1 修正: 调整校验顺序
        # 1. 先检查用户投注框是否为空
        user_bets_text = self.user_bets_text.get('1.0', tk.END).strip()
        if not user_bets_text:
            messagebox.showinfo("提示", "请输入或导入投注号码。")
            return
            
        # 2. 再检查开奖号码框是否有效
        winning_numbers = self.official_numbers_var.get().strip()
        if len(winning_numbers) != 14 or not all(c in '310' for c in winning_numbers):
            messagebox.showwarning("输入无效", "请输入14位由'3', '1', '0'组成的开奖号码。")
            return
        
        # 3. 如果都通过，则开始对奖
        self.check_button.config(state=tk.DISABLED)
        self.prize_summary_text.config(state=tk.NORMAL); self.prize_summary_text.delete('1.0', tk.END); self.prize_summary_text.insert('1.0', "正在后台计算...", "normal")
        self.prize_summary_text.config(state=tk.DISABLED); self.root.update_idletasks()
        self.results_tree.delete(*self.results_tree.get_children())
        threading.Thread(target=self._perform_prize_check, args=(user_bets_text, winning_numbers, self.game_type_var.get()), daemon=True).start()

    def _perform_prize_check(self, user_bets_text, official_result, game_type):
        winners, total_stakes, prize1, prize2, invalid_count = [], 0, 0, 0, 0
        high_hit, mid_hit = (14, 13) if game_type == 'sfc14' else (9, 9)

        for i, line in enumerate(user_bets_text.split('\n')):
            if not (bet_raw := line.strip()):
                continue
            
            parsed_bet = parse_sfc_bet(bet_raw)

            if not parsed_bet:
                invalid_count += 1
                continue

            # 计算注数
            stakes = calculate_stakes_sfc14(parsed_bet) if game_type == 'sfc14' else calculate_stakes_r9(parsed_bet)
            if stakes == 0 and game_type == 'r9': # 任九场次不足
                invalid_count += 1
                continue
            total_stakes += stakes
            
            line_p1, line_p2 = 0, 0
            
            if game_type == 'r9':
                non_star_indices = [idx for idx, val in enumerate(parsed_bet) if val != '*']
                if len(non_star_indices) >= 9:
                    for combo_indices_tuple in combinations(non_star_indices, 9):
                        bet_parts_for_combo = [parsed_bet[idx] for idx in combo_indices_tuple]
                        for single_combo in product(*bet_parts_for_combo):
                            hit_count = sum(1 for j, choice in enumerate(single_combo) if choice == official_result[combo_indices_tuple[j]])
                            if hit_count == 9:
                                line_p1 += 1
            else: # sfc14
                for combo in product(*[list(p) for p in parsed_bet]):
                    hit_count = sum(1 for j in range(14) if combo[j] == official_result[j])
                    if hit_count == high_hit:
                        line_p1 += 1
                    elif hit_count == mid_hit:
                        line_p2 += 1
            
            if line_p1 > 0 or line_p2 > 0:
                prize1 += line_p1
                prize2 += line_p2
                winners.append({'line_num': i + 1, 'bet_str': bet_raw, 'stakes': stakes, 'prize1': line_p1, 'prize2': line_p2})

        self.root.after(0, self.update_results_ui, {
            "total_stakes": total_stakes, "prize1": prize1, "prize2": prize2, 
            "invalid": invalid_count, "winners": winners
        })

    # ... update_results_ui 和 import_from_file 保持不变 ...
    def update_results_ui(self, results):
        self.check_button.config(state=tk.NORMAL); total_stakes, prize1, prize2, invalid, winners = results.values(); game_type = self.game_type_var.get()
        self.prize_summary_text.config(state=tk.NORMAL); self.prize_summary_text.delete('1.0', tk.END)
        self.prize_summary_text.insert(tk.END, "核对总注数: ", "normal"); self.prize_summary_text.insert(tk.END, f"{total_stakes} 注\n", "normal")
        prize1_label = "任九奖" if game_type == 'r9' else "一等奖"
        self.prize_summary_text.insert(tk.END, f"中 {prize1_label}: ", "normal"); self.prize_summary_text.insert(tk.END, f"{prize1} 注\n", "red_bold")
        if game_type == 'sfc14': self.prize_summary_text.insert(tk.END, "中 二等奖: ", "normal"); self.prize_summary_text.insert(tk.END, f"{prize2} 注\n", "red_bold")
        summary_msg = f"\n处理完毕: 共 {total_stakes} 注有效投注。" + (f" {invalid} 行格式不符或场次不足被忽略。" if invalid > 0 else "")
        self.prize_summary_text.insert(tk.END, summary_msg, "normal"); self.prize_summary_text.config(state=tk.DISABLED)
        for item in winners: self.results_tree.insert('', tk.END, values=(item['line_num'], item['bet_str'], item['stakes'], item['prize1'], item['prize2'] if game_type == 'sfc14' else '-'), tags=('hit',))
        if prize1 > 0 or prize2 > 0:
            msg = f"恭喜您！\n\n共中得 {prize1_label} {prize1} 注" + (f"\n二等奖 {prize2} 注" if game_type == 'sfc14' and prize2 > 0 else "")
            messagebox.showinfo("中奖提醒", msg)

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
        except Exception as e: messagebox.showerror("错误", f"文件读取失败: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LotteryCheckerApp(root)
    root.mainloop()

