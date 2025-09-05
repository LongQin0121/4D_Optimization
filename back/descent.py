#!/usr/bin/env python3
"""
襟翼和起落架标准操作程序分析
区分减速板和襟翼的不同用途和时机
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, List, Tuple
import json

@dataclass
class FlightPhase:
    """飞行阶段"""
    name: str
    altitude_range: Tuple[int, int]  # (min, max) feet
    speed_range: Tuple[int, int]     # (min, max) knots
    typical_distance_to_runway: float  # nautical miles
    duration_minutes: float

@dataclass
class ConfigurationSetting:
    """构型设置"""
    name: str
    flap_setting: int           # 襟翼角度
    gear_position: str          # UP/DOWN
    max_speed: int             # 最大允许速度 (knots)
    typical_speed: int         # 典型使用速度 (knots)
    when_to_use: str           # 使用时机
    purpose: str               # 主要目的

class Boeing737FlightProcedures:
    """Boeing 737飞行程序"""
    
    def __init__(self):
        self.aircraft_type = "Boeing 737-800"
        self.load_flight_phases()
        self.load_configuration_standards()
        self.load_speed_limitations()
    
    def load_flight_phases(self):
        """加载飞行阶段定义"""
        self.flight_phases = {
            'cruise': FlightPhase(
                name='巡航',
                altitude_range=(28000, 41000),
                speed_range=(420, 500),
                typical_distance_to_runway=200,
                duration_minutes=120
            ),
            'initial_descent': FlightPhase(
                name='初始下降',
                altitude_range=(18000, 28000),
                speed_range=(350, 420),
                typical_distance_to_runway=80,
                duration_minutes=15
            ),
            'arrival': FlightPhase(
                name='到场下降',
                altitude_range=(10000, 18000),
                speed_range=(280, 350),
                typical_distance_to_runway=40,
                duration_minutes=10
            ),
            'approach': FlightPhase(
                name='进近准备',
                altitude_range=(3000, 10000),
                speed_range=(200, 280),
                typical_distance_to_runway=15,
                duration_minutes=8
            ),
            'final_approach': FlightPhase(
                name='最终进近',
                altitude_range=(200, 3000),
                speed_range=(140, 200),
                typical_distance_to_runway=5,
                duration_minutes=5
            ),
            'landing': FlightPhase(
                name='着陆',
                altitude_range=(0, 200),
                speed_range=(130, 160),
                typical_distance_to_runway=0,
                duration_minutes=2
            )
        }
    
    def load_configuration_standards(self):
        """加载标准构型配置"""
        self.configurations = {
            'clean': ConfigurationSetting(
                name='干净构型',
                flap_setting=0,
                gear_position='UP',
                max_speed=350,
                typical_speed=300,
                when_to_use='巡航和高速下降',
                purpose='最小阻力，最大燃油效率'
            ),
            'flaps_1': ConfigurationSetting(
                name='襟翼1档',
                flap_setting=1,
                gear_position='UP',
                max_speed=230,
                typical_speed=210,
                when_to_use='初始进近配置',
                purpose='增加升力，便于减速'
            ),
            'flaps_5': ConfigurationSetting(
                name='襟翼5度',
                flap_setting=5,
                gear_position='UP',
                max_speed=230,
                typical_speed=200,
                when_to_use='进近初期',
                purpose='进一步增加升力和阻力'
            ),
            'flaps_15': ConfigurationSetting(
                name='襟翼15度',
                flap_setting=15,
                gear_position='UP',
                max_speed=200,
                typical_speed=180,
                when_to_use='中期进近',
                purpose='显著增加升力，准备放起落架'
            ),
            'flaps_15_gear_down': ConfigurationSetting(
                name='襟翼15度+起落架',
                flap_setting=15,
                gear_position='DOWN',
                max_speed=200,
                typical_speed=170,
                when_to_use='最终进近前',
                purpose='大幅增加阻力，稳定进近'
            ),
            'flaps_30_gear_down': ConfigurationSetting(
                name='襟翼30度+起落架',  
                flap_setting=30,
                gear_position='DOWN',
                max_speed=175,
                typical_speed=160,
                when_to_use='最终进近',
                purpose='最大升力，稳定进近角度'
            ),
            'flaps_40_gear_down': ConfigurationSetting(
                name='着陆构型',
                flap_setting=40,
                gear_position='DOWN', 
                max_speed=162,
                typical_speed=145,
                when_to_use='着陆',
                purpose='最大升力，最低失速速度'
            )
        }
        
    def load_speed_limitations(self):
        """加载速度限制"""
        self.speed_limits = {
            'flap_speeds': {
                # VFE - Maximum Flap Extended Speed
                1: 230,   # 襟翼1档最大速度
                5: 230,   # 襟翼5度最大速度
                15: 200,  # 襟翼15度最大速度
                25: 190,  # 襟翼25度最大速度
                30: 175,  # 襟翼30度最大速度
                40: 162   # 襟翼40度最大速度
            },
            'gear_speeds': {
                'VLO': 270,  # Landing gear Operating speed (放下时)
                'VLE': 270   # Landing gear Extended speed (放下后)
            },
            'other_limits': {
                'below_10000ft': 250,  # 10000英尺以下限速
                'approach': 180,       # 典型进近速度
                'final': 150,         # 最终进近速度
                'vref': 138           # 参考着陆速度(典型)
            }
        }
    
    def get_standard_descent_procedure(self) -> Dict:
        """获取标准下降程序"""
        
        procedure = {
            'title': 'Boeing 737-800 标准进近程序',
            'phases': []
        }
        
        # 阶段1：初始下降 (巡航→到场)
        phase1 = {
            'phase': '初始下降',
            'altitude': '35000 → 18000 ft',
            'speed': '420 → 280 kts',
            'configuration': 'Clean (襟翼0, 起落架收起)',
            'descent_rate': '2000-2500 ft/min',
            'typical_distance': '80-60 海里',
            'key_actions': [
                '推力设置慢车',
                '保持干净构型',
                '遵守ATC速度指令',
                '监控下降率'
            ]
        }
        
        # 阶段2：到场下降 (18000→10000)  
        phase2 = {
            'phase': '到场下降',
            'altitude': '18000 → 10000 ft',
            'speed': '280 → 250 kts',
            'configuration': 'Clean → Flaps 1',
            'descent_rate': '1500-2000 ft/min',
            'typical_distance': '40-25 海里',
            'key_actions': [
                '减速到250kts (10000英尺限制)',
                '在适当时机放襟翼1档',
                '开始进近准备',
                '联系进近管制'
            ]
        }
        
        # 阶段3：进近准备 (10000→3000)
        phase3 = {
            'phase': '进近准备', 
            'altitude': '10000 → 3000 ft',
            'speed': '250 → 200 kts',
            'configuration': 'Flaps 1 → Flaps 5 → Flaps 15',
            'descent_rate': '1000-1500 ft/min',
            'typical_distance': '25-8 海里',
            'key_actions': [
                '减速到230kts，放襟翼5度',
                '减速到200kts，放襟翼15度',
                '建立稳定进近',
                '完成进近检查单'
            ]
        }
        
        # 阶段4：最终进近 (3000→着陆)
        phase4 = {
            'phase': '最终进近',
            'altitude': '3000 → 0 ft',
            'speed': '180 → 145 kts',
            'configuration': 'Flaps 15 → Gear Down → Flaps 30/40',
            'descent_rate': '700-1000 ft/min',
            'typical_distance': '8-0 海里',
            'key_actions': [
                '减速到180kts，放下起落架',
                '减速到Vref+5，放襟翼30/40度',
                '建立稳定进近(3度下滑角)',
                '完成着陆检查单'
            ]
        }
        
        procedure['phases'] = [phase1, phase2, phase3, phase4]
        
        return procedure
    
    def analyze_flaps_vs_speedbrakes(self) -> Dict:
        """分析襟翼vs减速板的区别"""
        
        comparison = {
            'title': '襟翼 vs 减速板 - 系统对比',
            'systems': {
                'flaps': {
                    'name': '襟翼 (Flaps)',
                    'primary_purpose': '增加升力',
                    'secondary_purpose': '增加阻力(副作用)',
                    'when_used': '按标准程序，在特定阶段使用',
                    'speed_limits': '有严格的VFE限制',
                    'retraction_rules': '必须按顺序收回',
                    'pilot_discretion': '有限(遵循SOP)',
                    'fuel_impact': '中等(增加阻力)',
                    'passenger_comfort': '无影响',
                    'examples': [
                        '进近时放襟翼5度增加升力',
                        '着陆时放全襟翼降低失速速度',
                        '起飞时使用襟翼缩短滑跑距离'
                    ]
                },
                'speedbrakes': {
                    'name': '减速板/扰流板 (Speed Brakes/Spoilers)',
                    'primary_purpose': '快速减速',
                    'secondary_purpose': '减少升力',
                    'when_used': '飞行员根据需要随时使用',
                    'speed_limits': '相对宽松',
                    'retraction_rules': '可随时收回',
                    'pilot_discretion': '完全自主决定',
                    'fuel_impact': '高(显著增加阻力)',
                    'passenger_comfort': '可能有轻微不适',
                    'examples': [
                        '下降时需要快速减速',
                        '进近时过高过快',
                        '着陆后地面减速'
                    ]
                }
            }
        }
        
        return comparison
    
    def get_configuration_decision_tree(self, current_altitude: int, current_speed: int,
                                      distance_to_runway: float) -> Dict:
        """获取构型决策树"""
        
        recommendations = {
            'current_state': {
                'altitude': current_altitude,
                'speed': current_speed,
                'distance': distance_to_runway
            },
            'analysis': [],
            'recommended_action': '',
            'next_configuration': ''
        }
        
        # 决策逻辑
        if current_altitude > 10000:
            if current_speed > 280:
                recommendations['analysis'].append('高空高速 - 保持干净构型')
                recommendations['recommended_action'] = '继续下降减速'
                recommendations['next_configuration'] = 'clean'
            else:
                recommendations['analysis'].append('高空中速 - 可考虑初期减速')
                recommendations['recommended_action'] = '准备放襟翼1档'
                recommendations['next_configuration'] = 'flaps_1'
                
        elif 3000 < current_altitude <= 10000:
            if current_speed > 250:
                recommendations['analysis'].append('违反10000英尺限速 - 紧急减速')
                recommendations['recommended_action'] = '立即减速到250kts'
                recommendations['next_configuration'] = 'clean'
            elif current_speed > 230:
                recommendations['analysis'].append('中空中速 - 标准程序')
                recommendations['recommended_action'] = '放襟翼1档或5度'
                recommendations['next_configuration'] = 'flaps_1'
            elif current_speed > 200:
                recommendations['analysis'].append('中空低速 - 进近准备')
                recommendations['recommended_action'] = '放襟翼15度'
                recommendations['next_configuration'] = 'flaps_15'
            else:
                recommendations['analysis'].append('速度过低 - 检查构型')
                recommendations['recommended_action'] = '确认当前构型是否合适'
                recommendations['next_configuration'] = 'review'
                
        elif current_altitude <= 3000:
            if distance_to_runway > 8:
                recommendations['analysis'].append('最终进近前 - 准备放起落架')  
                recommendations['recommended_action'] = '检查速度，准备放起落架'
                recommendations['next_configuration'] = 'flaps_15'
            elif distance_to_runway > 5:
                recommendations['analysis'].append('最终进近 - 放起落架')
                recommendations['recommended_action'] = '放下起落架'
                recommendations['next_configuration'] = 'flaps_15_gear_down'
            else:
                recommendations['analysis'].append('短最终 - 着陆构型')
                recommendations['recommended_action'] = '放襟翼30/40度'
                recommendations['next_configuration'] = 'flaps_40_gear_down'
        
        return recommendations
    
    def create_configuration_timeline(self, flight_profile: List[Dict]) -> Dict:
        """创建构型时间线"""
        
        timeline = {
            'title': 'Boeing 737-800 标准构型时间线',
            'events': []
        }
        
        # 标准事件序列
        standard_events = [
            {
                'time_to_landing': 25,  # 分钟
                'altitude': 18000,
                'speed': 280,
                'action': '开始初始进近准备',
                'configuration': 'Clean',
                'notes': '联系进近管制，获取进近许可'
            },
            {
                'time_to_landing': 20,
                'altitude': 12000, 
                'speed': 250,
                'action': '遵守10000英尺限速',
                'configuration': 'Clean',
                'notes': '减速到250kts或更低'
            },
            {
                'time_to_landing': 15,
                'altitude': 8000,
                'speed': 230,
                'action': '放襟翼1档',
                'configuration': 'Flaps 1',
                'notes': '第一次构型改变，开始减速'
            },
            {
                'time_to_landing': 12,
                'altitude': 6000,
                'speed': 200,
                'action': '放襟翼5度',
                'configuration': 'Flaps 5', 
                'notes': '继续减速，准备进近'
            },
            {
                'time_to_landing': 10,
                'altitude': 4000,
                'speed': 180,
                'action': '放襟翼15度',
                'configuration': 'Flaps 15',
                'notes': '进近构型，准备放起落架'
            },
            {
                'time_to_landing': 8,
                'altitude': 2500,
                'speed': 170,
                'action': '放下起落架',
                'configuration': 'Flaps 15 + Gear Down',
                'notes': '建立稳定进近，完成进近检查单'
            },
            {
                'time_to_landing': 5,
                'altitude': 1500,
                'speed': 160,
                'action': '放襟翼30度',
                'configuration': 'Flaps 30 + Gear Down',
                'notes': '最终进近构型'
            },
            {
                'time_to_landing': 3,
                'altitude': 1000,
                'speed': 150,
                'action': '放襟翼40度(可选)',
                'configuration': 'Landing Configuration',
                'notes': '着陆构型，建立稳定进近'
            },
            {
                'time_to_landing': 0,
                'altitude': 50,
                'speed': 145,
                'action': '着陆',
                'configuration': 'Landing Configuration',
                'notes': 'Vref+5速度，保持稳定进近'
            }
        ]
        
        timeline['events'] = standard_events
        
        return timeline

def visualize_configuration_procedures():
    """可视化构型程序"""
    
    procedures = Boeing737FlightProcedures()
    timeline = procedures.create_configuration_timeline([])
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Boeing 737-800 标准构型程序', fontsize=16)
    
    # 提取时间线数据
    events = timeline['events']
    times = [event['time_to_landing'] for event in events]
    altitudes = [event['altitude'] for event in events]
    speeds = [event['speed'] for event in events]
    
    # 1. 高度剖面
    ax1.plot(times, altitudes, 'b-o', linewidth=2, markersize=6)
    ax1.set_xlabel('着陆前时间 (分钟)')
    ax1.set_ylabel('高度 (英尺)')
    ax1.set_title('标准下降剖面')
    ax1.grid(True, alpha=0.3)
    ax1.invert_xaxis()  # 时间倒序
    
    # 添加构型标注
    for i, event in enumerate(events[::2]):  # 每隔一个标注，避免拥挤
        ax1.annotate(event['configuration'], 
                    (event['time_to_landing'], event['altitude']),
                    xytext=(10, 10), textcoords='offset points',
                    fontsize=8, ha='left')
    
    # 2. 速度剖面
    ax2.plot(times, speeds, 'r-o', linewidth=2, markersize=6)
    ax2.set_xlabel('着陆前时间 (分钟)')
    ax2.set_ylabel('速度 (节)')
    ax2.set_title('标准速度剖面')
    ax2.grid(True, alpha=0.3)
    ax2.invert_xaxis()
    
    # 添加速度限制线
    ax2.axhline(y=250, color='orange', linestyle='--', alpha=0.7, label='10000ft限速')
    ax2.axhline(y=200, color='red', linestyle='--', alpha=0.7, label='襟翼15度限速')
    ax2.legend()
    
    # 3. 构型时间线
    ax3.barh(range(len(events)), [1]*len(events), color='lightblue', alpha=0.7)
    
    # 添加构型标签
    for i, event in enumerate(events):
        ax3.text(0.5, i, f"{event['action']}\n({event['time_to_landing']}min)", 
                ha='center', va='center', fontsize=8, weight='bold')
    
    ax3.set_xlim(0, 1)
    ax3.set_ylim(-0.5, len(events)-0.5)
    ax3.set_yticks([])
    ax3.set_xticks([])
    ax3.set_title('构型变化时间线')
    
    # 4. 速度限制表
    ax4.axis('off')
    
    speed_limits_text = """
Boeing 737-800 关键速度限制:

襟翼速度限制 (VFE):
• 襟翼 1档:  230 kts
• 襟翼 5度:  230 kts  
• 襟翼15度:  200 kts
• 襟翼30度:  175 kts
• 襟翼40度:  162 kts

起落架速度限制:
• VLO (操作): 270 kts
• VLE (放下): 270 kts

其他重要速度:
• 10000ft以下: 250 kts
• 典型进近:   180 kts
• 最终进近:   150 kts
• Vref参考:   138 kts

关键原则:
✓ 按顺序放出襟翼
✓ 严格遵守速度限制
✓ 起落架在最终进近前放下
✓ 稳定进近的重要性
    """
    
    ax4.text(0.05, 0.95, speed_limits_text, transform=ax4.transAxes,
            fontsize=10, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    plt.tight_layout()
    plt.show()

def main():
    """主函数"""
    
    print("🛩️ 襟翼和起落架标准操作程序")
    print("=" * 60)
    
    procedures = Boeing737FlightProcedures()
    
    # 1. 系统对比分析
    print("📊 襟翼 vs 减速板 系统对比")
    print("-" * 40)
    
    comparison = procedures.analyze_flaps_vs_speedbrakes()
    
    for system_name, system_data in comparison['systems'].items():
        print(f"\n🔧 {system_data['name']}:")
        print(f"   主要目的: {system_data['primary_purpose']}")
        print(f"   使用时机: {system_data['when_used']}")
        print(f"   速度限制: {system_data['speed_limits']}")
        print(f"   飞行员决定权: {system_data['pilot_discretion']}")
    
    # 2. 标准下降程序
    print(f"\n📋 标准下降程序")
    print("-" * 40)
    
    procedure = procedures.get_standard_descent_procedure()
    
    for phase in procedure['phases']:
        print(f"\n✈️ {phase['phase']}:")
        print(f"   高度: {phase['altitude']}")
        print(f"   速度: {phase['speed']}")
        print(f"   构型: {phase['configuration']}")
        print(f"   距离: {phase['typical_distance']}")
        print(f"   关键动作: {', '.join(phase['key_actions'][:2])}")
    
    # 3. 构型决策示例
    print(f"\n🎯 构型决策示例")
    print("-" * 40)
    
    test_scenarios = [
        (15000, 280, 30, "高空下降"),
        (8000, 220, 15, "中空进近"),
        (3000, 180, 8, "最终进近前"),
        (1500, 160, 4, "短最终")
    ]
    
    for alt, speed, dist, scenario in test_scenarios:
        decision = procedures.get_configuration_decision_tree(alt, speed, dist)
        print(f"\n📍 {scenario} ({alt}ft, {speed}kts, {dist}nm):")
        print(f"   建议动作: {decision['recommended_action']}")
        print(f"   下一构型: {decision['next_configuration']}")
    
    # 4. 生成时间线图表
    print(f"\n📈 生成构型程序图表...")
    visualize_configuration_procedures()
    
    # 5. 保存程序数据
    output_data = {
        'aircraft_type': procedures.aircraft_type,
        'flight_phases': {name: {
            'name': phase.name,
            'altitude_range': phase.altitude_range,
            'speed_range': phase.speed_range,
            'distance': phase.typical_distance_to_runway,
            'duration': phase.duration_minutes
        } for name, phase in procedures.flight_phases.items()},
        'configurations': {name: {
            'name': config.name,
            'flap_setting': config.flap_setting,
            'gear_position': config.gear_position,
            'max_speed': config.max_speed,
            'typical_speed': config.typical_speed,
            'when_to_use': config.when_to_use,
            'purpose': config.purpose
        } for name, config in procedures.configurations.items()},
        'speed_limits': procedures.speed_limits,
        'standard_procedure': procedures.get_standard_descent_procedure(),
        'comparison': procedures.analyze_flaps_vs_speedbrakes()
    }
    
    with open('b737_configuration_procedures.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 程序数据已保存到: b737_configuration_procedures.json")
    
    # 总结要点
    print(f"\n💡 关键要点总结:")
    print("🎯 襟翼 ≠ 减速板:")
    print("   • 襟翼: 主要增加升力，按标准程序使用")
    print("   • 减速板: 专门用于快速减速，飞行员自主决定")
    
    print(f"\n⏰ 使用时机:")
    print("   • 襟翼: 进近阶段按速度/高度标准放出")
    print("   • 起落架: 最终进近前(通常8海里内)")
    print("   • 减速板: 任何需要快速减速的时候")
    
    print(f"\n📏 速度限制:")
    print("   • 每个襟翼档位都有严格的VFE限制")
    print("   • 起落架有VLO/VLE限制(270kts)")
    print("   • 10000英尺以下强制限速250kts")
    
    print(f"\n🔄 操作顺序:")
    print("   • 襟翼必须按顺序放出(1→5→15→30→40)")
    print("   • 起落架通常在襟翼15度后放下")
    print("   • 减速板可随时使用和收回")

if __name__ == "__main__":
    main()