#!/usr/bin/env python3
"""
无减速板情况下的下降减速方法分析
解决下降时如何减速的问题
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Dict, Tuple
import json

@dataclass
class FlightConfiguration:
    """飞行构型"""
    name: str
    CD_base: float           # 基础阻力系数
    CD_induced_factor: float # 诱导阻力系数
    max_speed: float        # 最大允许速度 (kts)
    deployment_time: float  # 展开时间 (seconds)
    fuel_penalty: float     # 燃油消耗增加百分比

class DescentDecelerationAnalyzer:
    """下降减速分析器"""
    
    def __init__(self, aircraft_type: str = 'B738W26'):
        self.aircraft_type = aircraft_type
        self.load_aircraft_data()
        self.load_configuration_data()
    
    def load_aircraft_data(self):
        """加载飞机基本数据"""
        self.aircraft = {
            'mass': 70000,          # kg
            'wing_area': 124.6,     # m²
            'wing_span': 35.8,      # m
            'aspect_ratio': 10.2,   # 展弦比
            'max_thrust': 117000,   # N (单发)
            'engines': 2
        }
    
    def load_configuration_data(self):
        """加载不同构型的阻力数据"""
        self.configurations = {
            'clean': FlightConfiguration(
                name='干净构型',
                CD_base=0.024,
                CD_induced_factor=0.042,
                max_speed=350,
                deployment_time=0,
                fuel_penalty=0
            ),
            'gear_down': FlightConfiguration(
                name='起落架放下',
                CD_base=0.055,          # 大幅增加
                CD_induced_factor=0.042,
                max_speed=250,          # 速度限制
                deployment_time=15,     # 15秒展开
                fuel_penalty=5          # 5%燃油增加
            ),
            'flaps_5': FlightConfiguration(
                name='襟翼5度',
                CD_base=0.032,
                CD_induced_factor=0.050, # 增加诱导阻力
                max_speed=230,
                deployment_time=10,
                fuel_penalty=2
            ),
            'flaps_15': FlightConfiguration(
                name='襟翼15度', 
                CD_base=0.045,
                CD_induced_factor=0.065,
                max_speed=200,
                deployment_time=15,
                fuel_penalty=8
            ),
            'flaps_40': FlightConfiguration(
                name='襟翼40度',
                CD_base=0.080,
                CD_induced_factor=0.090,
                max_speed=162,
                deployment_time=20,
                fuel_penalty=15
            )
        }
    
    def method_1_idle_thrust_descent(self, initial_speed: float, target_speed: float,
                                   altitude: float, descent_rate: float = 1500) -> Dict:
        """方法1：慢车推力下降"""
        
        print(f"🎯 方法1：慢车推力下降")
        print(f"   初始条件：{initial_speed} kts, {altitude} ft")
        
        # 计算慢车推力下的阻力平衡
        rho = self.get_air_density(altitude)
        config = self.configurations['clean']
        
        # 当前阻力
        current_drag = self.calculate_total_drag(altitude, initial_speed, 'clean')
        
        # 慢车推力（约为最大推力的5-8%）
        idle_thrust = 0.06 * self.aircraft['max_thrust'] * self.aircraft['engines']
        
        # 净阻力力（阻力 - 慢车推力）
        net_deceleration_force = current_drag - idle_thrust
        
        # 减速度 (m/s²)
        deceleration = net_deceleration_force / self.aircraft['mass']
        deceleration_kts_per_min = deceleration * 1.944 * 60  # 转换为 kts/min
        
        # 计算减速时间
        speed_reduction = initial_speed - target_speed
        deceleration_time = speed_reduction / abs(deceleration_kts_per_min)  # 分钟
        
        # 计算下降距离
        avg_speed_ms = (initial_speed + target_speed) / 2 * 0.514444
        descent_distance = (descent_rate * deceleration_time * 0.3048) / 60  # 米
        horizontal_distance = avg_speed_ms * deceleration_time * 60  # 米
        
        result = {
            'method': '慢车推力下降',
            'feasible': deceleration_kts_per_min < -2,  # 至少2 kts/min减速
            'deceleration_rate': deceleration_kts_per_min,
            'time_required': deceleration_time,
            'altitude_loss': descent_rate * deceleration_time,
            'distance_required': horizontal_distance / 1852,  # 海里
            'advantages': ['不需要额外构型', '燃油效率高', '操作简单'],
            'disadvantages': ['减速率较慢', '需要较长距离'],
            'recommendation': '适用于早期下降阶段，有充足距离时'
        }
        
        print(f"   减速率：{deceleration_kts_per_min:.1f} kts/min")
        print(f"   所需时间：{deceleration_time:.1f} 分钟")
        print(f"   可行性：{'✅' if result['feasible'] else '❌'}")
        
        return result
    
    def method_2_configuration_changes(self, initial_speed: float, target_speed: float,
                                     altitude: float) -> Dict:
        """方法2：改变飞机构型"""
        
        print(f"\n🎯 方法2：改变飞机构型")
        
        # 测试不同构型的减速效果
        config_results = {}
        
        for config_name, config in self.configurations.items():
            if config_name == 'clean':
                continue
                
            if initial_speed > config.max_speed:
                # 速度太高，不能使用此构型
                config_results[config_name] = {
                    'feasible': False,
                    'reason': f'速度超限 ({initial_speed} > {config.max_speed})'
                }
                continue
            
            # 计算此构型下的阻力
            drag_force = self.calculate_total_drag(altitude, initial_speed, config_name)
            
            # 慢车推力
            idle_thrust = 0.06 * self.aircraft['max_thrust'] * self.aircraft['engines']
            
            # 净减速力
            net_force = drag_force - idle_thrust
            deceleration = net_force / self.aircraft['mass']
            decel_rate = deceleration * 1.944 * 60  # kts/min
            
            # 计算减速时间
            speed_diff = initial_speed - target_speed
            time_required = speed_diff / abs(decel_rate) if decel_rate < 0 else float('inf')
            
            config_results[config_name] = {
                'feasible': decel_rate < -5 and time_required < 10,  # 至少5 kts/min，10分钟内
                'deceleration_rate': decel_rate,
                'time_required': time_required,
                'deployment_time': config.deployment_time,
                'fuel_penalty': config.fuel_penalty,
                'speed_limit': config.max_speed
            }
            
            print(f"   {config.name}:")
            print(f"     减速率：{decel_rate:.1f} kts/min")
            print(f"     所需时间：{time_required:.1f} 分钟")
            print(f"     可行性：{'✅' if config_results[config_name]['feasible'] else '❌'}")
        
        # 找到最佳构型
        feasible_configs = {k: v for k, v in config_results.items() if v['feasible']}
        
        if feasible_configs:
            best_config = min(feasible_configs.items(), 
                            key=lambda x: x[1]['time_required'])
            
            result = {
                'method': '构型改变',
                'best_configuration': best_config[0],
                'all_results': config_results,
                'feasible': True,
                'recommended_sequence': self.get_configuration_sequence(initial_speed, target_speed),
                'advantages': ['减速效果显著', '可控性好', '适用范围广'],
                'disadvantages': ['增加燃油消耗', '有速度限制', '需要时间展开'],
                'recommendation': f'推荐使用{self.configurations[best_config[0]].name}'
            }
        else:
            result = {
                'method': '构型改变',
                'feasible': False,
                'reason': '当前速度下无可用构型',
                'recommendation': '需要先通过其他方法减速'
            }
        
        return result
    
    def method_3_flight_path_angle_increase(self, initial_speed: float, target_speed: float,
                                          altitude: float) -> Dict:
        """方法3：增加下降角度"""
        
        print(f"\n🎯 方法3：增加下降角度（能量管理）")
        
        # 标准下降率 vs 陡峭下降率
        standard_descent_rate = 1500  # ft/min
        steep_descent_rates = [2000, 2500, 3000, 3500]  # ft/min
        
        results = []
        
        for steep_rate in steep_descent_rates:
            # 计算下降角度
            ground_speed = initial_speed * 0.85  # 考虑风的影响，简化为85%
            descent_angle = np.degrees(np.arctan((steep_rate / 60) / (ground_speed * 1.688)))
            
            # 更陡的下降需要更高的迎角来控制速度
            # 这会增加诱导阻力
            alpha_increase = descent_angle * 0.5  # 经验关系
            induced_drag_increase = 1 + (alpha_increase / 10) ** 2
            
            # 计算增加的阻力
            base_drag = self.calculate_total_drag(altitude, initial_speed, 'clean')
            additional_drag = base_drag * (induced_drag_increase - 1)
            
            # 减速效果
            decel_force = additional_drag
            deceleration = decel_force / self.aircraft['mass']
            decel_rate = deceleration * 1.944 * 60  # kts/min
            
            # 可行性检查
            max_descent_angle = 6.0  # 度，乘客舒适性限制
            feasible = descent_angle <= max_descent_angle and decel_rate > 2
            
            results.append({
                'descent_rate': steep_rate,
                'descent_angle': descent_angle,
                'deceleration_rate': decel_rate,
                'feasible': feasible,
                'passenger_comfort': 'good' if descent_angle < 4 else 'acceptable' if descent_angle < 6 else 'poor'
            })
            
            print(f"   下降率 {steep_rate} ft/min:")
            print(f"     下降角：{descent_angle:.1f}°")
            print(f"     减速率：{decel_rate:.1f} kts/min")
            print(f"     可行性：{'✅' if feasible else '❌'}")
        
        # 找到最佳下降率
        feasible_results = [r for r in results if r['feasible']]
        
        if feasible_results:
            best_result = max(feasible_results, key=lambda x: x['deceleration_rate'])
            
            result = {
                'method': '增加下降角度',
                'feasible': True,
                'best_descent_rate': best_result['descent_rate'],
                'best_descent_angle': best_result['descent_angle'],
                'expected_deceleration': best_result['deceleration_rate'],
                'all_results': results,
                'advantages': ['不需要额外构型', '减速效果中等', '操作相对简单'],
                'disadvantages': ['乘客舒适性影响', '下降角度限制', '需要精确控制'],
                'recommendation': f'推荐下降率 {best_result["descent_rate"]} ft/min'
            }
        else:
            result = {
                'method': '增加下降角度',
                'feasible': False,
                'reason': '无法在舒适性限制内实现有效减速',
                'recommendation': '需要结合其他方法'
            }
        
        return result
    
    def method_4_s_turn_technique(self, initial_speed: float, target_speed: float,
                                 altitude: float) -> Dict:
        """方法4：S型转弯技术（增加航程）"""
        
        print(f"\n🎯 方法4：S型转弯技术")
        
        # S转弯参数
        turn_radius = 5  # 海里
        turn_angle = 30  # 度，每次转弯角度
        number_of_turns = 4  # S型需要的转弯次数
        
        # 计算额外航程
        straight_distance = 20  # 假设直线距离，海里
        
        # S转弯增加的距离
        turn_distance = 0
        for i in range(number_of_turns):
            arc_length = 2 * np.pi * turn_radius * (turn_angle / 360)
            turn_distance += arc_length
        
        total_distance = straight_distance + turn_distance
        distance_increase = (total_distance - straight_distance) / straight_distance
        
        # 转弯时的额外阻力（银行角产生的诱导阻力）
        bank_angle = 25  # 度，标准转弯
        load_factor = 1 / np.cos(np.radians(bank_angle))
        induced_drag_multiplier = load_factor ** 2
        
        # 计算减速效果
        base_drag = self.calculate_total_drag(altitude, initial_speed, 'clean')
        additional_drag = base_drag * (induced_drag_multiplier - 1)
        
        # 时间增加效应
        time_increase = distance_increase * 0.3  # 大约30%的时间增加
        effective_deceleration = (initial_speed - target_speed) / (10 * time_increase)  # kts/min
        
        # 可行性评估
        atc_acceptable = distance_increase < 0.5  # ATC通常接受50%以内的航程增加
        fuel_penalty = distance_increase * 8  # 大约8%燃油增加per额外距离比例
        
        result = {
            'method': 'S型转弯技术',
            'feasible': atc_acceptable and fuel_penalty < 20,
            'distance_increase_percent': distance_increase * 100,
            'time_increase_percent': time_increase * 100,
            'fuel_penalty_percent': fuel_penalty,
            'effective_deceleration': effective_deceleration,
            'atc_coordination_required': True,
            'advantages': ['不改变飞机构型', '可精确控制', '逐步减速'],
            'disadvantages': ['需要ATC协调', '增加燃油消耗', '增加飞行时间', '空域限制'],
            'recommendation': '仅在特殊情况下使用，需要ATC许可'
        }
        
        print(f"   航程增加：{distance_increase*100:.1f}%")
        print(f"   燃油损失：{fuel_penalty:.1f}%")
        print(f"   减速效果：{effective_deceleration:.1f} kts/min")
        print(f"   可行性：{'✅' if result['feasible'] else '❌'}")
        
        return result
    
    def method_5_altitude_for_speed_trade(self, initial_speed: float, target_speed: float,
                                        initial_altitude: float) -> Dict:
        """方法5：高度换速度策略"""
        
        print(f"\n🎯 方法5：高度换速度策略")
        
        # 计算需要耗散的动能
        speed_diff_ms = (initial_speed - target_speed) * 0.514444
        kinetic_energy_diff = 0.5 * self.aircraft['mass'] * (
            (initial_speed * 0.514444)**2 - (target_speed * 0.514444)**2
        )
        
        # 将动能转换为势能
        # ΔKE = ΔPE => 需要爬升高度来耗散多余动能
        altitude_gain_needed = kinetic_energy_diff / (self.aircraft['mass'] * 9.81)
        altitude_gain_ft = altitude_gain_needed / 0.3048
        
        # 实际操作：平飞一段时间让阻力自然减速
        level_flight_time = 5  # 分钟
        level_drag = self.calculate_total_drag(initial_altitude, initial_speed, 'clean')
        idle_thrust = 0.06 * self.aircraft['max_thrust'] * self.aircraft['engines']
        
        net_drag = level_drag - idle_thrust
        deceleration = net_drag / self.aircraft['mass']
        natural_decel_rate = deceleration * 1.944 * 60  # kts/min
        
        speed_loss_in_level = abs(natural_decel_rate) * level_flight_time
        remaining_speed_diff = max(0, (initial_speed - target_speed) - speed_loss_in_level)
        
        # 剩余的速度差通过继续下降时的阻力管理
        final_altitude_loss = initial_altitude - 5000  # 假设最终高度
        
        result = {
            'method': '高度换速度策略',
            'feasible': remaining_speed_diff < 30,  # 剩余速度差可接受
            'level_flight_time': level_flight_time,
            'speed_loss_in_level': speed_loss_in_level,
            'natural_decel_rate': natural_decel_rate,
            'remaining_speed_reduction': remaining_speed_diff,
            'theoretical_altitude_gain': altitude_gain_ft,
            'advantages': ['充分利用空气阻力', '燃油效率高', '操作平稳'],
            'disadvantages': ['需要额外时间', '可能不符合ATC要求', '高度损失'],
            'recommendation': '适用于时间充裕的情况'
        }
        
        print(f"   平飞减速率：{natural_decel_rate:.1f} kts/min")
        print(f"   平飞时间：{level_flight_time} 分钟")
        print(f"   平飞减速量：{speed_loss_in_level:.1f} kts")
        print(f"   剩余减速需求：{remaining_speed_diff:.1f} kts")
        print(f"   可行性：{'✅' if result['feasible'] else '❌'}")
        
        return result
    
    def calculate_total_drag(self, altitude: float, speed: float, configuration: str) -> float:
        """计算总阻力"""
        rho = self.get_air_density(altitude)
        config = self.configurations[configuration]
        
        # 速度转换
        speed_ms = speed * 0.514444
        dynamic_pressure = 0.5 * rho * speed_ms**2
        
        # 升力系数（简化）
        weight_n = self.aircraft['mass'] * 9.81
        CL = weight_n / (dynamic_pressure * self.aircraft['wing_area'])
        
        # 总阻力系数
        CD_total = config.CD_base + config.CD_induced_factor * CL**2
        
        # 阻力
        drag = dynamic_pressure * self.aircraft['wing_area'] * CD_total
        
        return drag
    
    def get_air_density(self, altitude: float) -> float:
        """计算空气密度"""
        h = altitude * 0.3048
        if h <= 11000:
            T = 288.15 - 0.0065 * h
            p = 101325 * (T / 288.15) ** 5.256
        else:
            T = 216.65
            p = 22632 * np.exp(-0.0001577 * (h - 11000))
        
        return p / (287.05 * T)
    
    def get_configuration_sequence(self, initial_speed: float, target_speed: float) -> List[str]:
        """获取推荐的构型使用顺序"""
        sequence = []
        
        current_speed = initial_speed
        
        # 根据速度范围推荐构型顺序
        if current_speed > 250:
            sequence.append('先减速到250kts以下')
            
        if target_speed < 230:
            sequence.append('flaps_5')  # 襟翼5度
            
        if target_speed < 200:
            sequence.append('flaps_15')  # 襟翼15度
            
        if target_speed < 180:
            sequence.append('gear_down')  # 起落架
            
        if target_speed < 165:
            sequence.append('flaps_40')  # 全襟翼
            
        return sequence
    
    def comprehensive_analysis(self, initial_speed: float, target_speed: float,
                             altitude: float) -> Dict:
        """综合分析所有方法"""
        
        print(f"🔍 综合分析：{initial_speed} → {target_speed} kts @ {altitude} ft")
        print("=" * 60)
        
        methods = []
        
        # 分析所有方法
        methods.append(self.method_1_idle_thrust_descent(initial_speed, target_speed, altitude))
        methods.append(self.method_2_configuration_changes(initial_speed, target_speed, altitude))
        methods.append(self.method_3_flight_path_angle_increase(initial_speed, target_speed, altitude))
        methods.append(self.method_4_s_turn_technique(initial_speed, target_speed, altitude))
        methods.append(self.method_5_altitude_for_speed_trade(initial_speed, target_speed, altitude))
        
        # 找到可行的方法
        feasible_methods = [m for m in methods if m['feasible']]
        
        # 生成综合建议
        if feasible_methods:
            # 按优先级排序（简化评分）
            def score_method(method):
                score = 0
                if 'idle_thrust' in method['method'].lower():
                    score += 10  # 优先推荐
                if 'configuration' in method['method'].lower():
                    score += 8
                if 'flight_path' in method['method'].lower():
                    score += 6
                if 'altitude' in method['method'].lower():
                    score += 4
                if 's_turn' in method['method'].lower():
                    score += 2
                return score
            
            feasible_methods.sort(key=score_method, reverse=True)
            
            comprehensive_result = {
                'scenario': f'{initial_speed} → {target_speed} kts @ {altitude} ft',
                'feasible': True,
                'total_methods': len(methods),
                'feasible_methods': len(feasible_methods),
                'all_methods': methods,
                'recommended_approach': self.generate_combined_strategy(feasible_methods),
                'best_single_method': feasible_methods[0]['method'],
                'summary': f'发现 {len(feasible_methods)} 种可行方法'
            }
        else:
            comprehensive_result = {
                'scenario': f'{initial_speed} → {target_speed} kts @ {altitude} ft',
                'feasible': False,
                'total_methods': len(methods),
                'feasible_methods': 0,
                'all_methods': methods,
                'recommended_approach': '建议分段减速或重新规划航迹',
                'summary': '当前条件下无直接可行方法'
            }
        
        return comprehensive_result
    
    def generate_combined_strategy(self, feasible_methods: List[Dict]) -> str:
        """生成组合策略"""
        
        strategies = []
        
        # 检查是否有多种方法可以组合
        has_idle_thrust = any('idle_thrust' in m['method'].lower() for m in feasible_methods)
        has_configuration = any('configuration' in m['method'].lower() for m in feasible_methods)
        has_flight_path = any('flight_path' in m['method'].lower() for m in feasible_methods)
        
        if has_idle_thrust and has_configuration:
            strategies.append("推荐组合策略：先使用慢车推力自然减速，再配合构型改变完成目标减速")
        elif has_configuration:
            strategies.append("推荐策略：使用飞机构型改变实现减速")
        elif has_idle_thrust:
            strategies.append("推荐策略：使用慢车推力下降实现缓慢减速")
        elif has_flight_path:
            strategies.append("推荐策略：通过调整下降剖面实现减速")
        else:
            strategies.append("推荐策略：使用可行方法中的最佳选择")
        
        return " | ".join(strategies)

def create_deceleration_comparison_chart(analyzer: DescentDecelerationAnalyzer):
    """创建减速方法比较图表"""
    
    # 测试场景
    scenarios = [
        (300, 250, 25000, "高速巡航减速"),
        (250, 200, 15000, "中速进近减速"), 
        (200, 160, 8000, "最终进近减速"),
        (180, 140, 3000, "着陆准备减速")
    ]
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('无减速板下降减速方法对比分析', fontsize=16)
    
    for idx, (initial_spd, target_spd, alt, scenario_name) in enumerate(scenarios):
        ax = axes[idx//2, idx%2]
        
        # 分析每种方法
        result = analyzer.comprehensive_analysis(initial_spd, target_spd, alt)
        
        methods = result['all_methods']
        method_names = [m['method'] for m in methods]
        feasibility = [1 if m['feasible'] else 0 for m in methods]
        
        # 创建柱状图
        colors = ['green' if f else 'red' for f in feasibility]
        bars = ax.bar(range(len(method_names)), feasibility, color=colors, alpha=0.7)
        
        # 添加标签
        ax.set_title(f'{scenario_name}\n{initial_spd}→{target_spd} kts @ {alt} ft')
        ax.set_ylabel('可行性')
        ax.set_ylim(0, 1.2)
        
        # 旋转x轴标签
        ax.set_xticks(range(len(method_names)))
        ax.set_xticklabels([name.replace('方法', '').replace('：', '') for name in method_names], 
                          rotation=45, ha='right', fontsize=8)
        
        # 添加数值标签
        for bar, feasible in zip(bars, feasibility):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                   '✅' if feasible else '❌', ha='center', va='bottom', fontsize=12)
    
    plt.tight_layout()
    plt.show()

def main():
    """主函数"""
    
    print("🛩️ 无减速板下降减速方法分析")
    print("=" * 60)
    
    # 创建分析器
    analyzer = DescentDecelerationAnalyzer('B738W26')
    
    # 测试典型场景
    test_scenarios = [
        (280, 250, 20000, "巡航下降减速"),
        (250, 180, 10000, "进近减速"),
        (200, 160, 5000, "最终进近减速")
    ]
    
    all_results = {}
    
    for initial_speed, target_speed, altitude, scenario_name in test_scenarios:
        print(f"\n🎯 场景：{scenario_name}")
        print(f"条件：{initial_speed} → {target_speed} kts @ {altitude} ft")
        print("-" * 50)
        
        result = analyzer.comprehensive_analysis(initial_speed, target_speed, altitude)
        all_results[scenario_name] = result
        
        print(f"\n📊 结果摘要：")
        print(f"   可行方法：{result['feasible_methods']}/{result['total_methods']}")
        print(f"   推荐策略：{result['recommended_approach']}")
        
        if result['feasible']:
            print(f"   最佳方法：{result['best_single_method']}")
    
    # 生成比较图表
    print(f"\n📈 生成对比图表...")
    create_deceleration_comparison_chart(analyzer)
    
    # 保存分析结果
    with open('descent_deceleration_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✅ 分析完成！结果已保存到 descent_deceleration_analysis.json")
    
    # 总结建议
    print(f"\n💡 关键结论：")
    print("1. 🎯 慢车推力下降 - 最经济，但减速慢")
    print("2. 🔧 构型改变 - 最有效，但有速度限制")  
    print("3. 📐 增加下降角 - 中等效果，需要精确控制")
    print("4. 🌊 S型转弯 - 特殊情况，需要ATC协调")
    print("5. ⏰ 高度换速度 - 适合时间充裕的情况")
    
    print(f"\n🎯 实用建议：")
    print("• 优先使用慢车推力 + 构型改变的组合")
    print("• 提前规划，避免大幅度减速需求")
    print("• 根据速度范围选择合适的构型")
    print("• 考虑乘客舒适性和ATC要求")

if __name__ == "__main__":
    main()