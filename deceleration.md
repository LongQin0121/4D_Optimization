# 两种 CAS 减速率计算方法对比

## TAS 减速率计算（两方法相同）

两种方法使用了相同的 **TAS 减速率计算**，都基于基本的力学原理：

```python
term1 = net_thrust / aircraft_mass
term2 = -9.80665 * descent_rate / tas if tas > 0 else 0
tas_deceleration_ms2 = term1 + term2
```

### CAS 减速率计算（两种不同方法）
1. 理论热力学公式法

使用大气物理公式直接计算：
```python
dsigma_dh_precise = (1/2) * math.sqrt(sigma) * ((g_value/(temp_gradient * R_value)) - 1) * (-temp_gradient/temp)
cas_term1 = math.sqrt(sigma) * tas_deceleration_ms2
cas_term2 = tas * dsigma_dh_precise * descent_rate
cas_deceleration_ms2 = cas_term1 + cas_term2
```

### 2. 数值微分法（使用 pyBADA 函数）

使用 pyBADA 的转换函数进行数值微分：
```python
current_cas = atm.tas2Cas(tas, delta_val, sigma_val)
altitude_delta = 1.0  # 1 米高度差
new_alt = altitude_m - altitude_delta  # 下降
new_theta, new_delta, new_sigma = atm.atmosphereProperties(new_alt, DeltaTemp)

new_tas = tas + tas_deceleration_ms2 * 1.0  # 1 秒后的 TAS
new_cas = atm.tas2Cas(new_tas, new_delta, new_sigma)

cas_deceleration_ms2 = (new_cas - current_cas) / 1.0  # 每秒变化率

```

| 特点        | 理论公式法               | 数值微分法                  |
| --------- | ------------------- | ---------------------- |
| **准确性**   | 依赖于理论公式的精确性         | 依赖于 pyBADA 转换函数的精确性和步长 |
| **一致性**   | 可能与 pyBADA 内部模型略有差异 | 与 pyBADA 其他计算完全一致      |
| **计算效率**  | 较高（单次计算）            | 较低（多次函数调用）             |
| **实现复杂度** | 需要理解复杂的热力学关系        | 概念简单，但需小心选择步长          |

推荐选择
在与pyBADA库集成的应用中，推荐使用第二种方法(数值微分法)，因为：

确保与pyBADA库其他部分的计算一致性
直接利用pyBADA的大气模型处理边界条件和特殊情况
避免因理论简化导致的潜在误差
建议使用场景：

如果您的代码已经深度集成了pyBADA库，使用数值微分法保持一致性更好
如果计算效率是关键因素，或者您需要更透明的计算过程，使用理论公式法
![alt text](be146a4b-10f4-41a2-ad62-64069dd7cf9a.png)
![alt text](8d30ce0d-610e-4971-b62b-1c0026210afb.png)

### TAS和CAS减速率关系分析
两种方法确实都以TAS减速率(加速度)为基础，然后通过不同途径计算CAS减速率：


共同起点：TAS减速率计算
两种方法使用完全相同的方程计算TAS减速率：
```python
dV_TAS/dt = (T-D)/m - g·(dh/dt)/V_TAS
```
这个公式来自基本的力学原理和能量守恒定律。
##### 不同的CAS减速率计算方法
方法1：理论推导法

直接使用TAS减速率作为输入
通过理论公式计算：
```
dV_CAS/dt = √σ·dV_TAS/dt + V_TAS·(d√σ/dh)·(dh/dt)
```
这是一个基于链式法则的解析解

方法2：数值估计法

也使用TAS减速率作为输入
但是通过"模拟"一小段时间后的状态来估计：

计算当前CAS
预测Δt秒后的TAS：new_tas = tas + dV_TAS/dt × Δt
计算新高度下对应的CAS
通过差分近似导数：dV_CAS/dt ≈ (new_cas - current_cas)/Δt

主要区别总结

两种方法都依赖于先计算TAS减速率
方法1直接应用微分公式从TAS减速率推导CAS减速率
方法2通过模拟预测和数值微分来估计CAS减速率

这种共同基础解释了为什么两种方法在大多数情况下给出相似的结果，因为它们使用相同的物理模型计算基础的TAS减速率，只是从TAS减速率到CAS减速率的转换方法不同。Retry