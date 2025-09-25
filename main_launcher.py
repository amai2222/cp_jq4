"""
足彩缩水工具套件主启动器
提供统一的入口界面，选择不同的缩水工具
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

class ToolLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("足彩缩水工具套件 V1.0")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # 设置窗口居中
        self.center_window()
        
        self._create_widgets()
        self._setup_styles()
    
    def center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _setup_styles(self):
        """设置样式"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 配置样式
        self.style.configure('Title.TLabel', font=('Microsoft YaHei UI', 18, 'bold'))
        self.style.configure('Subtitle.TLabel', font=('Microsoft YaHei UI', 12))
        self.style.configure('Tool.TButton', font=('Microsoft YaHei UI', 11), padding=(20, 10))
        self.style.configure('Info.TLabel', font=('Microsoft YaHei UI', 10), foreground='gray')
        
        # 按钮样式
        self.style.configure('JQC.TButton', foreground='white', background='#007bff')
        self.style.configure('BQC.TButton', foreground='white', background='#28a745')
        self.style.configure('R9.TButton', foreground='white', background='#ffc107')
        self.style.configure('SFC.TButton', foreground='white', background='#dc3545')
        
        self.style.map('JQC.TButton', background=[('active', '#0056b3')])
        self.style.map('BQC.TButton', background=[('active', '#1e7e34')])
        self.style.map('R9.TButton', background=[('active', '#e0a800')])
        self.style.map('SFC.TButton', background=[('active', '#c82333')])
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="足彩缩水工具套件", style='Title.TLabel')
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, text="专业足彩投注缩水解决方案", style='Subtitle.TLabel')
        subtitle_label.pack(pady=(0, 30))
        
        # 工具选择区域
        tools_frame = ttk.LabelFrame(main_frame, text="选择缩水工具", padding="20")
        tools_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 工具按钮网格
        buttons_frame = ttk.Frame(tools_frame)
        buttons_frame.pack(expand=True)
        
        # 进球4场工具
        jqc_frame = ttk.Frame(buttons_frame)
        jqc_frame.grid(row=0, column=0, padx=20, pady=20, sticky='nsew')
        
        jqc_btn = ttk.Button(jqc_frame, text="进球4场\n缩水工具", 
                            command=self.launch_jqc_tool, style='JQC.TButton')
        jqc_btn.pack(fill=tk.BOTH, expand=True)
        
        jqc_info = ttk.Label(jqc_frame, text="支持0-4+球投注\n自动获取期号对阵\n多种过滤条件", 
                           style='Info.TLabel', justify=tk.CENTER)
        jqc_info.pack(pady=(10, 0))
        
        # 半全场工具
        bqc_frame = ttk.Frame(buttons_frame)
        bqc_frame.grid(row=0, column=1, padx=20, pady=20, sticky='nsew')
        
        bqc_btn = ttk.Button(bqc_frame, text="半全场\n缩水工具", 
                            command=self.launch_bqc_tool, style='BQC.TButton')
        bqc_btn.pack(fill=tk.BOTH, expand=True)
        
        bqc_info = ttk.Label(bqc_frame, text="支持9种半全场组合\n智能过滤算法\n旋转矩阵优化", 
                           style='Info.TLabel', justify=tk.CENTER)
        bqc_info.pack(pady=(10, 0))
        
        # 任九工具
        r9_frame = ttk.Frame(buttons_frame)
        r9_frame.grid(row=1, column=0, padx=20, pady=20, sticky='nsew')
        
        r9_btn = ttk.Button(r9_frame, text="任九\n缩水工具", 
                           command=self.launch_r9_tool, style='R9.TButton')
        r9_btn.pack(fill=tk.BOTH, expand=True)
        
        r9_info = ttk.Label(r9_frame, text="支持胆码选择\n高级过滤条件\n保8旋转矩阵", 
                          style='Info.TLabel', justify=tk.CENTER)
        r9_info.pack(pady=(10, 0))
        
        # 14场工具
        sfc_frame = ttk.Frame(buttons_frame)
        sfc_frame.grid(row=1, column=1, padx=20, pady=20, sticky='nsew')
        
        sfc_btn = ttk.Button(sfc_frame, text="14场胜负彩\n缩水工具", 
                            command=self.launch_sfc_tool, style='SFC.TButton')
        sfc_btn.pack(fill=tk.BOTH, expand=True)
        
        sfc_info = ttk.Label(sfc_frame, text="完整14场投注\n多维度过滤\n专业缩水算法", 
                           style='Info.TLabel', justify=tk.CENTER)
        sfc_info.pack(pady=(10, 0))
        
        # 配置网格权重
        buttons_frame.grid_rowconfigure(0, weight=1)
        buttons_frame.grid_rowconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        # 底部信息
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        version_label = ttk.Label(info_frame, text="版本: V1.0 | 支持自动获取数据 | 专业缩水算法", 
                                style='Info.TLabel')
        version_label.pack(side=tk.LEFT)
        
        help_btn = ttk.Button(info_frame, text="使用帮助", command=self.show_help)
        help_btn.pack(side=tk.RIGHT)
    
    def launch_jqc_tool(self):
        """启动进球4场工具"""
        # 优先启动专业版工具
        if os.path.exists("jqc_professional_tool.py"):
            self._launch_tool("jqc_professional_tool.py", "进球彩专业缩水工具")
        else:
            self._launch_tool("jqc_shrink_tool.py", "进球4场缩水工具")
    
    def launch_bqc_tool(self):
        """启动半全场工具"""
        self._launch_tool("bqc_shrink_tool.py", "半全场缩水工具")
    
    def launch_r9_tool(self):
        """启动任九工具"""
        self._launch_tool("r9_shrink_tool.py", "任九缩水工具")
    
    def launch_sfc_tool(self):
        """启动14场工具"""
        self._launch_tool("sfc_shrink_tool.py", "14场胜负彩缩水工具")
    
    def _launch_tool(self, script_name, tool_name):
        """启动指定工具"""
        try:
            # 检查文件是否存在
            if not os.path.exists(script_name):
                messagebox.showerror("错误", f"找不到 {script_name} 文件")
                return
            
            # 启动工具
            subprocess.Popen([sys.executable, script_name])
            messagebox.showinfo("成功", f"{tool_name} 已启动")
            
        except Exception as e:
            messagebox.showerror("错误", f"启动 {tool_name} 失败: {e}")
    
    def show_help(self):
        """显示使用帮助"""
        help_text = """
足彩缩水工具套件使用说明

【功能特点】
• 自动获取最新期号和对阵信息
• 支持多种投注方式选择
• 提供专业缩水过滤算法
• 旋转矩阵进一步优化投注

【使用流程】
1. 选择对应的缩水工具
2. 自动获取期号，选择投注选项
3. 设置过滤条件进行缩水
4. 使用旋转矩阵进一步优化
5. 导出或复制最终结果

【工具说明】
• 进球4场：支持0-4+球投注，适合进球彩
• 半全场：支持9种半全场组合，适合半全场彩
• 任九：支持胆码选择，适合任选九场
• 14场：完整14场投注，适合胜负彩

【注意事项】
• 请确保网络连接正常以获取最新数据
• 过滤条件设置要合理，避免过度缩水
• 旋转矩阵会进一步减少注数，请谨慎使用
• 建议先小规模测试，确认效果后再大量投注

【技术支持】
如有问题请检查网络连接和文件完整性
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("使用帮助")
        help_window.geometry("500x600")
        help_window.resizable(False, False)
        
        # 居中显示
        help_window.update_idletasks()
        x = (help_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (help_window.winfo_screenheight() // 2) - (600 // 2)
        help_window.geometry(f'500x600+{x}+{y}')
        
        # 创建滚动文本框
        text_frame = ttk.Frame(help_window, padding="20")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Microsoft YaHei UI', 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        # 关闭按钮
        close_btn = ttk.Button(help_window, text="关闭", command=help_window.destroy)
        close_btn.pack(pady=10)

def main():
    root = tk.Tk()
    app = ToolLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()
