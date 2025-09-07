from bada_dis_time import calculate_descent_profile
import Utility

def calculate_eta_window(origin_fl, target_fl, aircraft_mass, ac_model, standard_route_length=200, print_details=True):
    """
    计算下降过程的时间窗口(ETAmin和ETAmax)，包括巡航段
    
    Parameters:
    origin_fl: int - 起始高度层
    target_fl: int - 目标高度层
    aircraft_mass: float - 飞机重量(kg)
    ac_model: str - 飞机型号
    standard_route_length: float - 标准航路总长度(nm)
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
    
    # 计算ETAmin巡航段
    min_descent_distance = min_summary["Descent Distance (nm)"]
    min_descent_time = round(min_summary["Descent Time (s)"], 1)  # 保留一位小数
    
    # 计算巡航真空速和地速 (ETAmin)
    min_tas = Utility.mach2tas_kt(flight_level=origin_fl, mach=0.80)
    min_gs = round(min_tas, 1)
    
    min_cruise_distance = standard_route_length - min_descent_distance
    min_cruise_time = round(min_cruise_distance / min_gs * 3600, 1)  # 转换为秒，保留一位小数
    min_eta = round(min_cruise_time + min_descent_time, 1)
    
    # 计算ETAmax巡航段
    max_descent_distance = max_summary["Descent Distance (nm)"]
    max_descent_time = round(max_summary["Descent Time (s)"], 1)  # 保留一位小数
    
    # 计算巡航真空速和地速 (ETAmax)
    max_tas = Utility.mach2tas_kt(flight_level=origin_fl, mach=0.73)
    max_gs = round(max_tas, 1)
    
    max_cruise_distance = standard_route_length - max_descent_distance
    max_cruise_time = round(max_cruise_distance / max_gs * 3600, 1)  # 转换为秒，保留一位小数
    max_eta = round(max_cruise_time + max_descent_time, 1)
    
    # 计算时间窗口
    window_seconds = round(max_eta - min_eta, 1)
    
    # 创建ETAmin和ETAmax的数组
    eta_array = [min_eta, max_eta]
    
    # 创建巡航距离数组
    cruise_distance_array = [min_cruise_distance, max_cruise_distance]
    
    # 创建结果字典
    result = {
        "ETAmin": {
            "profile": min_summary["Profile"],
            "cruise_mach": 0.80,
            "cruise_tas_kt": min_tas,
            "cruise_gs_kt": min_gs,
            "cruise_distance_nm": min_cruise_distance,
            "cruise_time_seconds": min_cruise_time,
            "descent_distance_nm": min_descent_distance,
            "descent_time_seconds": min_descent_time,
            "total_time_seconds": min_eta,
            "fuel_kg": min_summary["Fuel Consumption (kg)"]
        },
        "ETAmax": {
            "profile": max_summary["Profile"],
            "cruise_mach": 0.73,
            "cruise_tas_kt": max_tas,
            "cruise_gs_kt": max_gs,
            "cruise_distance_nm": max_cruise_distance,
            "cruise_time_seconds": max_cruise_time,
            "descent_distance_nm": max_descent_distance,
            "descent_time_seconds": max_descent_time,
            "total_time_seconds": max_eta,
            "fuel_kg": max_summary["Fuel Consumption (kg)"]
        },
        "window": {
            "time_seconds": window_seconds,
            "standard_route_length": standard_route_length,
            "eta_array": eta_array,  # 添加ETA数组
            "cruise_distance_array": cruise_distance_array  # 添加巡航距离数组
        }
    }
    
    # 打印结果
    if print_details:
        print(f"\n{'='*100}")
        print(f"全航路ETA窗口分析: {ac_model}")
        print(f"{'='*100}")
        print(f"起始高度: FL{origin_fl}")
        print(f"目标高度: FL{target_fl}")
        print(f"飞机重量: {aircraft_mass/1000:.1f} tonnes")
        print(f"标准航路长度: {standard_route_length} nm")
        print(f"{'='*100}")
        
        print(f"\nETAmin (最快到达方案):")
        print(f"  飞行剖面: {min_summary['Profile']}")
        print(f"  巡航马赫数: 0.80M")
        print(f"  巡航速度: {min_gs} kt")
        print(f"  巡航距离: {min_cruise_distance:.1f} nm")
        print(f"  巡航时间: {min_cruise_time:.1f} 秒")
        print(f"  下降距离: {min_descent_distance:.1f} nm")
        print(f"  下降时间: {min_descent_time:.1f} 秒")
        print(f"  总飞行时间: {min_eta:.1f} 秒")
        print(f"  下降燃油: {min_summary['Fuel Consumption (kg)']:.1f} kg")
        
        print(f"\nETAmax (最慢到达方案):")
        print(f"  飞行剖面: {max_summary['Profile']}")
        print(f"  巡航马赫数: 0.73M")
        print(f"  巡航速度: {max_gs} kt")
        print(f"  巡航距离: {max_cruise_distance:.1f} nm")
        print(f"  巡航时间: {max_cruise_time:.1f} 秒")
        print(f"  下降距离: {max_descent_distance:.1f} nm")
        print(f"  下降时间: {max_descent_time:.1f} 秒")
        print(f"  总飞行时间: {max_eta:.1f} 秒")
        print(f"  下降燃油: {max_summary['Fuel Consumption (kg)']:.1f} kg")
        
        print(f"\n时间窗口:")
        print(f"  窗口大小: {window_seconds:.1f} 秒")
        print(f"  ETA数组: {eta_array}")  # 打印ETA数组
        print(f"  巡航距离数组: {cruise_distance_array}")  # 打印巡航距离数组
        print(f"{'='*100}")
    
    return result, min_df, max_df


# 使用示例
eta_result, min_profile, max_profile = calculate_eta_window(
    origin_fl=370,
    target_fl=30,
    aircraft_mass=60000,
    ac_model="A320-232",
    standard_route_length=200
)


from bada_dis_time import calculate_descent_profile
import Utility
import numpy as np

def find_profiles_for_target_eta(origin_fl, target_fl, aircraft_mass, ac_model, 
                                standard_route_length, target_eta, tolerance=10.0):
    """
    在预设的下降剖面参数中，寻找符合目标ETA的方案
    
    Parameters:
    origin_fl: int - 起始高度层
    target_fl: int - 目标高度层
    aircraft_mass: float - 飞机重量(kg)
    ac_model: str - 飞机型号
    standard_route_length: float - 标准航路总长度(nm)
    target_eta: float - 目标ETA(秒)
    tolerance: float - 允许的ETA误差(秒)
    
    Returns:
    list - 符合条件的下降剖面参数和对应ETA列表
    """
    # 预定义可能的下降剖面参数组合
    profile_params = [
        # 马赫数0.80组
        {"descent_mach": 0.80, "high_cas": 310, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.80, "high_cas": 305, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.80, "high_cas": 300, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.80, "high_cas": 310, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.80, "high_cas": 310, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.80, "high_cas": 305, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.80, "high_cas": 305, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.80, "high_cas": 300, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.80, "high_cas": 300, "intermediate_cas": 220, "intermediate_fl": 60},
        
        # 马赫数0.79组
        {"descent_mach": 0.79, "high_cas": 310, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.79, "high_cas": 305, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.79, "high_cas": 300, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.79, "high_cas": 310, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.79, "high_cas": 310, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.79, "high_cas": 305, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.79, "high_cas": 305, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.79, "high_cas": 300, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.79, "high_cas": 300, "intermediate_cas": 220, "intermediate_fl": 60},
        
        # 马赫数0.78组
        {"descent_mach": 0.78, "high_cas": 300, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.78, "high_cas": 295, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.78, "high_cas": 290, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.78, "high_cas": 285, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.78, "high_cas": 300, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.78, "high_cas": 300, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.78, "high_cas": 295, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.78, "high_cas": 295, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.78, "high_cas": 290, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.78, "high_cas": 290, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.78, "high_cas": 285, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.78, "high_cas": 285, "intermediate_cas": 220, "intermediate_fl": 60},
        
        # 马赫数0.77组
        {"descent_mach": 0.77, "high_cas": 300, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.77, "high_cas": 295, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.77, "high_cas": 290, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.77, "high_cas": 285, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.77, "high_cas": 300, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.77, "high_cas": 300, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.77, "high_cas": 295, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.77, "high_cas": 295, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.77, "high_cas": 290, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.77, "high_cas": 290, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.77, "high_cas": 285, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.77, "high_cas": 285, "intermediate_cas": 220, "intermediate_fl": 60},
        
        # 马赫数0.76组
        {"descent_mach": 0.76, "high_cas": 285, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.76, "high_cas": 280, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.76, "high_cas": 275, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.76, "high_cas": 285, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.76, "high_cas": 285, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.76, "high_cas": 280, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.76, "high_cas": 280, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.76, "high_cas": 275, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.76, "high_cas": 275, "intermediate_cas": 220, "intermediate_fl": 60},
        
        # 马赫数0.75组
        {"descent_mach": 0.75, "high_cas": 285, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.75, "high_cas": 280, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.75, "high_cas": 275, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.75, "high_cas": 285, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.75, "high_cas": 285, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.75, "high_cas": 280, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.75, "high_cas": 280, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.75, "high_cas": 275, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.75, "high_cas": 275, "intermediate_cas": 220, "intermediate_fl": 60},
        
        # 马赫数0.74组
        {"descent_mach": 0.74, "high_cas": 265, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.74, "high_cas": 260, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.74, "high_cas": 255, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.74, "high_cas": 265, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.74, "high_cas": 265, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.74, "high_cas": 260, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.74, "high_cas": 260, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.74, "high_cas": 255, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.74, "high_cas": 255, "intermediate_cas": 220, "intermediate_fl": 60},
        
        # 马赫数0.73组（基本低速方案）
        {"descent_mach": 0.73, "high_cas": 255, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.73, "high_cas": 250, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.73, "high_cas": 245, "intermediate_cas": None, "intermediate_fl": None},
        {"descent_mach": 0.73, "high_cas": 255, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.73, "high_cas": 255, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.73, "high_cas": 250, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.73, "high_cas": 250, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.73, "high_cas": 245, "intermediate_cas": 220, "intermediate_fl": 50},
        {"descent_mach": 0.73, "high_cas": 245, "intermediate_cas": 220, "intermediate_fl": 60},
        {"descent_mach": 0.73, "high_cas": 245, "intermediate_cas": 220, "intermediate_fl": 100},
        {"descent_mach": 0.73, "high_cas": 245, "intermediate_cas": 220, "intermediate_fl": 120},
        {"descent_mach": 0.73, "high_cas": 245, "intermediate_cas": 220, "intermediate_fl": 150}
    ]
        
        # 存储符合条件的剖面
    suitable_profiles = []
    
    # 计算基准ETAmin和ETAmax
    eta_min_result, _, _ = calculate_eta_window(
        origin_fl=origin_fl,
        target_fl=target_fl,
        aircraft_mass=aircraft_mass,
        ac_model=ac_model,
        standard_route_length=standard_route_length,
        print_details=False
    )
    eta_min = eta_min_result["ETAmin"]["total_time_seconds"]
    eta_max = eta_min_result["ETAmax"]["total_time_seconds"]
    
    print(f"基准ETAmin: {eta_min:.1f}秒, ETAmax: {eta_max:.1f}秒")
    print(f"目标ETA: {target_eta:.1f}秒, 允许误差: ±{tolerance:.1f}秒")
    print("\n开始测试各种下降剖面...\n")
    
    # 对每种参数组合计算实际ETA
    for params in profile_params:
        profile_str = format_profile_string(params)
        print(f"测试剖面: {profile_str}")
        
        try:
            # 计算当前参数组合的下降剖面
            descent_params = {
                "cruise_fl": origin_fl,
                "target_fl": target_fl,
                "aircraft_mass": aircraft_mass,
                "ac_model": ac_model,
                "descent_mach": params["descent_mach"],
                "high_cas": params["high_cas"],
                "print_details": False
            }
            
            # 如果有中间高度层和CAS，添加到参数中
            if params["intermediate_fl"] is not None and params["intermediate_cas"] is not None:
                descent_params["intermediate_fl"] = params["intermediate_fl"]
                descent_params["intermediate_cas"] = params["intermediate_cas"]
            
            # 计算下降剖面
            summary, df, decel = calculate_descent_profile(**descent_params)
            
            # 计算总ETA
            descent_distance = summary["Descent Distance (nm)"]
            descent_time = round(summary["Descent Time (s)"], 1)
            
            # 计算巡航段
            cruise_distance = standard_route_length - descent_distance
            cruise_tas = Utility.mach2tas_kt(flight_level=origin_fl, mach=params["descent_mach"])
            cruise_gs = round(cruise_tas, 1)
            cruise_time = round(cruise_distance / cruise_gs * 3600, 1)
            
            # 计算总ETA
            total_eta = round(cruise_time + descent_time, 1)
            
            # 计算与目标ETA的差值
            eta_diff = abs(total_eta - target_eta)
            
            print(f"  ETA: {total_eta:.1f}秒, 与目标差值: {eta_diff:.1f}秒")
            
            # 如果在容差范围内，添加到符合条件的列表
            if eta_diff <= tolerance:
                suitable_profiles.append({
                    "params": params,
                    "profile_str": profile_str,
                    "eta": total_eta,
                    "diff": eta_diff,
                    "descent_distance": descent_distance,
                    "descent_time": descent_time,
                    "cruise_distance": cruise_distance,
                    "cruise_time": cruise_time
                })
                print(f"  ✓ 符合条件!")
            else:
                print(f"  ✗ 超出容差范围")
                
        except Exception as e:
            print(f"  计算出错: {e}")
    
    # 按照与目标ETA的差异排序
    suitable_profiles.sort(key=lambda x: x["diff"])
    
    return suitable_profiles

def format_profile_string(params):
    """将参数格式化为标准下降剖面字符串表示"""
    mach = params["descent_mach"]
    high_cas = params["high_cas"]
    intermediate_cas = params["intermediate_cas"]
    intermediate_fl = params["intermediate_fl"]
    
    if intermediate_fl is None:
        return f"{mach:.2f}M/{high_cas}kt"
    else:
        return f"{mach:.2f}M/{high_cas}kt/{intermediate_cas}kt@FL{intermediate_fl}"

# 使用示例
if __name__ == "__main__":
    # 设置参数
    origin_fl = 370
    target_fl = 30
    aircraft_mass = 60000
    ac_model = "A320-232"
    standard_route_length = 200
    target_eta = 100.0  # 目标ETA为1900秒
    tolerance = 10.0     # 允许误差10秒
    
    # 寻找符合条件的下降剖面
    suitable_profiles = find_profiles_for_target_eta(
        origin_fl=origin_fl,
        target_fl=target_fl,
        aircraft_mass=aircraft_mass,
        ac_model=ac_model,
        standard_route_length=standard_route_length,
        target_eta=target_eta,
        tolerance=tolerance
    )
    
    # 显示结果
    print(f"\n{'='*80}")
    print(f"找到 {len(suitable_profiles)} 个符合条件的下降剖面:")
    print(f"{'='*80}")
    
    for i, profile in enumerate(suitable_profiles):
        params = profile["params"]
        print(f"\n{i+1}. 下降剖面: {profile['profile_str']}")
        print(f"   ETA: {profile['eta']:.1f}秒 (与目标差异: {profile['diff']:.1f}秒)")
        print(f"   巡航马赫数: {params['descent_mach']:.2f}M")
        print(f"   巡航距离: {profile['cruise_distance']:.1f} nm")
        print(f"   巡航时间: {profile['cruise_time']:.1f} 秒")
        print(f"   下降距离: {profile['descent_distance']:.1f} nm")
        print(f"   下降时间: {profile['descent_time']:.1f} 秒")
    
    print(f"\n{'='*80}")
    
    # 将结果保存为数组
    if suitable_profiles:
        eta_array = [profile["eta"] for profile in suitable_profiles]
        print(f"符合条件的ETA数组: {eta_array}")
        
        # 保存第一个最佳匹配剖面的参数，可以后续使用
        best_profile = suitable_profiles[0]["params"]
        print(f"最佳匹配剖面参数: {best_profile}")
    else:
        print("未找到符合条件的下降剖面")