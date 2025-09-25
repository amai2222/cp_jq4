"""
简化的进球彩测试工具
"""

import tkinter as tk
from tkinter import ttk, messagebox
import itertools

class SimpleJQCTest:
    def __init__(self, root):
        self.root = root
        self.root.title("进球彩测试工具")
        self.root.geometry("1000x700")
        
        # 进球选择变量 - 每场主队和客队各4个选项(0,1,2,3+)
        self.goal_vars = [[[tk.BooleanVar() for _ in range(4)] for _ in range(2)] for _ in range(8)]
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 对阵表格
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 表头
        headers = ["场次", "联赛", "开赛日期", "主队 VS 客队", "主/客", "0", "1", "2", "3+"]
        for col, header in enumerate(headers):
            ttk.Label(table_frame, text=header, font=('Microsoft YaHei UI', 10, 'bold')).grid(row=0, column=col, padx=3, pady=3, sticky='ew')
        
        # 对阵数据
        match_data = [
            ("1", "欧罗巴", "2025-09-26", "里尔 VS 布兰"),
            ("2", "欧罗巴", "2025-09-26", "维拉 VS 博洛尼"),
            ("3", "欧罗巴", "2025-09-26", "斯图加 VS 塞尔塔"),
            ("4", "欧罗巴", "2025-09-26", "乌德勒 VS 里昂")
        ]
        
        for i in range(8):
            # 场次号
            if i < len(match_data):
                ttk.Label(table_frame, text=match_data[i][0]).grid(row=i*2+1, column=0, padx=3, pady=3, rowspan=2)
                # 联赛
                ttk.Label(table_frame, text=match_data[i][1]).grid(row=i*2+1, column=1, padx=3, pady=3, rowspan=2)
                # 开赛日期
                ttk.Label(table_frame, text=match_data[i][2]).grid(row=i*2+1, column=2, padx=3, pady=3, rowspan=2)
                # 对阵信息
                ttk.Label(table_frame, text=match_data[i][3]).grid(row=i*2+1, column=3, padx=3, pady=3, rowspan=2)
            else:
                ttk.Label(table_frame, text=f"{i+1}").grid(row=i*2+1, column=0, padx=3, pady=3, rowspan=2)
                ttk.Label(table_frame, text="欧罗巴").grid(row=i*2+1, column=1, padx=3, pady=3, rowspan=2)
                ttk.Label(table_frame, text="2025-09-26").grid(row=i*2+1, column=2, padx=3, pady=3, rowspan=2)
                ttk.Label(table_frame, text=f"第{i+1}场对阵").grid(row=i*2+1, column=3, padx=3, pady=3, rowspan=2)
            
            # 主队进球选择
            ttk.Label(table_frame, text="主").grid(row=i*2+1, column=4, padx=3, pady=3)
            for j in range(4):
                goal_text = "3+" if j == 3 else str(j)
                ttk.Checkbutton(table_frame, text=goal_text, variable=self.goal_vars[i][0][j]).grid(
                    row=i*2+1, column=5+j, padx=3, pady=3)
            
            # 客队进球选择
            ttk.Label(table_frame, text="客").grid(row=i*2+2, column=4, padx=3, pady=3)
            for j in range(4):
                goal_text = "3+" if j == 3 else str(j)
                ttk.Checkbutton(table_frame, text=goal_text, variable=self.goal_vars[i][1][j]).grid(
                    row=i*2+2, column=5+j, padx=3, pady=3)
        
        # 配置列权重
        for i in range(9):
            table_frame.grid_columnconfigure(i, weight=1)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="计算投注", command=self.calculate_bets).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空选择", command=self.clear_selections).pack(side=tk.LEFT, padx=5)
        
        # 结果显示
        result_frame = ttk.Frame(main_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        ttk.Label(result_frame, text="投注结果:", font=('Microsoft YaHei UI', 10, 'bold')).pack(anchor='w')
        
        # 结果表格
        columns = ('注号', '投注结果')
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=15)
        
        self.result_tree.heading('注号', text='注号')
        self.result_tree.heading('投注结果', text='投注结果')
        
        self.result_tree.column('注号', width=80, anchor='center')
        self.result_tree.column('投注结果', width=200, anchor='center')
        
        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def clear_selections(self):
        """清空所有选择"""
        for i in range(8):
            for j in range(2):
                for k in range(4):
                    self.goal_vars[i][j][k].set(False)
        
        # 清空结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
    
    def calculate_bets(self):
        """计算投注组合"""
        # 检查输入 - 每场主队和客队都必须至少选择一个进球数
        selected_matches = []
        for i in range(8):
            home_options = []
            away_options = []
            
            # 检查主队选择
            for j in range(4):
                if self.goal_vars[i][0][j].get():
                    home_options.append(j)
            
            # 检查客队选择
            for j in range(4):
                if self.goal_vars[i][1][j].get():
                    away_options.append(j)
            
            if not home_options:
                messagebox.showerror("错误", f"第{i+1}场主队必须至少选择一个进球数")
                return
            
            if not away_options:
                messagebox.showerror("错误", f"第{i+1}场客队必须至少选择一个进球数")
                return
            
            # 进球彩是8场，每场主队和客队各选一个进球数
            # 所以每场有 home_options × away_options 种组合
            match_combos = []
            for h in home_options:
                for a in away_options:
                    match_combos.append((h, a))
            
            selected_matches.append(match_combos)
        
        # 生成所有组合
        bets = []
        for combo in itertools.product(*selected_matches):
            # 将每场的(主队进球, 客队进球)转换为8位数字串
            bet_str = ''.join([f"{h}{a}" for h, a in combo])
            bets.append(bet_str)
        
        # 清空现有结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 显示结果
        for i, bet in enumerate(bets, 1):
            self.result_tree.insert('', tk.END, values=(i, bet))
        
        messagebox.showinfo("完成", f"投注计算完成，共 {len(bets)} 注")

def main():
    root = tk.Tk()
    app = SimpleJQCTest(root)
    root.mainloop()

if __name__ == "__main__":
    main()


