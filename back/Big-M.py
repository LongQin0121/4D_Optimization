import pyomo.environ as pyo

def demonstrate_separation_constraint():
    """
    演示Big-M方法如何处理飞机分离约束
    核心思想：|RTA_i - RTA_j| >= t_sep 转换为线性约束
    """
    
    # 创建简单模型：只有2架飞机
    model = pyo.ConcreteModel()
    
    # 参数
    t_sep = 120  # 分离时间：120秒
    big_M = 500  # Big-M值
    
    # 决策变量
    model.RTA_A = pyo.Var(domain=pyo.NonNegativeReals, bounds=(900, 1200))
    model.RTA_B = pyo.Var(domain=pyo.NonNegativeReals, bounds=(1000, 1300))
    model.B_AB = pyo.Var(domain=pyo.Binary)  # B_AB=1表示A先于B到达
    
    print("=" * 60)
    print("Big-M分离约束演示")
    print("=" * 60)
    print(f"分离时间要求: {t_sep}秒")
    print(f"Big-M值: {big_M}")
    print()
    
    print("原始非线性约束：")
    print("  |RTA_A - RTA_B| >= 120")
    print()
    
    print("转换后的线性约束：")
    print("  约束1: RTA_A + 120 <= RTA_B + M * (1 - B_AB)")
    print("  约束2: RTA_B + 120 <= RTA_A + M * B_AB")
    print()
    
    # 分离约束
    model.sep_constraint_1 = pyo.Constraint(
        expr=model.RTA_A + t_sep <= model.RTA_B + big_M * (1 - model.B_AB)
    )
    
    model.sep_constraint_2 = pyo.Constraint(
        expr=model.RTA_B + t_sep <= model.RTA_A + big_M * model.B_AB
    )
    
    print("逻辑分析：")
    print()
    print("情况1: B_AB = 1 (飞机A先到达)")
    print("  约束1变为: RTA_A + 120 <= RTA_B + 500*0 = RTA_B  ✓ 激活")
    print("  约束2变为: RTA_B + 120 <= RTA_A + 500*1 = RTA_A + 500  ✓ 自动满足")
    print("  结果: 强制 RTA_A + 120 <= RTA_B")
    print()
    
    print("情况2: B_AB = 0 (飞机B先到达)")  
    print("  约束1变为: RTA_A + 120 <= RTA_B + 500*1 = RTA_B + 500  ✓ 自动满足")
    print("  约束2变为: RTA_B + 120 <= RTA_A + 500*0 = RTA_A  ✓ 激活")
    print("  结果: 强制 RTA_B + 120 <= RTA_A")
    print()
    
    # 测试不同的B_AB值
    test_scenarios = [
        ("A先到达", 1, 1000, 1150),  # A=1000, B=1150, 间隔150>120 ✓
        ("B先到达", 0, 1150, 1000),  # A=1150, B=1000, 间隔150>120 ✓
    ]
    
    print("=" * 60)
    print("约束验证测试")
    print("=" * 60)
    
    for scenario, b_val, rta_a, rta_b in test_scenarios:
        print(f"\n测试场景: {scenario}")
        print(f"  B_AB = {b_val}")
        print(f"  RTA_A = {rta_a}, RTA_B = {rta_b}")
        print(f"  实际间隔: |{rta_a} - {rta_b}| = {abs(rta_a - rta_b)}")
        
        # 验证约束1
        lhs1 = rta_a + t_sep
        rhs1 = rta_b + big_M * (1 - b_val)
        constraint1_satisfied = lhs1 <= rhs1
        
        # 验证约束2  
        lhs2 = rta_b + t_sep
        rhs2 = rta_a + big_M * b_val
        constraint2_satisfied = lhs2 <= rhs2
        
        print(f"  约束1: {lhs1} <= {rhs1} → {'✓' if constraint1_satisfied else '✗'}")
        print(f"  约束2: {lhs2} <= {rhs2} → {'✓' if constraint2_satisfied else '✗'}")
        
        if constraint1_satisfied and constraint2_satisfied:
            print(f"  结果: 所有约束满足 ✓")
        else:
            print(f"  结果: 约束违反 ✗")

def show_big_m_calculation():
    """演示如何计算合适的Big-M值"""
    
    print("\n" + "=" * 60)
    print("Big-M值计算方法")
    print("=" * 60)
    
    # 示例飞机时间窗
    aircraft_windows = {
        'A': {'ETA': 900, 'LTA': 1200},
        'B': {'ETA': 1000, 'LTA': 1300},
        'C': {'ETA': 1100, 'LTA': 1400}
    }
    
    print("飞机时间窗：")
    for aircraft, window in aircraft_windows.items():
        print(f"  飞机{aircraft}: [{window['ETA']}, {window['LTA']}]")
    
    print(f"\nBig-M计算公式：")
    print(f"  M_ij = max{{LTA_i - ETA_j, LTA_j - ETA_i}}")
    print()
    
    aircraft_list = list(aircraft_windows.keys())
    for i in range(len(aircraft_list)):
        for j in range(i+1, len(aircraft_list)):
            ac_i, ac_j = aircraft_list[i], aircraft_list[j]
            
            lta_i = aircraft_windows[ac_i]['LTA']
            eta_i = aircraft_windows[ac_i]['ETA']
            lta_j = aircraft_windows[ac_j]['LTA'] 
            eta_j = aircraft_windows[ac_j]['ETA']
            
            option1 = lta_i - eta_j
            option2 = lta_j - eta_i
            big_m = max(option1, option2)
            
            print(f"M_{ac_i}{ac_j}:")
            print(f"  选项1: LTA_{ac_i} - ETA_{ac_j} = {lta_i} - {eta_j} = {option1}")
            print(f"  选项2: LTA_{ac_j} - ETA_{ac_i} = {lta_j} - {eta_i} = {option2}")
            print(f"  Big-M = max{{{option1}, {option2}}} = {big_m}")
            print()
    
    print("Big-M选择原则：")
    print("  ✓ 足够大：确保非激活约束自动满足")
    print("  ✓ 足够小：避免数值不稳定")
    print("  ✓ 基于时间窗：M = max{LTA_i - ETA_j, LTA_j - ETA_i}")

if __name__ == "__main__":
    demonstrate_separation_constraint()
    show_big_m_calculation()