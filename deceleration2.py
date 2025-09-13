import math
import pandas as pd
from pyBADA.bada4 import Bada4Aircraft, BADA4, Airplane, atm, conv

# 固定的BADA配置
bada_version = "4.2"
filepath = "/home/longqin/Downloads/4.2/BADA_4.2_L06514UPC/Models"

# 飞机配置参数
ac_model = "A320-232"  # 飞机型号
aircraft_mass = 60000  # 飞机质量(kg)
DeltaTemp = 0  # 温度偏差(ISA+0)

# 初始化飞机模型
AC = Bada4Aircraft(
    badaVersion=bada_version,
    acName=ac_model,
    filePath=filepath,
)

# 创建BADA4性能计算对象
bada4 = BADA4(AC)

def calculate_performance_parameters(flight_level=110, cas_kt=280, esf_values=None):
    """计算指定高度和CAS下不同ESF值对应的性能参数
    
    Args:
        flight_level: 飞行高度层
        cas_kt: 校准空速(kt)
        esf_values: 要计算的ESF值列表
    """
    if esf_values is None:
        esf_values = [0.0, 0.1, 0.2, 0.3, 0.4]
    
    # 高度转换
    altitude_ft = flight_level * 100
    altitude_m = conv.ft2m(altitude_ft)
    
    # 计算大气参数
    theta_val, delta_val, sigma_val = atm.atmosphereProperties(altitude_m, DeltaTemp)
    
    # 设置速度
    cas = conv.kt2ms(cas_kt)
    tas = atm.cas2Tas(cas, delta_val, sigma_val)
    M = atm.tas2Mach(tas, theta_val)
    
    # 计算升力系数
    cl = bada4.CL(delta=delta_val, mass=aircraft_mass, M=M)
    
    # 计算阻力系数(干净构型)
    HLid = 0.0  # 无襟翼
    LG = "LGUP"  # 起落架收起
    cd = bada4.CD(HLid=HLid, LG=LG, CL=cl, M=M)
    
    # 计算阻力
    drag = bada4.D(delta=delta_val, M=M, CD=cd)
    
    # 计算怠速推力
    idle_thrust = bada4.Thrust(
        delta=delta_val,
        theta=theta_val,
        M=M,
        rating="LIDL",  # 怠速设置
        DeltaTemp=DeltaTemp
    )
    
    # 计算净推力 (通常为负值，表示净阻力)
    net_thrust = idle_thrust - drag
    
    results = []
    
    for esf in esf_values:
        # 计算给定ESF下的下降率
        descent_rate = bada4.ROCD(
            T=idle_thrust,
            D=drag,
            v=tas,
            mass=aircraft_mass,
            ESF=esf,  # 使用给定的ESF值
            h=altitude_m,
            DeltaTemp=DeltaTemp
        )
        
        # 计算下降角
        if tas > 0 and abs(descent_rate) > 0.01:
            descent_angle_rad = math.asin(descent_rate / tas)
            descent_angle_deg = math.degrees(descent_angle_rad)
        else:
            descent_angle_rad = 0
            descent_angle_deg = 0
        
        # 计算TAS减速率
        # 能量平衡: m*v*dv/dt + m*g*dh/dt = (T-D)*v
        # 重新排列求解 dv/dt:
        # dv/dt = [(T-D)*v - m*g*dh/dt] / (m*v)
        
        # 计算TAS减速率 - 基本物理原理保持不变
        # 能量平衡: m*v*dv/dt + m*g*dh/dt = (T-D)*v
        # 重新排列求解 dv/dt:
        # dv/dt = [(T-D)*v - m*g*dh/dt] / (m*v)

        # 计算TAS减速率 (这部分基本正确)
        term1 = net_thrust / aircraft_mass
        term2 = -9.80665 * descent_rate / tas if tas > 0 else 0
        tas_deceleration_ms2 = term1 + term2

        # 使用pyBADA库的逻辑计算CAS减速率
        # 方法1：通过数值微分估计
        # 计算当前状态的CAS
        current_cas = atm.tas2Cas(tas, delta_val, sigma_val)


        # 估计略高一点的高度和TAS下的CAS
        altitude_delta = 1.0  # 1米高度差
        new_alt = altitude_m - altitude_delta  # 下降
        new_theta, new_delta, new_sigma = atm.atmosphereProperties(new_alt, DeltaTemp)
        new_tas = tas + tas_deceleration_ms2 * 1.0  # 1秒后的TAS
        new_cas = atm.tas2Cas(new_tas, new_delta, new_sigma)

        # 估计CAS减速率
        cas_deceleration_ms2 = (new_cas - current_cas) / 1.0  # 每秒变化率

        # 转换为节/秒
        cas_deceleration_kts = cas_deceleration_ms2 / 0.514444
                
        results.append({
            "ESF": esf,
            "TAS(kt)": round(conv.ms2kt(tas), 1),
            "马赫数": round(M, 3),
            "下降率(ft/min)": round(descent_rate * 196.85, 0),
            "下降角(度)": round(descent_angle_deg, 2),
            # "TAS减速率(kt/s)": round(tas_deceleration_kts, 3),
            # "TAS减速率(kt/min)": round(tas_deceleration_kts * 60, 1),
            "CAS减速率(kt/s)": round(cas_deceleration_kts, 3),
            "CAS减速率(kt/min)": round(cas_deceleration_kts * 60, 1),
            "阻力(N)": round(drag, 0),
            "怠速推力(N)": round(idle_thrust, 0),
            "净推力(N)": round(net_thrust, 0)
        })
    
    # 转换为DataFrame并打印
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)
    df = pd.DataFrame(results)
    print(f"飞机型号: {ac_model}")
    print(f"飞机质量: {aircraft_mass} kg")
    print(f"FL{flight_level}高度、{cas_kt}节CAS下不同ESF值对应的性能参数:")
    print(df.to_string(index=False))
    
    return results

if __name__ == "__main__":
    # 计算FL110、CAS 280节情况下不同ESF值对应的性能参数
    calculate_performance_parameters(100, 280)