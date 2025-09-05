import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import pandas as pd

def create_aircraft_scheduling_model():
    """
    创建5架飞机调度的MILP模型
    目标：最小化与计划时间的偏差，同时满足分离约束
    """
    
    # 示例数据：5架飞机的时间信息（单位：秒）
    aircraft_data = {
        'A': {'STA': 1000, 'ETA': 900, 'LTA': 1200},
        'B': {'STA': 1100, 'ETA': 1000, 'LTA': 1300}, 
        'C': {'STA': 1200, 'ETA': 1100, 'LTA': 1400},
        'D': {'STA': 1300, 'ETA': 1200, 'LTA': 1500},
        'E': {'STA': 1400, 'ETA': 1300, 'LTA': 1600}
    }
    
    # 分离时间要求
    t_sep = 120  # 120秒
    
    # 创建模型
    model = pyo.ConcreteModel()
    
    # ==================== 集合定义 ====================
    model.aircraft = pyo.Set(initialize=aircraft_data.keys())
    
    # 创建飞机对集合 (i < j)
    aircraft_pairs = []
    aircraft_list = list(aircraft_data.keys())
    for i in range(len(aircraft_list)):
        for j in range(i+1, len(aircraft_list)):
            aircraft_pairs.append((aircraft_list[i], aircraft_list[j]))
    
    model.aircraft_pairs = pyo.Set(initialize=aircraft_pairs)
    
    # ==================== 参数定义 ====================
    model.STA = pyo.Param(model.aircraft, initialize={i: aircraft_data[i]['STA'] for i in aircraft_data})
    model.ETA = pyo.Param(model.aircraft, initialize={i: aircraft_data[i]['ETA'] for i in aircraft_data})
    model.LTA = pyo.Param(model.aircraft, initialize={i: aircraft_data[i]['LTA'] for i in aircraft_data})
    model.t_sep = pyo.Param(initialize=t_sep)
    
    # 计算Big-M值
    def calculate_big_M(model, i, j):
        return max(model.LTA[i] - model.ETA[j], model.LTA[j] - model.ETA[i])
    
    model.big_M = pyo.Param(model.aircraft_pairs, initialize=lambda model, i, j: calculate_big_M(model, i, j))
    
    # ==================== 决策变量 ====================
    # 实际到达时间
    model.RTA = pyo.Var(model.aircraft, domain=pyo.NonNegativeReals)
    
    # 二进制变量：B[i,j] = 1 表示飞机i先于飞机j到达
    model.B = pyo.Var(model.aircraft_pairs, domain=pyo.Binary)
    
    # 偏差变量（用于线性化绝对值）
    model.dev_pos = pyo.Var(model.aircraft, domain=pyo.NonNegativeReals)  # 正偏差
    model.dev_neg = pyo.Var(model.aircraft, domain=pyo.NonNegativeReals)  # 负偏差
    
    # ==================== 目标函数 ====================
    def objective_rule(model):
        return sum(model.dev_pos[i] + model.dev_neg[i] for i in model.aircraft)
    
    model.objective = pyo.Objective(rule=objective_rule, sense=pyo.minimize)
    
    # ==================== 约束条件 ====================
    
    # 1. 时间窗约束
    def time_window_lower_rule(model, i):
        return model.ETA[i] <= model.RTA[i]
    
    def time_window_upper_rule(model, i):
        return model.RTA[i] <= model.LTA[i]
    
    model.time_window_lower = pyo.Constraint(model.aircraft, rule=time_window_lower_rule)
    model.time_window_upper = pyo.Constraint(model.aircraft, rule=time_window_upper_rule)
    
    # 2. 绝对值线性化约束
    def deviation_rule(model, i):
        return model.RTA[i] - model.STA[i] == model.dev_pos[i] - model.dev_neg[i]
    
    model.deviation_constraint = pyo.Constraint(model.aircraft, rule=deviation_rule)
    
    # 3. 分离约束（Big-M方法）
    def separation_constraint_1_rule(model, i, j):
        # 如果B[i,j] = 1，则 RTA[i] + t_sep <= RTA[j]
        return model.RTA[i] + model.t_sep <= model.RTA[j] + model.big_M[i,j] * (1 - model.B[i,j])
    
    def separation_constraint_2_rule(model, i, j):
        # 如果B[i,j] = 0，则 RTA[j] + t_sep <= RTA[i]
        return model.RTA[j] + model.t_sep <= model.RTA[i] + model.big_M[i,j] * model.B[i,j]
    
    model.separation_1 = pyo.Constraint(model.aircraft_pairs, rule=separation_constraint_1_rule)
    model.separation_2 = pyo.Constraint(model.aircraft_pairs, rule=separation_constraint_2_rule)
    
    return model, aircraft_data

def solve_and_display_results(model, aircraft_data):
    """求解模型并展示结果"""
    
    # 选择求解器（需要安装CPLEX、Gurobi或其他MILP求解器）
    # 这里使用免费的GLPK求解器作为示例
    try:
        solver = SolverFactory('glpk')  # 或者 'cplex', 'gurobi'
        results = solver.solve(model, tee=True)
        
        # 检查求解状态
        if results.solver.termination_condition == pyo.TerminationCondition.optimal:
            print("\n" + "="*50)
            print("求解成功！找到最优解")
            print("="*50)
            
            # 展示结果
            print(f"\n目标函数值（总偏差）: {pyo.value(model.objective):.2f} 秒")
            
            print("\n飞机到达时间安排:")
            print("-" * 60)
            print(f"{'飞机':<6} {'计划(STA)':<12} {'实际(RTA)':<12} {'偏差':<10} {'时间窗'}")
            print("-" * 60)
            
            for aircraft in model.aircraft:
                sta = aircraft_data[aircraft]['STA']
                eta = aircraft_data[aircraft]['ETA'] 
                lta = aircraft_data[aircraft]['LTA']
                rta = pyo.value(model.RTA[aircraft])
                deviation = rta - sta
                
                print(f"{aircraft:<6} {sta:<12} {rta:<12.1f} {deviation:+8.1f} {'['+str(eta)+','+str(lta)+']'}")
            
            print("\n飞机到达顺序:")
            print("-" * 40)
            
            # 按RTA排序显示
            aircraft_schedule = [(aircraft, pyo.value(model.RTA[aircraft])) 
                               for aircraft in model.aircraft]
            aircraft_schedule.sort(key=lambda x: x[1])
            
            for i, (aircraft, rta) in enumerate(aircraft_schedule):
                print(f"{i+1}. 飞机{aircraft}: {rta:.1f}秒")
                if i < len(aircraft_schedule) - 1:
                    gap = aircraft_schedule[i+1][1] - rta
                    print(f"   -> 与下一架飞机间隔: {gap:.1f}秒 {'✓' if gap >= 120 else '✗'}")
            
            print("\n二进制变量值（飞机优先级）:")
            print("-" * 30)
            for i, j in model.aircraft_pairs:
                b_val = pyo.value(model.B[i,j])
                if b_val > 0.5:
                    print(f"飞机{i} 先于 飞机{j}")
                else:
                    print(f"飞机{j} 先于 飞机{i}")
                    
        else:
            print("求解失败！")
            print(f"终止条件: {results.solver.termination_condition}")
            
    except Exception as e:
        print(f"求解器错误: {e}")
        print("请确保安装了MILP求解器，如 GLPK: conda install -c conda-forge glpk")

def main():
    """主函数"""
    print("5架飞机调度问题 - MILP模型求解")
    print("="*50)
    
    # 创建模型
    model, aircraft_data = create_aircraft_scheduling_model()
    
    # 显示模型信息
    print(f"\n模型统计:")
    print(f"- 飞机数量: {len(model.aircraft)}")
    print(f"- 连续变量: {len(model.aircraft) * 3} 个 (RTA + 正负偏差)")
    print(f"- 二进制变量: {len(model.aircraft_pairs)} 个")
    print(f"- 约束条件: {len(model.aircraft)*3 + len(model.aircraft_pairs)*2} 个")
    print(f"- 分离时间要求: {pyo.value(model.t_sep)} 秒")
    
    print(f"\nBig-M 值:")
    for i, j in model.aircraft_pairs:
        print(f"M[{i},{j}] = {pyo.value(model.big_M[i,j])}")
    
    # 求解模型
    solve_and_display_results(model, aircraft_data)

if __name__ == "__main__":
    main()