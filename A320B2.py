from bada_dis_time import calculate_descent_profile
import Utility



def calculate_eta_window(origin_fl, target_fl, aircraft_mass, ac_model, print_details=True):
    """
    计算下降过程的时间窗口(ETAmin和ETAmax)
    
    Parameters:
    origin_fl: int - 起始高度层
    target_fl: int - 目标高度层
    aircraft_mass: float - 飞机重量(kg)
    ac_model: str - 飞机型号
    print_details: bool - 是否打印详细信息
    
    Returns:
    dict: 包含ETAmin和ETAmax信息的字典
    """
    # 计算ETAmin - 使用高速下降剖面
    min_summary, min_df, min_decel = calculate_descent_profile(
        cruise_fl=origin_fl,
        target_fl=target_fl,
        aircraft_mass=aircraft_mass,
        ac_model=ac_model,
        descent_mach=0.80,
        high_cas=310,
        print_details=False
    )
    
    # 计算ETAmax - 使用低速下降剖面
    max_summary, max_df, max_decel = calculate_descent_profile(
        cruise_fl=origin_fl,
        target_fl=target_fl,
        aircraft_mass=aircraft_mass,
        ac_model=ac_model,
        descent_mach=0.73,
        high_cas=245,
        intermediate_cas=220,
        intermediate_fl=150,
        print_details=False
    )
    
    # 提取时间和距离信息
    eta_min_seconds = min_summary["Descent Time (s)"]
    eta_min_minutes = eta_min_seconds / 60
    eta_max_seconds = max_summary["Descent Time (s)"]
    eta_max_minutes = eta_max_seconds / 60
    
    min_distance = min_summary["Descent Distance (nm)"]
    max_distance = max_summary["Descent Distance (nm)"]
    
    window_seconds = eta_max_seconds - eta_min_seconds
    window_minutes = window_seconds / 60
    
    # 创建结果字典
    result = {
        "ETAmin": {
            "profile": min_summary["Profile"],
            "time_seconds": eta_min_seconds,
            "time_minutes": eta_min_minutes,
            "distance_nm": min_distance,
            "fuel_kg": min_summary["Fuel Consumption (kg)"]
        },
        "ETAmax": {
            "profile": max_summary["Profile"],
            "time_seconds": eta_max_seconds,
            "time_minutes": eta_max_minutes,
            "distance_nm": max_distance,
            "fuel_kg": max_summary["Fuel Consumption (kg)"]
        },
        "window": {
            "time_seconds": window_seconds,
            "time_minutes": window_minutes,
            "distance_difference_nm": max_distance - min_distance
        }
    }
    
    # 打印结果
    if print_details:
        print(f"\n{'='*80}")
        print(f"ETA窗口分析: {ac_model}")
        print(f"{'='*80}")
        print(f"起始高度: FL{origin_fl}")
        print(f"目标高度: FL{target_fl}")
        print(f"飞机重量: {aircraft_mass/1000:.1f} tonnes")
        print(f"{'='*80}")
        
        print(f"\nETAmin (最快下降方案):")
        print(f"  飞行剖面: {min_summary['Profile']}")
        print(f"  下降时间: {eta_min_seconds:.0f} 秒 ({eta_min_minutes:.1f} 分钟)")
        print(f"  下降距离: {min_distance:.1f} 海里")
        print(f"  燃油消耗: {min_summary['Fuel Consumption (kg)']:.1f} kg")
        
        print(f"\nETAmax (最慢下降方案):")
        print(f"  飞行剖面: {max_summary['Profile']}")
        print(f"  下降时间: {eta_max_seconds:.0f} 秒 ({eta_max_minutes:.1f} 分钟)")
        print(f"  下降距离: {max_distance:.1f} 海里")
        print(f"  燃油消耗: {max_summary['Fuel Consumption (kg)']:.1f} kg")
        
        print(f"\n时间窗口:")
        print(f"  窗口大小: {window_seconds:.0f} 秒 ({window_minutes:.1f} 分钟)")
        print(f"  距离差异: {(max_distance - min_distance):.1f} 海里")
        print(f"{'='*80}")
    
    return result, min_df, max_df

# 使用示例
eta_result, min_profile, max_profile = calculate_eta_window(
    origin_fl=370,
    target_fl=30,
    aircraft_mass=60000,
    ac_model="A320-232",
  

)