import tkinter as tk
from tkinter import ttk, font, messagebox
import requests
import threading
import json
import time

# 脚本主类
class OddsParserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("500.com 欧赔解析器 (v5.0 路径修正终版)")
        self.root.geometry("950x600")

        # --- 字体和样式 ---
        self.default_font = font.Font(family="Microsoft YaHei UI", size=10)
        self.bold_font = font.Font(family="Microsoft YaHei UI", size=11, weight="bold")
        style = ttk.Style(root)
        style.configure("Treeview", rowheight=25, font=self.default_font)
        style.configure("Treeview.Heading", font=self.bold_font)

        # --- 创建界面布局 ---
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. 顶部控制区域
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(control_frame, text="比赛ID:", font=self.bold_font).pack(side=tk.LEFT, padx=(0, 5))
        self.id_entry = ttk.Entry(control_frame, font=self.default_font, width=20)
        self.id_entry.pack(side=tk.LEFT, padx=5)
        self.id_entry.insert(0, "1278736")

        self.fetch_button = ttk.Button(control_frame, text="  解 析 赔 率  ", command=self.start_fetch_data)
        self.fetch_button.pack(side=tk.LEFT, padx=10)

        self.chupan_var = tk.IntVar(value=0)
        self.chupan_check = ttk.Checkbutton(control_frame, text="仅显示有初盘的公司", variable=self.chupan_var)
        self.chupan_check.pack(side=tk.LEFT, padx=15)

        # 2. 中间数据展示区域 (表格)
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.tree = self._create_treeview(tree_frame)

        # 3. 底部状态栏
        self.status_label = ttk.Label(main_frame, text="请输入比赛ID后点击解析", font=self.default_font, anchor='w')
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

    def _create_treeview(self, parent):
        columns = {'company': ('公司', 120, 'w'), 'init_w': ('初盘-胜', 80, 'center'), 'init_d': ('初盘-平', 80, 'center'), 'init_l': ('初盘-负', 80, 'center'), 'live_w': ('即时-胜', 80, 'center'), 'live_d': ('即时-平', 80, 'center'), 'live_l': ('即时-负', 80, 'center')}
        tree = ttk.Treeview(parent, columns=list(columns.keys()), show='headings')
        for col, (text, width, anchor) in columns.items():
            tree.heading(col, text=text)
            tree.column(col, width=width, anchor=anchor, stretch=True)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return tree

    def start_fetch_data(self):
        match_id = self.id_entry.get().strip()
        if not match_id.isdigit():
            messagebox.showerror("输入错误", "比赛ID必须是纯数字！")
            return
        self.update_status(f"正在加载比赛ID: {match_id} 的数据...", "blue")
        self.fetch_button.config(state="disabled")
        self.clear_tree()
        threading.Thread(target=self._worker_fetch, args=(match_id,), daemon=True).start()

    def _worker_fetch(self, match_id):
        print("\n" + "="*50)
        print("开始新的解析任务 (v5.0 策略)...")
        
        timestamp = int(time.time() * 1000)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Referer': f'https://odds.500.com/fenxi/ouzhi-{match_id}.shtml',
            'X-Requested-With': 'XMLHttpRequest'
        }
        cookies = {
            'ck_rate_name_S': 'bocai'
        }
        
        # --- 核心修正: 将 URL 中的 "fenxi1" 改为 "fenxi" ---
        base_url = f"https://odds.500.com/fenxi/ouzhi.php?id={match_id}&ctype=1&start=0&end=500&r=1"
        
        if self.chupan_var.get() == 1:
            api_url = f"{base_url}&chupan=1&_={timestamp}"
        else:
            api_url = f"{base_url}&_={timestamp}"

        print(f"[调试] 目标API URL: {api_url}")
        print(f"[调试] 携带的Headers: {headers}")
        print(f"[调试] 伪造的Cookies: {cookies}")

        try:
            response = requests.get(
                api_url, 
                headers=headers, 
                cookies=cookies,
                timeout=15
            )
            response.raise_for_status()
            print(f"[调试] API响应状态码: {response.status_code}")

            response.encoding = 'gbk'
            print("[调试] 开始解析返回的数据...")
            
            # 检查返回的是否是期望的JS变量格式
            if not response.text.strip().startswith('var ou='):
                raise json.JSONDecodeError("返回内容不是预期的JS变量格式", response.text, 0)

            clean_text = response.text.replace("var ou=", "").strip().rstrip(';')
            
            data = json.loads(clean_text)
            print("[调试] 数据解析成功！准备更新界面。")
            self.root.after(0, self.populate_tree, data)

        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {e}"
            print(f"[调试] 错误: {error_msg}")
            self.root.after(0, self.update_status, error_msg, "red")
        except json.JSONDecodeError as e:
            error_msg = "加载失败: 服务器返回数据格式错误，可能被反爬机制拦截。"
            print(f"[调试] 错误: JSON解析失败 - {e}")
            self.root.after(0, self.update_status, error_msg, "red")
            print("="*20 + "【 失败详情 】" + "="*20)
            print(f"失败的API URL: {api_url}")
            print(f"服务器返回的原始文本(前300字符): \n---\n{response.text[:300]}\n---")
            print("="*54)
        finally:
            print("任务结束。")
            print("="*50 + "\n")
            self.root.after(0, lambda: self.fetch_button.config(state="normal"))
            
    def populate_tree(self, odds_data):
        if not odds_data:
            self.update_status("数据加载完成，但该比赛没有赔率数据。", "orange")
            return
        for company_data in odds_data:
            values = (company_data[1], company_data[2], company_data[3], company_data[4], company_data[5], company_data[6], company_data[7])
            self.tree.insert('', 'end', values=values)
        self.update_status(f"加载成功！共获取 {len(odds_data)} 家公司的数据。", "green")

    def clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
    def update_status(self, text, color):
        self.status_label.config(text=text, foreground=color)

if __name__ == "__main__":
    root = tk.Tk()
    app = OddsParserApp(root)
    root.mainloop()
