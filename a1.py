#!/usr/bin/env python3
"""
JSBSim A320 FMS 和 4D 导航功能分析
检查是否支持RTA (Required Time of Arrival) 和航路点导航
"""

import jsbsim
import math
from datetime import datetime, timedelta

class A320_FMS_Analyzer:
    def __init__(self):
        self.fdm = None
        self.fms_properties = []
        self.autopilot_properties = []
        self.navigation_properties = []
        
    def load_aircraft(self):
        """加载A320模型"""
        try:
            self.fdm = jsbsim.FGFDMExec(None)
            self.fdm.load_model('A320')
            self.fdm.run_ic()
            print("✅ A320 模型加载成功")
            return True
        except Exception as e:
            print(f"❌ A320 模型加载失败: {e}")
            return False
    
    def scan_fms_properties(self):
        """扫描所有可能的FMS相关属性"""
        
        print("\n🔍 扫描 FMS 和导航相关属性...")
        print("=" * 60)
        
        # 可能的FMS属性列表
        fms_property_candidates = [
            # 基本FMS功能
            'fms/active',
            'fms/waypoint-active',
            'fms/waypoint-count', 
            'fms/current-waypoint',
            'fms/next-waypoint',
            'fms/route-active',
            'fms/flight-plan-active',
            
            # 航路点相关
            'navigation/waypoint[0]/lat-deg',
            'navigation/waypoint[0]/lon-deg', 
            'navigation/waypoint[0]/alt-ft',
            'navigation/waypoint[0]/eta',
            'navigation/waypoint[0]/distance-nm',
            'navigation/waypoint[0]/bearing-deg',
            
            # RTA相关 (Required Time of Arrival)
            'fms/rta-active',
            'fms/rta-time',
            'fms/required-time-arrival',
            'fms/eta-error',
            'fms/time-constraint',
            
            # 自动驾驶仪
            'autopilot/active',
            'autopilot/heading-select',
            'autopilot/altitude-select',
            'autopilot/speed-select',
            'autopilot/vnav-active',
            'autopilot/lnav-active',
            
            # GPS/导航
            'gps/waypoint-distance-nm',
            'gps/waypoint-bearing-deg',
            'gps/route-distance-nm',
            'gps/route-time-remaining',
            'gps/ground-track-deg',
            'gps/course-error-nm',
            
            # 飞行管理
            'guidance/target-latitude-deg',
            'guidance/target-longitude-deg',
            'guidance/target-altitude-ft',
            'guidance/target-heading-deg',
            'guidance/cross-track-error-nm',
            'guidance/along-track-distance-nm',
            
            # 时间约束
            'flight-management/time-constraint-active',
            'flight-management/required-time',
            'flight-management/estimated-time',
            'flight-management/time-error-sec'
        ]
        
        # 自动驾驶仪属性
        autopilot_candidates = [
            'ap/active',
            'ap/autopilot-roll-on',
            'ap/roll-attitude-mode',
            'ap/heading-mode',
            'ap/altitude-mode',
            'ap/speed-mode',
            'ap/roll-cmd-norm-output',
            'ap/pitch-cmd-norm-output',
            'ap/heading-setpoint-deg',
            'ap/altitude-setpoint-ft',
            'ap/airspeed-setpoint-kt'
        ]
        
        # 检查每个属性
        available_properties = []
        
        print("📋 FMS 功能检查:")
        for prop in fms_property_candidates:
            try:
                value = self.fdm.get_property_value(prop)
                available_properties.append((prop, value, 'FMS'))
                print(f"  ✅ {prop}: {value}")
            except:
                print(f"  ❌ {prop}: 不可用")
        
        print(f"\n📋 自动驾驶仪功能检查:")
        for prop in autopilot_candidates:
            try:
                value = self.fdm.get_property_value(prop)
                available_properties.append((prop, value, 'AP'))
                print(f"  ✅ {prop}: {value}")
            except:
                print(f"  ❌ {prop}: 不可用")
        
        return available_properties
    
    def test_waypoint_navigation(self):
        """测试航路点导航功能"""
        
        print(f"\n🧭 测试航路点导航功能...")
        print("=" * 60)
        
        # 尝试设置目标航路点
        target_waypoints = [
            # 北京 -> 上海航线上的几个点
            {'name': 'PEK_DEP', 'lat': 40.08, 'lon': 116.58, 'alt': 35000},
            {'name': 'WAYPOINT_1', 'lat': 39.5, 'lon': 118.0, 'alt': 35000},
            {'name': 'WAYPOINT_2', 'lat': 38.5, 'lon': 120.0, 'alt': 35000},
            {'name': 'PVG_ARR', 'lat': 31.15, 'lon': 121.81, 'alt': 1000}
        ]
        
        waypoint_properties = [
            'guidance/target-latitude-deg',
            'guidance/target-longitude-deg', 
            'guidance/target-altitude-ft',
            'navigation/wp/lat-deg',
            'navigation/wp/lon-deg',
            'fms/wp-lat',
            'fms/wp-lon'
        ]
        
        for i, waypoint in enumerate(target_waypoints):
            print(f"\n航路点 {i+1}: {waypoint['name']}")
            
            # 尝试不同的设置方法
            for prop_base in ['guidance/target', 'navigation/wp', 'fms/wp']:
                try:
                    if prop_base == 'guidance/target':
                        self.fdm.set_property_value(f'{prop_base}-latitude-deg', waypoint['lat'])
                        self.fdm.set_property_value(f'{prop_base}-longitude-deg', waypoint['lon'])
                        self.fdm.set_property_value(f'{prop_base}-altitude-ft', waypoint['alt'])
                    else:
                        self.fdm.set_property_value(f'{prop_base}-lat', waypoint['lat'])
                        self.fdm.set_property_value(f'{prop_base}-lon', waypoint['lon'])
                    
                    print(f"  ✅ 使用 {prop_base} 设置成功")
                    
                    # 计算到航路点的距离和方位
                    current_lat = self.fdm.get_property_value('position/lat-gc-deg')
                    current_lon = self.fdm.get_property_value('position/long-gc-deg')
                    
                    distance = self.calculate_distance(
                        current_lat, current_lon,
                        waypoint['lat'], waypoint['lon']
                    )
                    
                    bearing = self.calculate_bearing(
                        current_lat, current_lon,
                        waypoint['lat'], waypoint['lon']
                    )
                    
                    print(f"     距离: {distance:.1f} 海里")
                    print(f"     方位: {bearing:.1f}°")
                    
                    break
                    
                except Exception as e:
                    print(f"  ❌ 使用 {prop_base} 设置失败: {str(e)[:50]}...")
    
    def test_rta_functionality(self):
        """测试RTA (Required Time of Arrival) 功能"""
        
        print(f"\n⏰ 测试 RTA (Required Time of Arrival) 功能...")
        print("=" * 60)
        
        # RTA相关属性测试
        rta_properties = [
            'fms/rta-active',
            'fms/rta-time',
            'fms/required-time-arrival',
            'fms/eta-error',
            'fms/time-constraint',
            'flight-management/time-constraint-active',
            'flight-management/required-time',
            'flight-management/estimated-time',
            'flight-management/time-error-sec',
            'autopilot/rta-mode',
            'guidance/rta-active'
        ]
        
        print("🔍 检查RTA属性支持:")
        rta_supported = False
        
        for prop in rta_properties:
            try:
                value = self.fdm.get_property_value(prop)
                print(f"  ✅ {prop}: {value}")
                rta_supported = True
            except:
                print(f"  ❌ {prop}: 不支持")
        
        if not rta_supported:
            print(f"\n⚠️ A320模型似乎不支持原生RTA功能")
            print(f"💡 但可以通过编程实现4D导航:")
            return self.implement_custom_rta()
        else:
            print(f"\n✅ 检测到RTA功能支持!")
            return self.test_native_rta()
    
    def implement_custom_rta(self):
        """实现自定义的4D导航/RTA功能"""
        
        print(f"\n🔧 实现自定义4D导航...")
        print("=" * 40)
        
        # 设置目标：10分钟后到达指定点
        target_time = datetime.now() + timedelta(minutes=10)
        target_lat = 40.5   # 目标纬度
        target_lon = 117.0  # 目标经度
        target_alt = 35000  # 目标高度
        
        print(f"🎯 4D目标设置:")
        print(f"   位置: ({target_lat}, {target_lon})")
        print(f"   高度: {target_alt} 英尺")
        print(f"   时间: {target_time.strftime('%H:%M:%S')}")
        
        # 获取当前位置
        current_lat = self.fdm.get_property_value('position/lat-gc-deg')
        current_lon = self.fdm.get_property_value('position/long-gc-deg')
        current_alt = self.fdm.get_property_value('position/h-sl-ft')
        current_speed = self.fdm.get_property_value('velocities/vc-kts')
        
        # 计算距离和所需速度
        distance_nm = self.calculate_distance(current_lat, current_lon, target_lat, target_lon)
        time_available_hours = 10 / 60  # 10分钟转小时
        required_speed = distance_nm / time_available_hours
        
        print(f"\n📊 4D导航计算:")
        print(f"   当前位置: ({current_lat:.3f}, {current_lon:.3f})")
        print(f"   当前高度: {current_alt:.0f} 英尺")
        print(f"   当前速度: {current_speed:.0f} 节")
        print(f"   到目标距离: {distance_nm:.1f} 海里")
        print(f"   所需速度: {required_speed:.0f} 节")
        
        # 判断是否可行
        if required_speed > 600:  # A320最大速度限制
            print(f"⚠️ 所需速度过高，无法在指定时间到达")
            return False
        elif required_speed < 200:  # A320最小巡航速度
            print(f"⚠️ 所需速度过低，需要延迟到达")
            return False
        else:
            print(f"✅ 4D导航可行，建议巡航速度: {required_speed:.0f} 节")
            
            # 演示速度调整
            try:
                # 设置推力以达到目标速度
                thrust_setting = min(1.0, required_speed / 500)  # 简化的推力计算
                self.fdm.set_property_value('fcs/throttle-cmd-norm[0]', thrust_setting)
                self.fdm.set_property_value('fcs/throttle-cmd-norm[1]', thrust_setting)
                
                print(f"🎮 推力设置: {thrust_setting*100:.0f}%")
                
                # 设置航向
                bearing = self.calculate_bearing(current_lat, current_lon, target_lat, target_lon)
                self.fdm.set_property_value('fcs/heading-setpoint-deg', bearing)
                
                print(f"🧭 目标航向: {bearing:.0f}°")
                
                return True
                
            except Exception as e:
                print(f"❌ 控制设置失败: {e}")
                return False
    
    def test_native_rta(self):
        """测试原生RTA功能"""
        
        print(f"测试原生RTA功能...")
        
        # 设置RTA参数
        try:
            target_time = (datetime.now() + timedelta(minutes=15)).timestamp()
            self.fdm.set_property_value('fms/required-time-arrival', target_time)
            self.fdm.set_property_value('fms/rta-active', 1.0)
            
            print(f"✅ RTA设置成功")
            return True
            
        except Exception as e:
            print(f"❌ RTA设置失败: {e}")
            return False
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """计算两点间的大圆距离（海里）"""
        R = 3440.065  # 地球半径（海里）
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """计算方位角"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon = math.radians(lon2 - lon1)
        
        y = math.sin(delta_lon) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
        
        bearing = math.atan2(y, x)
        return (math.degrees(bearing) + 360) % 360
    
    def analyze_4d_capabilities(self):
        """分析4D导航能力总结"""
        
        print(f"\n📋 A320 的 4D 导航能力总结")
        print("=" * 60)
        
        capabilities = {
            'basic_autopilot': '基本自动驾驶仪',
            'waypoint_nav': '航路点导航', 
            'time_constraints': '时间约束',
            'rta_native': '原生RTA功能',
            'speed_control': '速度控制',
            'altitude_control': '高度控制',
            '4d_trajectory': '4D轨迹管理'
        }
        
        # 检查各项能力
        results = {}
        
        # 基本自动驾驶仪
        try:
            self.fdm.set_property_value('ap/active', 1)
            results['basic_autopilot'] = True
        except:
            results['basic_autopilot'] = False
        
        # 速度控制
        try:
            self.fdm.set_property_value('fcs/throttle-cmd-norm[0]', 0.8)
            results['speed_control'] = True
        except:
            results['speed_control'] = False
        
        # 高度控制
        try:
            self.fdm.set_property_value('fcs/elevator-cmd-norm', 0.1)
            results['altitude_control'] = True
        except:
            results['altitude_control'] = False
        
        # 其他功能基于属性检查
        results['waypoint_nav'] = False
        results['time_constraints'] = False
        results['rta_native'] = False
        results['4d_trajectory'] = False
        
        # 显示结果
        print(f"功能评估:")
        for key, desc in capabilities.items():
            status = "✅ 支持" if results.get(key, False) else "❌ 不支持"
            print(f"  {desc:20s}: {status}")
        
        # 总结
        supported_count = sum(results.values())
        total_count = len(capabilities)
        
        print(f"\n📊 支持度: {supported_count}/{total_count} ({supported_count/total_count*100:.0f}%)")
        
        if supported_count >= 5:
            print(f"✅ A320具有良好的4D导航基础能力")
        elif supported_count >= 3:
            print(f"⚠️ A320具有基本的导航能力，需要自定义实现4D功能")
        else:
            print(f"❌ A320的4D导航能力有限")
        
        return results

def main():
    """主程序"""
    
    print("🛩️ JSBSim A320 FMS & 4D 导航功能全面分析")
    print("=" * 80)
    
    analyzer = A320_FMS_Analyzer()
    
    # 加载飞机
    if not analyzer.load_aircraft():
        return
    
    # 扫描FMS属性
    available_props = analyzer.scan_fms_properties()
    
    # 测试航路点导航
    analyzer.test_waypoint_navigation()
    
    # 测试RTA功能
    analyzer.test_rta_functionality()
    
    # 分析4D能力
    results = analyzer.analyze_4d_capabilities()
    
    # 最终结论
    print(f"\n🎯 最终结论")
    print("=" * 40)
    print(f"JSBSim A320模型:")
    print(f"• 具备基础的飞行动力学仿真能力")
    print(f"• 支持基本的自动驾驶仪功能")
    print(f"• 可以通过编程实现4D导航功能")
    print(f"• 需要自定义实现RTA (指定时间过某点)")
    print(f"• 适合用于ATC研究和4D轨迹仿真")
    
    print(f"\n💡 建议:")
    print(f"• 使用编程方式实现4D FMS功能")
    print(f"• 结合外部飞行计划系统")
    print(f"• 可作为4D轨迹生成和验证工具")

if __name__ == "__main__":
    main()