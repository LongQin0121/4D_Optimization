from pyBADA.bada4 import Bada4Aircraft, BADA4
import pyBADA.atmosphere as atm
import pyBADA.conversions as conv

def mach2tas_kt(flight_level, mach, delta_temp=0):
    """
    Simple function to calculate True Airspeed (TAS) from flight level and Mach number
    
    Parameters:
    flight_level: Flight level (FL)
    mach: Mach number
    delta_temp: Temperature deviation from ISA, default is 0
    
    Returns:
    float: True airspeed (TAS) in knots
    """

    # Calculate altitude in meters
    altitude_ft = flight_level * 100
    altitude_m = conv.ft2m(altitude_ft)
    
    # Calculate atmospheric properties
    theta_val, delta_val, sigma_val = atm.atmosphereProperties(altitude_m, delta_temp)
    
    # Calculate true airspeed (TAS)
    tas_ms = atm.mach2Tas(mach, theta_val)
    tas_kt = conv.ms2kt(tas_ms)
    
    return tas_kt

import matplotlib.pyplot as plt
import numpy as np

def plot_descent_profile_with_dual_xaxis(standard_route_length, descent_distance, cumulative_distance, 
                                        altitude_ft, cumulative_time, mach, cas_kt, tas_kt, 
                                        cruise_fl=370, figsize=(12, 10)):
    """
    绘制飞机下降轨迹图（双x轴：距离和时间）
    """
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
    
    # Calculate cruise distance
    cruise_distance = standard_route_length - descent_distance
    
    # Create distance array for cruise segment
    cruise_x = np.array([-standard_route_length, -descent_distance])
    cruise_alt = np.array([cruise_fl * 100, cruise_fl * 100])
    
    # Adjust descent profile x-coordinates to end at target (0)
    descent_x = cumulative_distance - descent_distance
    
    # 正确转换时间：每个点的时间 = cumulative_time - total_descent_time
    total_descent_time = cumulative_time.iloc[-1]
    relative_time = cumulative_time - total_descent_time
    
    # Plot 1: Altitude Profile
    ax1.plot(cruise_x, cruise_alt, color = 'brown', linewidth=2, label='Cruise')
    ax1.plot(descent_x, altitude_ft, 'r-', linewidth=2, label='Descent',marker='o', markersize=2)
    ax1.set_ylabel('Altitude (ft)', fontsize=12)
    ax1.set_title('Aircraft Descent Profile (i4D FMS)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # 设置下方距离轴范围
    ax1.set_xlim(-standard_route_length, 0)
    
    # 创建上方时间轴 - 关键：确保完全对齐
    ax1_time = ax1.twiny()
    
    # 明确设置时间轴的范围，确保与距离轴完全一致
    ax1_time.set_xlim(-standard_route_length, 0)
    
    # 设置下方距离轴标签
    ax1.set_xlabel('Distance to Target (nm)', fontsize=12)
    
    # 简单直接找关键点
    time_positions = []
    time_labels = []
    
    # 1. 第一个点（下降开始）
    first_idx = 0
    time_positions.append(descent_x.iloc[first_idx])
    time_labels.append(f'{relative_time.iloc[first_idx]:.0f}')
    
    # 2. 最后一个点（目标点）
    last_idx = len(altitude_ft) - 1
    time_positions.append(descent_x.iloc[last_idx])
    time_labels.append('0')
    
    # 3. 特殊高度点：30000, 25000, 20000, 15000, 10000 ft
    special_altitudes = [30000, 25000, 20000, 15000, 10000]
    
    for target_alt in special_altitudes:
        closest_idx = np.argmin(np.abs(altitude_ft - target_alt))
        
        if (altitude_ft.iloc[closest_idx] <= altitude_ft.iloc[0] and 
            altitude_ft.iloc[closest_idx] >= altitude_ft.iloc[-1] and
            closest_idx not in [0, len(altitude_ft)-1]):
            time_positions.append(descent_x.iloc[closest_idx])
            time_labels.append(f'{relative_time.iloc[closest_idx]:.0f}')
    
    # 按距离位置排序（从左到右）
    sorted_pairs = sorted(zip(time_positions, time_labels))
    time_positions, time_labels = zip(*sorted_pairs)
    
    # 调试：打印时间轴刻度位置
    print("时间轴刻度位置：", time_positions)
    print("时间轴刻度标签：", time_labels)
    
    # 设置时间轴刻度 - 确保精确对应
    ax1_time.set_xticks(time_positions)
    ax1_time.set_xticklabels(time_labels)
    ax1_time.set_xlabel('Time to Target (seconds)', fontsize=12, color='orange')
    ax1_time.tick_params(axis='x', labelcolor='orange')
    
    # Plot 2: Speed Profile
    ax2.plot(descent_x, mach, 'g-', linewidth=2, label='Mach', marker='o', markersize=3)
    ax2.plot(descent_x, cas_kt/100, 'b-', linewidth=2, label='CAS (kt/100)', marker='s', markersize=3)
    ax2.plot(descent_x, tas_kt/100, 'purple', linewidth=2, label='TAS (kt/100)', marker='^', markersize=3)
    
    ax2.set_xlabel('Distance to Target (nm)', fontsize=12)
    ax2.set_ylabel('Speed (Mach / kt/100)', fontsize=12)
    ax2.set_title('Speed Profile During Descent', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Set x-axis limits for ax2
    ax2.set_xlim(-standard_route_length, 0)
    
    # Add vertical lines
    ax1.axvline(x=-descent_distance, color='k', linestyle='--', alpha=0.5)
    ax2.axvline(x=-descent_distance, color='k', linestyle='--', alpha=0.5)
    # ax1.axvline(x=0, color='red', linestyle='-', alpha=0.7)
    # ax2.axvline(x=0, color='red', linestyle='-', alpha=0.7)
    
    # 标注
    target_alt = altitude_ft.iloc[-1]
    actual_end_x = descent_x.iloc[-1]
    
    ax1.annotate(f'Target\n{actual_end_x:.1f} nm / 0s\nFL{int(target_alt/100)}', 
                xy=(actual_end_x, target_alt), 
                xytext=(actual_end_x + 15, target_alt + 2000),
                fontsize=10, ha='center',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral", alpha=0.7),
                arrowprops=dict(arrowstyle='->', color='red', alpha=0.7))
    
    # 其他标注
    cruise_mid_x = (-standard_route_length + -descent_distance) / 2
    ax1.text(cruise_mid_x, cruise_fl * 100 - 12000, 
            f'Cruise: {cruise_distance:.1f} nm', 
            ha='center', va='bottom', fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7))
    
    descent_mid_x = -descent_distance / 2
    descent_mid_alt = (cruise_fl * 100 + target_alt) / 2
    ax1.text(descent_mid_x, descent_mid_alt + 12000, 
            f'Descent: {descent_distance:.1f} nm\n{total_descent_time:.0f}s duration', 
            ha='center', va='center', fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.7))
    
    plt.tight_layout()
    
    return fig, ax1, ax2

def plot_from_summary_and_df_with_dual_xaxis(summary, df, standard_route_length=200, cruise_fl=370, figsize=(12, 10)):
    """
    直接从summary和df绘制图表的便捷函数（双x轴）
    """
    
    return plot_descent_profile_with_dual_xaxis(
        standard_route_length=standard_route_length,
        descent_distance=summary['Descent Distance (nm)'],
        cumulative_distance=df['Cumulative Distance(nm)'],
        altitude_ft=df['Altitude(ft)'],
        cumulative_time=df['Cumulative Time(s)'],
        mach=df['Mach'],
        cas_kt=df['CAS(kt)'],
        tas_kt=df['TAS(kt)'],
        cruise_fl=cruise_fl,
        figsize=figsize
    )