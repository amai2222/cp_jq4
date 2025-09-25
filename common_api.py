"""
足彩缩水工具通用API模块
提供统一的数据获取、缩水算法和旋转矩阵功能
"""

import requests
import threading
import itertools
import random
import math
from functools import reduce
from operator import mul
from typing import List, Dict, Tuple, Optional, Any
import tkinter as tk
from tkinter import messagebox

class LotteryAPI:
    """足彩API接口类"""
    
    def __init__(self):
        self.base_url = "https://webapi.sporttery.cn/gateway/lottery"
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
    def get_draw_list(self, game_type: str, count: int = 10) -> Dict[str, Any]:
        """获取期号列表"""
        game_config = {
            'jqc': {'api_num': '94', 'list_key': 'jqclist'},
            'bqc': {'api_num': '98', 'list_key': 'bqclist'}, 
            'sfc': {'api_num': '90', 'list_key': 'sfclist'},
            'r9': {'api_num': '90', 'list_key': 'sfclist'}
        }
        
        if game_type not in game_config:
            return {'success': False, 'message': f'不支持的玩法类型: {game_type}'}
            
        config = game_config[game_type]
        url = f"{self.base_url}/getFootBallDrawInfoV1.qry?isVerify=1&param=94,0;90,0;98,0"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            draw_list = data.get('value', {}).get(config['list_key'], [])
            if not data.get('success') or not isinstance(draw_list, list):
                return {'success': False, 'message': 'API返回数据格式错误'}
                
            return {
                'success': True,
                'ids': draw_list[:count],
                'default_id': draw_list[0] if draw_list else None
            }
        except Exception as e:
            return {'success': False, 'message': f'获取期号失败: {e}'}
    
    def get_draw_details(self, game_type: str, draw_id: str) -> Dict[str, Any]:
        """获取开奖详情"""
        game_config = {
            'jqc': '94', 'bqc': '98', 'sfc': '90', 'r9': '90'
        }
        
        api_num = game_config.get(game_type, '90')
        url = f"{self.base_url}/getFootBallDrawInfoByDrawNumV1.qry?isVerify=1&lotteryGameNum={api_num}&lotteryDrawNum={draw_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success') or not data.get('value'):
                return {'status': 'error', 'message': f'第 {draw_id} 期数据获取失败'}
                
            value_data = data['value']
            result = {
                'draw_id': draw_id,
                'draw_time': value_data.get('lotteryDrawTime', '未知'),
                'matches': value_data.get('matchList', []),
                'status': 'pending'
            }
            
            # 检查是否已开奖
            winning_numbers = value_data.get('lotteryDrawResult')
            if winning_numbers:
                result.update({
                    'status': 'drawn',
                    'numbers': winning_numbers.replace(' ', ''),
                    'prize_info': self._parse_prize_info(value_data.get('prizeLevelList', []))
                })
            else:
                result['message'] = f"销售截止: {value_data.get('lotterySaleEndtime', '未知')}"
                
            return result
        except Exception as e:
            return {'status': 'error', 'message': f'获取详情失败: {e}'}
    
    def _parse_prize_info(self, prize_list: List[Dict]) -> List[str]:
        """解析奖金信息"""
        info = []
        for item in prize_list:
            level = item.get('prizeLevel', '')
            count = item.get('stakeCount', 'N/A')
            amount = item.get('stakeAmount', 'N/A')
            try:
                formatted_amount = f"{int(float(amount.replace(',', ''))):,}"
            except:
                formatted_amount = amount
            info.append(f"{level}: {count} 注, 每注 {formatted_amount} 元")
        return info

class ShrinkAlgorithm:
    """缩水算法类"""
    
    @staticmethod
    def parse_bet_string(bet_string: str, game_type: str) -> Optional[List[str]]:
        """解析投注字符串"""
        bet_string = bet_string.strip().replace(" ", "")
        parts = []
        i = 0
        
        while i < len(bet_string):
            if bet_string[i] in '310*':
                parts.append(bet_string[i])
                i += 1
            elif bet_string[i] == '(':
                end_index = bet_string.find(')', i)
                if end_index == -1:
                    return None
                content = bet_string[i+1:end_index]
                if not all(c in '310' for c in content):
                    return None
                parts.append("".join(sorted(list(set(content)))))
                i = end_index + 1
            else:
                return None
        
        # 验证长度
        expected_lengths = {'jqc': 8, 'bqc': 12, 'sfc': 14, 'r9': 14}
        expected_len = expected_lengths.get(game_type, 14)
        return parts if len(parts) == expected_len else None
    
    @staticmethod
    def calculate_stakes(parsed_bet: List[str], game_type: str) -> int:
        """计算注数"""
        if not parsed_bet:
            return 0
            
        if game_type == 'r9':
            # 任九特殊计算
            non_star_bets = [p for p in parsed_bet if p != '*']
            if len(non_star_bets) < 9:
                return 0
            total_stakes = 0
            for combo_parts in itertools.combinations(non_star_bets, 9):
                total_stakes += reduce(mul, (len(p) for p in combo_parts), 1)
            return total_stakes
        else:
            # 其他玩法直接计算
            return reduce(mul, (len(p) for p in parsed_bet), 1)
    
    @staticmethod
    def apply_filters(bets: List[str], filters: Dict[str, Any]) -> List[str]:
        """应用过滤条件"""
        if not filters:
            return bets
            
        filtered_bets = []
        for bet in bets:
            if ShrinkAlgorithm._check_filter_conditions(bet, filters):
                filtered_bets.append(bet)
        return filtered_bets
    
    @staticmethod
    def _check_filter_conditions(bet: str, filters: Dict[str, Any]) -> bool:
        """检查过滤条件"""
        # 胜平负统计
        win_count = bet.count('3')
        draw_count = bet.count('1') 
        lose_count = bet.count('0')
        
        # 积分和
        total_points = win_count * 3 + draw_count * 1
        
        # 断点数
        breaks = sum(1 for i in range(len(bet) - 1) if bet[i] != bet[i+1])
        
        # 检查条件
        if 'min_wins' in filters and win_count < filters['min_wins']:
            return False
        if 'max_wins' in filters and win_count > filters['max_wins']:
            return False
        if 'min_draws' in filters and draw_count < filters['min_draws']:
            return False
        if 'max_draws' in filters and draw_count > filters['max_draws']:
            return False
        if 'min_loses' in filters and lose_count < filters['min_loses']:
            return False
        if 'max_loses' in filters and lose_count > filters['max_loses']:
            return False
        if 'min_points' in filters and total_points < filters['min_points']:
            return False
        if 'max_points' in filters and total_points > filters['max_points']:
            return False
        if 'min_breaks' in filters and breaks < filters['min_breaks']:
            return False
        if 'max_breaks' in filters and breaks > filters['max_breaks']:
            return False
            
        return True

class WheelMatrix:
    """旋转矩阵类"""
    
    @staticmethod
    def wheel_guarantee_8(bets: List[str], game_type: str) -> List[str]:
        """保8旋转矩阵"""
        if not bets:
            return []
            
        if game_type == 'r9':
            return WheelMatrix._wheel_r9_guarantee_8(bets)
        else:
            return WheelMatrix._wheel_standard_guarantee_8(bets)
    
    @staticmethod
    def _wheel_r9_guarantee_8(bets: List[str]) -> List[str]:
        """任九保8旋转"""
        tickets_to_cover = set(bets)
        wheeled_tickets = []
        
        while tickets_to_cover:
            best_ticket, max_coverage = None, -1
            # 随机采样避免计算量过大
            sample_size = min(len(tickets_to_cover), 100)
            potential_best = random.sample(list(tickets_to_cover), sample_size)
            
            for ticket in potential_best:
                neighbors = WheelMatrix._get_8_of_9_neighbors(ticket)
                neighbors.add(ticket)
                coverage = len(tickets_to_cover.intersection(neighbors))
                if coverage > max_coverage:
                    max_coverage, best_ticket = coverage, ticket
            
            if best_ticket is None:
                best_ticket = tickets_to_cover.pop()
                
            wheeled_tickets.append(best_ticket)
            neighbors_of_best = WheelMatrix._get_8_of_9_neighbors(best_ticket)
            neighbors_of_best.add(best_ticket)
            tickets_to_cover -= neighbors_of_best
            
        return wheeled_tickets
    
    @staticmethod
    def _wheel_standard_guarantee_8(bets: List[str]) -> List[str]:
        """标准保8旋转"""
        if len(bets) <= 8:
            return bets
            
        # 使用数学方法进行保8旋转
        wheeled_bets = []
        remaining_bets = set(bets)
        
        while remaining_bets:
            # 选择第一个票作为基准
            base_ticket = remaining_bets.pop()
            wheeled_bets.append(base_ticket)
            
            # 移除与基准票相差不超过1个位置的票
            to_remove = set()
            for ticket in remaining_bets:
                if WheelMatrix._hamming_distance(base_ticket, ticket) <= 1:
                    to_remove.add(ticket)
            remaining_bets -= to_remove
            
        return wheeled_bets
    
    @staticmethod
    def _get_8_of_9_neighbors(r9_ticket: str) -> set:
        """获取任九票的8个邻居"""
        neighbors = set()
        indices = [i for i, char in enumerate(r9_ticket) if char != '*']
        options = ['3', '1', '0']
        
        for i in indices:
            original_char = r9_ticket[i]
            for new_char in options:
                if new_char != original_char:
                    neighbor_list = list(r9_ticket)
                    neighbor_list[i] = new_char
                    neighbors.add("".join(neighbor_list))
        return neighbors
    
    @staticmethod
    def _hamming_distance(s1: str, s2: str) -> int:
        """计算汉明距离"""
        if len(s1) != len(s2):
            return float('inf')
        return sum(c1 != c2 for c1, c2 in zip(s1, s2))

class ThreadManager:
    """线程管理器"""
    
    @staticmethod
    def run_in_thread(target_func, *args, **kwargs):
        """在后台线程中运行函数"""
        def wrapper():
            try:
                target_func(*args, **kwargs)
            except Exception as e:
                print(f"线程执行错误: {e}")
        
        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()
        return thread

class UIHelper:
    """UI辅助类"""
    
    @staticmethod
    def show_progress(parent, message: str):
        """显示进度信息"""
        if hasattr(parent, 'status_label'):
            parent.status_label.config(text=message)
        if hasattr(parent, 'progress_bar'):
            parent.progress_bar.config(mode='indeterminate')
            parent.progress_bar.start()
    
    @staticmethod
    def hide_progress(parent):
        """隐藏进度信息"""
        if hasattr(parent, 'progress_bar'):
            parent.progress_bar.stop()
            parent.progress_bar.config(mode='determinate', value=0)
    
    @staticmethod
    def show_error(parent, title: str, message: str):
        """显示错误信息"""
        messagebox.showerror(title, message)
    
    @staticmethod
    def show_info(parent, title: str, message: str):
        """显示信息"""
        messagebox.showinfo(title, message)
