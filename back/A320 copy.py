from bada_dis_time import calculate_descent_profile
import Utility

def calculate_eta_window(origin_fl, target_fl, aircraft_mass, ac_model, standard_route_length=200, print_details=False):
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
# eta_result, min_profile, max_profile = calculate_eta_window(
#     origin_fl=370,
#     target_fl=30,
#     aircraft_mass=60000,
#     ac_model="A320-232",
#     standard_route_length=200
# )


from bada_dis_time import calculate_descent_profile
import Utility
import numpy as np

from bada_dis_time import calculate_descent_profile
import Utility
import numpy as np


def find_profile_for_rta(origin_fl, target_fl, aircraft_mass, ac_model,
                        standard_route_length, target_eta, tolerance=10.0, max_profiles=5, print_details=True):
    """
    智能搜索符合目标RTA的下降剖面参数
    
    Parameters:
    origin_fl: int - 起始高度层
    target_fl: int - 目标高度层
    aircraft_mass: float - 飞机重量(kg)
    ac_model: str - 飞机型号
    standard_route_length: float - 标准航路总长度(nm)
    target_eta: float - 目标ETA(秒)
    tolerance: float - 允许的ETA误差(秒)
    max_profiles: int - 最多返回的剖面数量
    
    Returns:
    list - 符合条件的下降剖面参数和对应ETA列表，包含完整的summary, df, decel信息
    """
    # 首先计算基准ETAmin和ETAmax，了解RTA是否在合理范围内
    min_result, min_df, min_decel = calculate_eta_window(
        origin_fl=origin_fl,
        target_fl=target_fl,
        aircraft_mass=aircraft_mass,
        ac_model=ac_model,
        standard_route_length=standard_route_length,
        print_details=False
    )
    
    eta_min = min_result["ETAmin"]["total_time_seconds"]
    eta_max = min_result["ETAmax"]["total_time_seconds"]
    eta_window = eta_max - eta_min
    
    print(f"基准ETAmin: {eta_min:.1f}秒, ETAmax: {eta_max:.1f}秒")
    print(f"ETA窗口: {eta_window:.1f}秒")
    print(f"目标RTA: {target_eta:.1f}秒, 允许误差: ±{tolerance:.1f}秒")
    
    # 检查目标RTA是否在可行范围内
    if target_eta < eta_min - tolerance:
        print(f"警告: 目标RTA比最小ETA还小 {eta_min - target_eta:.1f}秒")
        return []
    elif target_eta > eta_max + tolerance:
        print(f"警告: 目标RTA比最大ETA还大 {target_eta - eta_max:.1f}秒")
        return []
    
    # 生成智能参数搜索空间
    profile_params = generate_profile_params(eta_min, eta_max, target_eta)
    
    if print_details:
        print(f"\n生成了 {len(profile_params)} 个参数组合进行搜索")
    print("\n开始搜索符合RTA的下降剖面...\n")
    
    # 存储符合条件的剖面
    suitable_profiles = []
    
    # 对每种参数组合计算实际ETA
    for i, params in enumerate(profile_params):
        profile_str = format_profile_string(params)
        if print_details:
            print(f"测试剖面 {i+1}/{len(profile_params)}: {profile_str}")
        
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
            
            # 计算下降剖面 - 保存完整的三个返回值
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
            
            if print_details:
                print(f"  ETA: {total_eta:.1f}秒, 与目标差值: {eta_diff:.1f}秒")
            
            # 如果在容差范围内，添加到符合条件的列表 - 现在包含完整信息
            if eta_diff <= tolerance:
                suitable_profiles.append({
                    # 基本参数信息
                    "params": params,
                    "profile_str": profile_str,
                    
                    # ETA相关信息
                    "eta": total_eta,
                    "diff": eta_diff,
                    "descent_time": descent_time,
                    "cruise_time": cruise_time,
                    
                    # 距离信息
                    "descent_distance": descent_distance,
                    "cruise_distance": cruise_distance,
                    
                    # 燃油消耗
                    "fuel_kg": summary["Fuel Consumption (kg)"],
                    
                    # 完整的计算结果 - 新增
                    "summary": summary,       # 完整的汇总信息
                    "df": df.copy(),         # 详细的逐点计算数据 (复制以避免引用问题)
                    "decel": decel           # 减速信息
                })
                if print_details:
                    print(f"  ✓ 符合条件!")
            else:
                if print_details:
                    print(f"  ✗ 超出容差范围")
                
        except Exception as e:
            if print_details:
                print(f"  计算出错: {e}")
    
    # 按照与目标ETA的差异排序
    suitable_profiles.sort(key=lambda x: x["diff"])
    
    # 限制返回的剖面数量
    suitable_profiles = suitable_profiles[:max_profiles]
    
    return suitable_profiles


def get_best_profile_details(suitable_profiles):
    """
    获取最佳匹配剖面的详细信息
    
    Parameters:
    suitable_profiles: list - find_profile_for_rta返回的剖面列表
    
    Returns:
    dict - 最佳剖面的完整信息，如果没有符合条件的剖面则返回None
    """
    if not suitable_profiles:
        return None
    
    # 第一个就是最佳匹配的（已按diff排序）
    best_profile = suitable_profiles[0]
    
    return {
        "profile_str": best_profile["profile_str"],
        "params": best_profile["params"],
        "eta": best_profile["eta"],
        "diff": best_profile["diff"],
        "summary": best_profile["summary"],
        "df": best_profile["df"],
        "decel": best_profile["decel"]
    }


def print_suitable_profiles_summary(suitable_profiles):
    """
    打印符合条件剖面的汇总信息
    
    Parameters:
    suitable_profiles: list - find_profile_for_rta返回的剖面列表
    """
    if not suitable_profiles:
        print("没有找到符合条件的剖面")
        return
    
    print(f"\n找到 {len(suitable_profiles)} 个符合条件的剖面:")
    profile_names = [profile["profile_str"] for profile in suitable_profiles]
    print(f"符合条件的剖面数组: {profile_names}")
    
    # 显示最佳匹配剖面
    best_profile = suitable_profiles[0]
    print(f"\n最佳匹配剖面: {best_profile['profile_str']}")
    print(f"最佳匹配剖面参数: {best_profile['params']}")
    print(f"ETA: {best_profile['eta']:.1f}秒, 误差: {best_profile['diff']:.1f}秒")
    print(f"燃油消耗: {best_profile['fuel_kg']:.1f}kg")
    
    # 提示可以获取详细信息
    print(f"\n提示: 可以通过 suitable_profiles[0]['summary']、suitable_profiles[0]['df']、suitable_profiles[0]['decel'] 获取详细计算结果")


# 其他函数保持不变...
def generate_profile_params(eta_min, eta_max, target_eta):
    """
    智能生成下降剖面参数组合，基于目标ETA在ETA窗口中的位置
    """
    # ... 保持原有代码不变
    params_list = []
    
    # 计算目标ETA在ETA窗口中的相对位置 (0.0表示接近ETAmin, 1.0表示接近ETAmax)
    relative_position = (target_eta - eta_min) / (eta_max - eta_min)
    
    # 根据相对位置调整马赫数和CAS的搜索范围
    if relative_position < 0.2:
        # 接近ETAmin，优先搜索高马赫数和高CAS
        mach_values = [0.78, 0.79, 0.80]
        cas_ranges = {
            0.78: [290, 295, 300],
            0.79: [295, 300, 305],
            0.80: [300, 305, 310]
        }
        # 接近ETAmin时，中间高度层可能不需要
        int_options = [
            (None, None),
            (220, 50),
            (220, 50)
        ]
    elif relative_position < 0.4:
        # ETAmin和中间点之间，偏向快速剖面
        mach_values = [0.76, 0.77, 0.78, 0.79]
        cas_ranges = {
            0.76: [275, 280, 285],
            0.77: [280, 285, 290, 295],
            0.78: [285, 290, 295],
            0.79: [290, 295, 300]
        }
        int_options = [
            (None, None),
            (220, 50),
            (220, 60)
        ]
    elif relative_position < 0.6:
        # 接近中间点，中等马赫数和CAS
        mach_values = [0.75, 0.76, 0.77]
        cas_ranges = {
            0.75: [265, 270, 275, 280],
            0.76: [270, 275, 280],
            0.77: [275, 280, 285]
        }
        int_options = [
            (None, None),
            (220, 50),
            (220, 60),
            (220, 80)
        ]
    elif relative_position < 0.8:
        # 中间点和ETAmax之间，偏向慢速剖面
        mach_values = [0.74, 0.75, 0.76]
        cas_ranges = {
            0.74: [255, 260, 265],
            0.75: [260, 265, 270],
            0.76: [265, 270, 275]
        }
        int_options = [
            (220, 50),
            (220, 60),
            (220, 80),
            (220, 100)
        ]
    else:
        # 接近ETAmax，优先搜索低马赫数和低CAS
        mach_values = [0.73, 0.74]
        cas_ranges = {
            0.73: [245, 250, 255],
            0.74: [250, 255, 260]
        }
        int_options = [
            (220, 60),
            (220, 80),
            (220, 100),
            (220, 120),
            (220, 150)
        ]
    
    # 生成参数组合
    for mach in mach_values:
        for cas in cas_ranges[mach]:
            for int_cas, int_fl in int_options:
                # 创建参数字典
                param = {
                    "descent_mach": mach,
                    "high_cas": cas,
                    "intermediate_cas": int_cas,
                    "intermediate_fl": int_fl
                }
                
                params_list.append(param)
    
    # 始终添加基准配置
    params_list.append({
        "descent_mach": 0.80,
        "high_cas": 310,
        "intermediate_cas": None,
        "intermediate_fl": None
    })
    
    params_list.append({
        "descent_mach": 0.73,
        "high_cas": 245,
        "intermediate_cas": 220,
        "intermediate_fl": 150
    })
    
    return params_list

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
    target_eta = 1900.0  # 目标RTA为1900秒
    tolerance = 10.0     # 允许误差10秒
    
    # 寻找符合条件的下降剖面
    suitable_profiles = find_profile_for_rta(
        origin_fl=origin_fl,
        target_fl=target_fl,
        aircraft_mass=aircraft_mass,
        ac_model=ac_model,
        standard_route_length=standard_route_length,
        target_eta=target_eta,
        tolerance=tolerance,
        print_details=True
    )
    
    # 打印汇总信息
    print_suitable_profiles_summary(suitable_profiles)
    
    # 获取最佳剖面的详细信息
    best_profile_details = get_best_profile_details(suitable_profiles)
    if best_profile_details:
        print(f"\n最佳剖面的详细summary: {best_profile_details['summary']}")
        print(f"最佳剖面的df数据框形状: {best_profile_details['df'].shape}")
        print(f"最佳剖面的decel信息: {best_profile_details['decel']}")
        
        # 如果需要查看详细的df内容
        # print(f"\n详细的df数据:\n{best_profile_details['df']}")