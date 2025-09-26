#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
过滤器启动器
提供统一的入口来启动不同的体彩过滤器
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

class FilterLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("体彩过滤器启动器")
        self.root.geometry("600x400")
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
        """设置界面样式"""
        self.style = ttk.Style()
        self.root.configure(bg='#F0F0F0')
        
        # 设置按钮样式
        self.style.configure('Title.TLabel', font=('Microsoft YaHei UI', 16, 'bold'))
        self.style.configure('Subtitle.TLabel', font=('Microsoft YaHei UI', 12))
        self.style.configure('Info.TLabel', font=('Microsoft YaHei UI', 10))
        self.style.configure('Launch.TButton', font=('Microsoft YaHei UI', 12, 'bold'))
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="体彩过滤器启动器", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # 说明文字
        info_label = ttk.Label(main_frame, 
                              text="请选择要启动的体彩过滤器：", 
                              style='Subtitle.TLabel')
        info_label.pack(pady=(0, 20))
        
        # 过滤器选择区域
        filter_frame = ttk.LabelFrame(main_frame, text="过滤器选择", padding="20")
        filter_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 4场进球过滤器
        jqc_frame = ttk.Frame(filter_frame)
        jqc_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(jqc_frame, text="4场进球过滤器", style='Subtitle.TLabel').pack(anchor=tk.W)
        ttk.Label(jqc_frame, 
                 text="数据格式：8位数字，每2位代表1场比赛的主客队进球数\n示例：10303111", 
                 style='Info.TLabel').pack(anchor=tk.W, pady=(5, 0))
        ttk.Button(jqc_frame, text="启动4场进球过滤器", 
                  command=self.launch_jqc_filter, style='Launch.TButton').pack(anchor=tk.W, pady=(10, 0))
        
        # 分隔线
        ttk.Separator(filter_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # 6场半全场过滤器
        half_full_frame = ttk.Frame(filter_frame)
        half_full_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(half_full_frame, text="6场半全场过滤器", style='Subtitle.TLabel').pack(anchor=tk.W)
        ttk.Label(half_full_frame, 
                 text="数据格式：12位数字，每2位代表1场比赛的半全场结果\n示例：3311031100", 
                 style='Info.TLabel').pack(anchor=tk.W, pady=(5, 0))
        ttk.Button(half_full_frame, text="启动6场半全场过滤器", 
                  command=self.launch_half_full_filter, style='Launch.TButton').pack(anchor=tk.W, pady=(10, 0))
        
        # 分隔线
        ttk.Separator(filter_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # 任九过滤器
        r9_frame = ttk.Frame(filter_frame)
        r9_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(r9_frame, text="任九过滤器", style='Subtitle.TLabel').pack(anchor=tk.W)
        ttk.Label(r9_frame, 
                 text="数据格式：14个位置，用特殊符号表示（3=胜，1=平，0=负，*=任选）\n示例：3*103*1*0*3*1*0*", 
                 style='Info.TLabel').pack(anchor=tk.W, pady=(5, 0))
        ttk.Button(r9_frame, text="启动任九过滤器", 
                  command=self.launch_r9_filter, style='Launch.TButton').pack(anchor=tk.W, pady=(10, 0))
        
        # 分隔线
        ttk.Separator(filter_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # 十四场过滤器
        fourteen_frame = ttk.Frame(filter_frame)
        fourteen_frame.pack(fill=tk.X)
        
        ttk.Label(fourteen_frame, text="十四场过滤器", style='Subtitle.TLabel').pack(anchor=tk.W)
        ttk.Label(fourteen_frame, 
                 text="数据格式：14个位置，用数字表示（3=胜，1=平，0=负）\n示例：31031031031031", 
                 style='Info.TLabel').pack(anchor=tk.W, pady=(5, 0))
        ttk.Button(fourteen_frame, text="启动十四场过滤器", 
                  command=self.launch_fourteen_filter, style='Launch.TButton').pack(anchor=tk.W, pady=(10, 0))
        
        # 底部按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(bottom_frame, text="退出", command=self.root.quit).pack(side=tk.RIGHT)
    
    def launch_jqc_filter(self):
        """启动4场进球过滤器"""
        try:
            script_path = "jqc_4game_filter.py"
            if os.path.exists(script_path):
                subprocess.Popen([sys.executable, script_path])
                messagebox.showinfo("成功", "4场进球过滤器已启动")
            else:
                messagebox.showerror("错误", f"找不到文件：{script_path}")
        except Exception as e:
            messagebox.showerror("错误", f"启动失败：{e}")
    
    def launch_half_full_filter(self):
        """启动6场半全场过滤器"""
        try:
            script_path = "6ch_half_full_filter.py"
            if os.path.exists(script_path):
                subprocess.Popen([sys.executable, script_path])
                messagebox.showinfo("成功", "6场半全场过滤器已启动")
            else:
                messagebox.showerror("错误", f"找不到文件：{script_path}")
        except Exception as e:
            messagebox.showerror("错误", f"启动失败：{e}")
    
    def launch_r9_filter(self):
        """启动任九过滤器"""
        try:
            script_path = "r9_filter.py"
            if os.path.exists(script_path):
                subprocess.Popen([sys.executable, script_path])
                messagebox.showinfo("成功", "任九过滤器已启动")
            else:
                messagebox.showerror("错误", f"找不到文件：{script_path}")
        except Exception as e:
            messagebox.showerror("错误", f"启动失败：{e}")
    
    def launch_fourteen_filter(self):
        """启动十四场过滤器"""
        try:
            script_path = "14ch_filter.py"
            if os.path.exists(script_path):
                subprocess.Popen([sys.executable, script_path])
                messagebox.showinfo("成功", "十四场过滤器已启动")
            else:
                messagebox.showerror("错误", f"找不到文件：{script_path}")
        except Exception as e:
            messagebox.showerror("错误", f"启动失败：{e}")
    
    def run(self):
        """运行程序"""
        self.root.mainloop()

if __name__ == "__main__":
    app = FilterLauncher()
    app.run()
