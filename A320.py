from bada_dis_time import calculate_complete_descent_profile
import Utility

def calculate_eta_range(cruise_fl=370, target_fl=30, aircraft_mass=60000, 
                        ac_model="A320-232", standard_route_length=200):
    """
    计算最早到达时间(ETAmin)和最晚到达时间(ETAmax)
    
    参数:
        cruise_fl (int): 巡航飞行高度
        target_fl (int): 目标飞行高度
        aircraft_mass (int): 飞机质量(千克)
        ac_model (str): 飞机型号
        standard_route_length (float): 标准航线长度(海里)
    
    返回:
        tuple: (eta_min, eta_max, eta_min_profile, eta_max_profile)
    """
    print("\n计算ETAmin和ETAmax中...\n")
    
    # 已知的最快飞行时间配置
    fast_config = {
        'mach': 0.80, 
        'high_cas': 310, 
        'low_cas': 0, 
        'low_cas_fl': 0, 
        'description': '不使用低速CAS'
    }
    
    # 已知的最慢飞行时间配置
    slow_config = {
        'mach': 0.73, 
        'high_cas': 245, 
        'low_cas': 220, 
        'low_cas_fl': 150, 
        'description': 'FL150低速转换'
    }
    
    # 计算最快配置
    descent_mach = fast_config['mach']
    high_cas = fast_config['high_cas']
    low_cas = fast_config['low_cas']
    low_cas_fl = fast_config['low_cas_fl']
    description = fast_config['description']
    
    # 计算巡航真空速和地速
    tas = Utility.mach2tas_kt(flight_level=cruise_fl, mach=descent_mach, delta_temp=0)
    gs = round(tas, 1)
    
    try:
        # 计算下降剖面
        _, Param, _, df, _ = calculate_complete_descent_profile(
            cruise_fl=cruise_fl,
            target_fl=target_fl,
            aircraft_mass=aircraft_mass,
            descent_mach=descent_mach,
            high_cas=high_cas,
            ac_model=ac_model,
            low_cas=low_cas,
            low_cas_fl=low_cas_fl,
            print_details=False
        )
        
        # 提取关键参数
        descent_distance = Param['Descent Distance (nm)']
        descent_time = Param['Descent Time (s)']
        
        # 计算总飞行时间
        cruise_distance = standard_route_length - descent_distance
        cruise_time = cruise_distance / gs * 3600
        eta_min = cruise_time + descent_time
        
        eta_min_profile = {
            'mach': descent_mach,
            'high_cas': high_cas,
            'low_cas': low_cas,
            'low_cas_fl': low_cas_fl,
            'low_cas_desc': description,
            'descent_distance': descent_distance,
            'descent_time': descent_time,
            'cruise_time': cruise_time,
            'total_time_sec': eta_min,
            'total_time_min': eta_min / 60
        }
    except Exception as e:
        print(f"计算最早到达时间出错: {e}")
        eta_min = None
        eta_min_profile = None
    
    # 计算最慢配置
    descent_mach = slow_config['mach']
    high_cas = slow_config['high_cas']
    low_cas = slow_config['low_cas']
    low_cas_fl = slow_config['low_cas_fl']
    description = slow_config['description']
    
    # 计算巡航真空速和地速
    tas = Utility.mach2tas_kt(flight_level=cruise_fl, mach=descent_mach, delta_temp=0)
    gs = round(tas, 1)
    
    try:
        # 计算下降剖面
        _, Param, _, df, _ = calculate_complete_descent_profile(
            cruise_fl=cruise_fl,
            target_fl=target_fl,
            aircraft_mass=aircraft_mass,
            descent_mach=descent_mach,
            high_cas=high_cas,
            ac_model=ac_model,
            low_cas=low_cas,
            low_cas_fl=low_cas_fl,
            print_details=False
        )
        
        # 提取关键参数
        descent_distance = Param['Descent Distance (nm)']
        descent_time = Param['Descent Time (s)']
        
        # 计算总飞行时间
        cruise_distance = standard_route_length - descent_distance
        cruise_time = cruise_distance / gs * 3600
        eta_max = cruise_time + descent_time
        
        eta_max_profile = {
            'mach': descent_mach,
            'high_cas': high_cas,
            'low_cas': low_cas,
            'low_cas_fl': low_cas_fl,
            'low_cas_desc': description,
            'descent_distance': descent_distance,
            'descent_time': descent_time,
            'cruise_time': cruise_time,
            'total_time_sec': eta_max,
            'total_time_min': eta_max / 60
        }
    except Exception as e:
        print(f"计算最晚到达时间出错: {e}")
        eta_max = None
        eta_max_profile = None
    
    if eta_min is not None and eta_max is not None:
        print("\n======= ETA范围 =======")
        print(f"最早到达时间(ETAmin): {eta_min:.2f}秒 ({eta_min/60:.2f}分钟)")
        print(f"配置: Mach {eta_min_profile['mach']}, High CAS {eta_min_profile['high_cas']}, {eta_min_profile['low_cas_desc']}")
        
        print(f"\n最晚到达时间(ETAmax): {eta_max:.2f}秒 ({eta_max/60:.2f}分钟)")
        print(f"配置: Mach {eta_max_profile['mach']}, High CAS {eta_max_profile['high_cas']}, {eta_max_profile['low_cas_desc']}")
        
        print(f"\nETA范围: {eta_max - eta_min:.2f}秒 ({(eta_max - eta_min)/60:.2f}分钟)")

        print(f"\nETA: [{eta_min:.1f} - {eta_max:.1f}]")
        print("======================")
    
    return eta_min, eta_max, eta_min_profile, eta_max_profile



def find_profile_for_rta(target_rta, tolerance=10, cruise_fl=370, target_fl=30, 
                        aircraft_mass=60000, ac_model="A320-232", standard_route_length=200):
    """
    查找与指定RTA匹配的飞行剖面
    
    参数:
        target_rta (float): 目标所需到达时间(秒)
        tolerance (float): 与RTA的允许误差(秒)
        cruise_fl (int): 巡航飞行高度
        target_fl (int): 目标飞行高度
        aircraft_mass (int): 飞机质量(千克)
        ac_model (str): 飞机型号
        standard_route_length (float): 标准航线长度(海里)
    
    返回:
        tuple: (best_profile, param, df) - 最佳匹配的飞行剖面, 参数详情, 完整的下降数据
    """
    # 低速组 - 测试全套低速配置
    low_mach_cas_groups = [
        {
            'mach': 0.73, 
            'cas_values': [245, 250, 255, 260],
            'low_cas_configs': [
                {'low_cas': 0, 'low_cas_fl': 0, 'description': '不使用低速CAS'},
                {'low_cas': 220, 'low_cas_fl': 150, 'description': 'FL150低速转换'},
                {'low_cas': 220, 'low_cas_fl': 140, 'description': 'FL140低速转换'},
                {'low_cas': 220, 'low_cas_fl': 130, 'description': 'FL130低速转换'},
                {'low_cas': 220, 'low_cas_fl': 120, 'description': 'FL120低速转换'},
                {'low_cas': 220, 'low_cas_fl': 110, 'description': 'FL110低速转换'},
                {'low_cas': 220, 'low_cas_fl': 100, 'description': 'FL100低速转换'},
                {'low_cas': 220, 'low_cas_fl': 90, 'description': 'FL090低速转换'},
                {'low_cas': 220, 'low_cas_fl': 60, 'description': 'FL060低速转换'},
                {'low_cas': 220, 'low_cas_fl': 50, 'description': 'FL050低速转换'}
            ]
        }
    ]

    # 中速组 - 仅测试FL060和FL050低速转换
    mid_mach_cas_groups = [
        {
            'mach': 0.74, 
            'cas_values': [260, 265, 270],
            'low_cas_configs': [
                {'low_cas': 220, 'low_cas_fl': 60, 'description': 'FL060低速转换'},
                {'low_cas': 220, 'low_cas_fl': 50, 'description': 'FL050低速转换'}
            ]
        },
        {
            'mach': 0.75, 
            'cas_values': [270, 275, 280],
            'low_cas_configs': [
                {'low_cas': 220, 'low_cas_fl': 60, 'description': 'FL060低速转换'},
                {'low_cas': 220, 'low_cas_fl': 50, 'description': 'FL050低速转换'}
            ]
        },
        {
            'mach': 0.76, 
            'cas_values': [275, 280, 285],
            'low_cas_configs': [
                {'low_cas': 220, 'low_cas_fl': 60, 'description': 'FL060低速转换'},
                {'low_cas': 220, 'low_cas_fl': 50, 'description': 'FL050低速转换'}
            ]
        },
        {
            'mach': 0.77, 
            'cas_values': [280, 285, 290],
            'low_cas_configs': [
                {'low_cas': 220, 'low_cas_fl': 60, 'description': 'FL060低速转换'},
                {'low_cas': 220, 'low_cas_fl': 50, 'description': 'FL050低速转换'}
            ]
        },
        {
            'mach': 0.78, 
            'cas_values': [290, 295, 300],
            'low_cas_configs': [
                {'low_cas': 220, 'low_cas_fl': 60, 'description': 'FL060低速转换'},
                {'low_cas': 220, 'low_cas_fl': 50, 'description': 'FL050低速转换'}
            ]
        }
    ]

    # 高速组 - 测试FL060和FL050低速转换，外加不使用低速转换的配置
    high_mach_cas_groups = [
        {
            'mach': 0.79, 
            'cas_values': [295, 300, 305],
            'low_cas_configs': [
                {'low_cas': 0, 'low_cas_fl': 0, 'description': '不使用低速CAS'},
                {'low_cas': 220, 'low_cas_fl': 60, 'description': 'FL060低速转换'},
                {'low_cas': 220, 'low_cas_fl': 50, 'description': 'FL050低速转换'}
            ]
        },
        {
            'mach': 0.80, 
            'cas_values': [300, 305, 310],
            'low_cas_configs': [
                {'low_cas': 0, 'low_cas_fl': 0, 'description': '不使用低速CAS'},
                {'low_cas': 220, 'low_cas_fl': 60, 'description': 'FL060低速转换'},
                {'low_cas': 220, 'low_cas_fl': 50, 'description': 'FL050低速转换'},
                {'low_cas': 220, 'low_cas_fl': 40, 'description': 'FL040低速转换'}
            ]
        }
    ]

    # 合并所有组
    all_groups = low_mach_cas_groups + mid_mach_cas_groups + high_mach_cas_groups

    # 存储结果的列表
    results = []

    print(f"查找RTA={target_rta}秒，差值小于{tolerance}秒的配置...\n")

    # 遍历所有组合
    for group in all_groups:
        descent_mach = group['mach']
        
        for high_cas in group['cas_values']:
            for low_cas_config in group['low_cas_configs']:
                low_cas = low_cas_config['low_cas']
                low_cas_fl = low_cas_config['low_cas_fl']
                low_cas_desc = low_cas_config['description']
                
                # 计算巡航真空速和地速(假设零风)
                tas = Utility.mach2tas_kt(flight_level=cruise_fl, mach=descent_mach, delta_temp=0)
                gs = round(tas, 1)
                
                # 计算完整下降剖面
                try:
                    # 保存完整的返回结果
                    complete_result = calculate_complete_descent_profile(
                        cruise_fl=cruise_fl,
                        target_fl=target_fl,
                        aircraft_mass=aircraft_mass,
                        descent_mach=descent_mach,
                        high_cas=high_cas,
                        ac_model=ac_model,
                        low_cas=low_cas,
                        low_cas_fl=low_cas_fl,
                        print_details=False
                    )
                    
                    # 解包返回的结果
                    _, Param, _, df, _ = complete_result
                    
                    # 提取关键下降参数
                    descent_distance = Param['Descent Distance (nm)']
                    descent_time = Param['Descent Time (s)']
                    
                    # 计算总飞行时间
                    cruise_distance = standard_route_length - descent_distance
                    cruise_time = cruise_distance / gs * 3600  # 转换为秒
                    total_flight_time = cruise_time + descent_time
                    
                    # 计算与目标RTA的差值
                    diff = abs(total_flight_time - target_rta)
                    
                    # 将结果添加到列表，包括完整的参数和数据框
                    results.append({
                        'mach': descent_mach,
                        'high_cas': high_cas,
                        'low_cas': low_cas,
                        'low_cas_fl': low_cas_fl,
                        'low_cas_desc': low_cas_desc,
                        'descent_distance': descent_distance,
                        'descent_time': descent_time,
                        'cruise_time': cruise_time,
                        'total_time_sec': total_flight_time,
                        'total_time_min': total_flight_time / 60,
                        'diff_sec': diff,
                        'param': Param,    # 保存完整参数
                        'df': df           # 保存完整下降数据
                    })
                    
                except Exception as e:
                    pass  # 安静地忽略错误，专注于找到匹配的剖面

    # 找出与目标RTA差值在容忍范围内的所有配置
    matching_profiles = [r for r in results if r['diff_sec'] <= tolerance]
    
    # 按差值排序
    matching_profiles.sort(key=lambda x: x['diff_sec'])
    
    if matching_profiles:
        print("符合条件的飞行剖面：")
        print("排名  Mach  High CAS  低速CAS  低速FL  总飞行时间(秒)  总飞行时间(分钟)  配置描述        差值(秒)")
        print("----  ----  --------  ------  ------  --------------  ----------------  --------        --------")
        
        for i, profile in enumerate(matching_profiles, 1):
            print(f"{i:<5} {profile['mach']:.2f}  {profile['high_cas']:<8} {profile['low_cas']:<7} {profile['low_cas_fl']:<7} {profile['total_time_sec']:.2f}         {profile['total_time_min']:.2f}             {profile['low_cas_desc']}    {profile['diff_sec']:.2f}")
        
        best_match = matching_profiles[0]
        print("\n最佳匹配的配置是：")
        print(f"- Mach: {best_match['mach']}")
        print(f"- High CAS: {best_match['high_cas']}节")
        print(f"- 低速配置: {best_match['low_cas_desc']} (low_cas={best_match['low_cas']}, low_cas_fl={best_match['low_cas_fl']})")
        print(f"- 总飞行时间: {best_match['total_time_sec']:.2f}秒 ({best_match['total_time_min']:.2f}分钟)")
        print(f"- 与目标RTA差值: {best_match['diff_sec']:.2f}秒")
        
        # 返回最佳匹配的配置以及详细的参数和数据框
        return best_match, best_match['param'], best_match['df']
    else:
        # 找出最接近的配置
        results.sort(key=lambda x: x['diff_sec'])
        closest_match = results[0]
        
        print(f"未找到与目标RTA差值在{tolerance}秒以内的配置")
        print(f"最接近的配置与目标相差 {closest_match['diff_sec']:.2f}秒:")
        print(f"- Mach: {closest_match['mach']}")
        print(f"- High CAS: {closest_match['high_cas']}节")
        print(f"- 低速配置: {closest_match['low_cas_desc']} (low_cas={closest_match['low_cas']}, low_cas_fl={closest_match['low_cas_fl']})")
        print(f"- 总飞行时间: {closest_match['total_time_sec']:.2f}秒 ({closest_match['total_time_min']:.2f}分钟)")
        
        # 返回最接近的配置以及详细的参数和数据框
        return closest_match, closest_match['param'], closest_match['df']