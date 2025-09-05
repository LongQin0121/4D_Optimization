#!/usr/bin/env python3
"""
A320 快速功能测试 - 验证主要功能
"""

import jsbsim

def quick_a320_test():
    print("A320 快速功能测试")
    print("=" * 40)
    
    # 加载A320
    try:
        fdm = jsbsim.FGFDMExec(None)
        fdm.load_model('A320')
        print("✓ A320 加载成功!")
    except Exception as e:
        print(f"✗ A320 加载失败: {e}")
        return
    
    # 基本信息
    print(f"\n📊 基本规格:")
    try:
        wingspan = fdm.get_property_value('metrics/bw-ft')
        weight = fdm.get_property_value('inertia/empty-weight-lbs')
        engines = fdm.get_property_value('propulsion/num-engines')
        print(f"  翼展: {wingspan:.0f} 英尺")
        print(f"  空重: {weight:,.0f} 磅")  
        print(f"  发动机: {engines:.0f} 台")
    except:
        print("  无法获取基本规格")
    
    # 设置起飞状态
    print(f"\n🛫 设置起飞状态:")
    try:
        fdm.set_property_value('ic/h-sl-ft', 0.0)        # 地面
        fdm.set_property_value('ic/vc-kts', 0.0)         # 静止
        fdm.set_property_value('gear/gear-cmd-norm', 1.0) # 起落架放下
        fdm.set_property_value('fcs/throttle-cmd-norm[0]', 0.8) # 80%推力
        fdm.run_ic()
        print("  ✓ 初始条件设置成功")
    except Exception as e:
        print(f"  ✗ 初始条件设置失败: {e}")
    
    # 模拟短暂飞行
    print(f"\n✈️ 模拟起飞 (前10秒):")
    for i in range(100):  # 10秒仿真
        fdm.run()
        
        # 自动拉杆起飞
        speed = fdm.get_property_value('velocities/vc-kts')
        if speed > 120:  # 起飞速度
            fdm.set_property_value('fcs/elevator-cmd-norm', 0.2)
        
        # 每秒输出状态
        if i % 10 == 0:
            altitude = fdm.get_property_value('position/h-sl-ft')
            print(f"  {i//10}秒: 速度={speed:.0f}节, 高度={altitude:.0f}英尺")
    
    # 测试控制面
    print(f"\n🎮 控制面测试:")
    controls = {
        'fcs/elevator-cmd-norm': ('升降舵', 0.3),
        'fcs/aileron-cmd-norm': ('副翼', 0.2),
        'fcs/rudder-cmd-norm': ('方向舵', 0.1),
        'fcs/flap-cmd-norm': ('襟翼', 0.5)
    }
    
    for control, (name, value) in controls.items():
        try:
            fdm.set_property_value(control, value)
            fdm.run()
            pos_prop = control.replace('-cmd-', '-pos-').replace('-norm', '-deg')
            position = fdm.get_property_value(pos_prop)
            print(f"  {name}: 指令={value:.1f} → 位置={position:.1f}°")
        except:
            print(f"  {name}: 测试失败")
    
    # 可做的事情列表
    print(f"\n🔧 A320 能做什么:")
    capabilities = [
        "完整起飞降落仿真",
        "飞行控制系统测试", 
        "发动机操作仿真",
        "导航和自动驾驶",
        "应急程序训练",
        "性能数据分析",
        "空中交通管制仿真",
        "机器学习飞行控制"
    ]
    
    for cap in capabilities:
        print(f"  • {cap}")
    
    print(f"\n💡 快速使用示例:")
    print("  fdm = jsbsim.FGFDMExec(None)")
    print("  fdm.load_model('A320')")
    print("  fdm.set_property_value('ic/h-sl-ft', 35000)  # 巡航高度")
    print("  fdm.set_property_value('ic/vc-kts', 450)     # 巡航速度") 
    print("  fdm.run_ic()")
    print("  fdm.run()  # 开始仿真")

if __name__ == "__main__":
    quick_a320_test()