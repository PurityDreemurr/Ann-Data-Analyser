# CAN 报文整理

## 说明

- 数据来源：`can_decode_config.json`、`sensor_dashboard_config.json`
- 离线超时：`offline_timeout_s = 3s`
- 本文以 **CAN 通道为上一级标题，CAN ID 为下一级小标题** 进行整理。
- 文中 ID 记法默认采用 **十六进制且省略 `0x` 前缀**，例如 `156` 表示 `0x156`，`232` 表示 `0x232`。
- `283`、`284`、`287`、`288` 为 **CAN1** 通道报文，其余为 **CAN3** 通道报文。
- 表中“展示名 / 状态说明”来自 `sensor_dashboard_config.json` 与补充材料；其余解析规则来自 `can_decode_config.json`。
- 另外参考了补充材料：`25D电控系统dbc文件汇总`、`模式选择0x55.wps`、`转向电机内置报文解析.docx`、`EBS CAN.xls`、`ECU156.png`。
- 下文中的“补充说明”仅写入这些材料里能够明确确认的信息。
- `scale`：缩放系数，表示原始值需要乘以的倍数。
- 当前这份资料涉及的报文中，`offset` 全部为 `0`，因此文档中不再单独保留该列。
- 当前常见换算可直接理解为：`物理值 = 原始值 × scale`。

## CAN1

### 184 - AMK_SetPoint_LF

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| AMK_bReserve | 保留位 | 未见明确位布局 |  |  |  |  | 汇总表提到存在 `AMK_bReserve` |
| AMK_blnverterOn | 逆变器使能 | 未见明确位布局 |  |  |  |  | 汇总表提到 `AMK_blnverterOn` |
| CAN_bdcon |  | 未见明确位布局 |  |  |  |  | 汇总表提到 `CAN_bdcon` |
| AMK_bEnable | 控制器使能 | 未见明确位布局 |  |  |  |  | 汇总表提到 `AMK_bEnable` |
| AMK_bErrorReset | 错误复位 | 未见明确位布局 |  |  |  |  | 汇总表提到 `AMK_bErrorReset` |
| AMK_Reserve | 保留位 | 未见明确位布局 |  |  |  |  | 汇总表提到 `AMK_Reserve` |
| AMK_TargetVelocity | 目标速度 | 未见明确位布局 |  |  |  |  | 汇总表提到 `AMK_TargetVelocity` |
| AMK_TotqueLimitPositiv | 正向扭矩限制 | 未见明确位布局 |  |  |  |  | 汇总表提到 `AMK_TotqueLimitPositiv` |
| AMK_TotqueLimitNegativ | 负向扭矩限制 | 未见明确位布局 |  |  |  |  | 汇总表提到 `AMK_TotqueLimitNegativ` |

补充说明：
- 信息来源：`25D电控系统dbc文件汇总/25d报文整理.xlsx`
- 汇总表注明 `184` 为左前电机的下发控制报文，通道为 `CAN1`。
- 语义包括：目标速度、反扭限制、正扭矩限制、电机使能、电机复位、逆变器控制。
- 当前补充材料未给出该报文的明确字节/位布局，因此这里只保留已确认的字段语义。

### 185 - AMK_SetPoint_RF

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| 同 184 | 右前电机控制报文 | 同 184 |  |  |  |  | 汇总表注明 185 对应右前 |

补充说明：
- 信息来源：`25D电控系统dbc文件汇总/25d报文整理.xlsx`
- 汇总表注明 `185` 为右前电机的下发控制报文，通道为 `CAN1`。
- 字段语义与 `184` 相同。

### 188 - AMK_SetPoint_RB

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| 同 184 | 右后电机控制报文 | 同 184 |  |  |  |  | 汇总表注明 188 对应右后 |

补充说明：
- 信息来源：`25D电控系统dbc文件汇总/25d报文整理.xlsx`
- 汇总表注明 `188` 为右后电机的下发控制报文，通道为 `CAN1`。
- 字段语义与 `184` 相同。

### 189 - AMK_SetPoint_LB

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| 同 184 | 左后电机控制报文 | 同 184 |  |  |  |  | 汇总表注明 189 对应左后 |

补充说明：
- 信息来源：`25D电控系统dbc文件汇总/25d报文整理.xlsx`
- 汇总表注明 `189` 为左后电机的下发控制报文，通道为 `CAN1`。
- 字段语义与 `184` 相同。

### * 283 - AMK_ActualValue1_LF

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| status_lf | LF 电机状态 | start_byte=0, length=2 | little | uint16 | 1 |  | 121=待驶, 82=高压/使能失败, 129=低压正常, 1=已上高压 |
| velocity_lf | AMK_ActualVelocity | start_byte=2, length=2 | little | int16 | 1 |  | 电机转速 |
| torque_current_lf | AMK_TorqueCurrent | start_byte=4, length=2 | little | int16 | 1 |  | 扭矩电流 |
| magnetizing_current_lf | AMK_MagnetizingCurrent | start_byte=6, length=2 | little | int16 | 1 |  | 磁化电流 |

补充说明：
- 信息来源：`25D电控系统dbc文件汇总/25d报文整理.xlsx`
- 汇总表注明 `283（285）` 对应左前电机实际速度、实际扭矩等反馈，通道为 `CAN1`。

### * 284 - AMK_ActualValue1_RF

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| status_rf | RF 电机状态 | start_byte=0, length=2 | little | uint16 | 1 |  | 121=待驶, 82=高压/使能失败, 129=低压正常, 1=已上高压 |
| velocity_rf | AMK_ActualVelocity | start_byte=2, length=2 | little | int16 | 1 |  | 电机转速 |
| torque_current_rf | AMK_TorqueCurrent | start_byte=4, length=2 | little | int16 | 1 |  | 扭矩电流 |
| magnetizing_current_rf | AMK_MagnetizingCurrent | start_byte=6, length=2 | little | int16 | 1 |  | 磁化电流 |

补充说明：
- 信息来源：`25D电控系统dbc文件汇总/25d报文整理.xlsx`
- 汇总表注明 `284（286）` 对应右前电机反馈，通道为 `CAN1`。

### * 287 - AMK_ActualValue1_RB

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| status_rb | RB 电机状态 | start_byte=0, length=2 | little | uint16 | 1 |  | 121=待驶, 82=高压/使能失败, 129=低压正常, 1=已上高压 |
| velocity_rb | AMK_ActualVelocity | start_byte=2, length=2 | little | int16 | 1 |  | 电机转速 |
| torque_current_rb | AMK_TorqueCurrent | start_byte=4, length=2 | little | int16 | 1 |  | 扭矩电流 |
| magnetizing_current_rb | AMK_MagnetizingCurrent | start_byte=6, length=2 | little | int16 | 1 |  | 磁化电流 |

补充说明：
- 信息来源：`25D电控系统dbc文件汇总/25d报文整理.xlsx`
- 汇总表注明 `287（289）` 对应右后电机反馈，通道为 `CAN1`。

### * 288 - AMK_ActualValue1_LB

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| status_lb | LB 电机状态 | start_byte=0, length=2 | little | uint16 | 1 |  | 121=待驶, 82=高压/使能失败, 129=低压正常, 1=已上高压 |
| velocity_lb | AMK_ActualVelocity | start_byte=2, length=2 | little | int16 | 1 |  | 电机转速 |
| torque_current_lb | AMK_TorqueCurrent | start_byte=4, length=2 | little | int16 | 1 |  | 扭矩电流 |
| magnetizing_current_lb | AMK_MagnetizingCurrent | start_byte=6, length=2 | little | int16 | 1 |  | 磁化电流 |

补充说明：
- 信息来源：`25D电控系统dbc文件汇总/25d报文整理.xlsx`
- 汇总表注明 `288（290）` 对应左后电机反馈，通道为 `CAN1`。

## CAN3

### 000 - EPOS4_PDO_Start

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| raw_data | Start Optional Protocol | LEN=8 |  | 原始字节流 |  |  | 转向说明给出固定报文：`01 00 00 00 00 00 00 00` |

补充说明：
- 信息来源：`转向电机内置报文解析.docx`
- 转向说明文档中，`0x000` 为主控发往总线的启动报文，用于开启 EPOS4 PDO 映射通信。

### * 002 - EBS_Status

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| ebs_error | EBS_error | start_bit=0, bit_length=1 | little | uint, unsigned | 1 |  | 1=报错 |
| brake1_control | brake1_control | start_bit=1, bit_length=1 | little | uint, unsigned | 1 |  | 0=前路制动 |
| brake2_control | brake2_control | start_bit=2, bit_length=1 | little | uint, unsigned | 1 |  | 0=后路制动 |
| sdc_as | sdc_as | start_bit=3, bit_length=1 | little | uint, unsigned | 1 |  | 1=AS继电器闭合 |
| ebs_ready | ebs_ready | start_bit=4, bit_length=1 | little | uint, unsigned | 1 |  | 1=EBS准备好 |
| ecu_disconnected | EBS_RELAY_ERROR / ecu_disconnected | start_bit=5, bit_length=1 | little | uint, unsigned | 1 |  | DBC 与表格命名存在差异，需以现场定义为准 |
| pre_as_state | pre_AS_state | start_bit=8, bit_length=4 | little | uint, unsigned | 1 |  | 当前状态 |
| error_state_transition | error_state | start_bit=12, bit_length=4 | little | uint, unsigned | 1 |  | 接收到的错误状态，表格注明“不用显示” |
| bp_lose1 | bp_lose1 | start_bit=16, bit_length=1 | little | uint, unsigned | 1 |  | 前气路丢失标志 |
| bp_lose2 | bp_lose2 | start_bit=17, bit_length=1 | little | uint, unsigned | 1 |  | 后气路丢失标志 |
| bp_lose3 | bp_lose3 | start_bit=18, bit_length=1 | little | uint, unsigned | 1 |  | 左前油压丢失标志 |
| bp_lose4 | bp_lose4 | start_bit=19, bit_length=1 | little | uint, unsigned | 1 |  | 右前油压丢失标志 |
| bp_lose5 | bp_lose5 | start_bit=20, bit_length=1 | little | uint, unsigned | 1 |  | 左后油压丢失标志 |
| bp_lose6 | bp_lose6 | start_bit=21, bit_length=1 | little | uint, unsigned | 1 |  | 右后油压丢失标志 |
| air1_insufficient | air1_insuff | start_bit=24, bit_length=1 | little | uint, unsigned | 1 |  | 1=前气压不足 |
| air2_insufficient | air2_insuff | start_bit=25, bit_length=1 | little | uint, unsigned | 1 |  | 1=后气压不足 |
| air1_overpressure | air1_overpress | start_bit=26, bit_length=1 | little | uint, unsigned | 1 |  | 1=前气压过大 |
| air2_overpressure | air2_overpress | start_bit=27, bit_length=1 | little | uint, unsigned | 1 |  | 1=后气压过大 |
| air1_path_failure | path1_fail | start_bit=28, bit_length=1 | little | uint, unsigned | 1 |  | 1=前路制动失效 |
| air2_path_failure | path2_fail | start_bit=29, bit_length=1 | little | uint, unsigned | 1 |  | 1=后路制动失效 |
| circuit_error | circuit_error | start_bit=30, bit_length=1 | little | uint, unsigned | 1 |  | 1=报错 |
| timeout | timeout | start_bit=31, bit_length=1 | little | uint, unsigned | 1 |  | 1=超时 |

补充说明：
- 信息来源：`EBS CAN.xls`、`25D电控系统dbc文件汇总/ecures-孙广博.dbc`
- `EBS CAN.xls` 对 `0x002` 给出了更细的 bit 含义说明，上表已并入。
- DBC 中该报文名为 `EBS_State`，当前配置中名称为 `EBS_Status`，本质对应同一类状态报文。

### 020 - command

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| workstation_status | 工作站状态 | start_byte=0, length=1 | little | uint8 | 1 |  | 取自 `/command.dv_state`；代码写入 `toCAN3Msg20[0]`。常见状态映射：0低压，1有人高压，2无人高压，3无人准备，4无人行驶，5无人完赛，6无人急停，7缓停 |
| velocity_cmd | 目标速度 | start_byte=1, length=2 | little | int16（发送时按 `uint16_t` 组包） | 0.001 | m/s | 取自 `/command.speed`；先限制在 `-32.767 ~ 32.767`，再按 `raw = physical × 1000` 编码，低字节在 `byte1`，高字节在 `byte2` |
| angle_cmd | 目标转角 | start_byte=3, length=2 | little | int16（发送时按 `uint16_t` 组包） | 0.001 |  | 取自 `/command.angle`；先限制在 `-32.767 ~ 32.767`，再按 `raw = physical × 1000` 编码，低字节在 `byte3`，高字节在 `byte4` |
| reserved_5 | 保留字节 | start_byte=5, length=1 | little | uint8 | 1 |  | 当前源码未写入，保持初始化值 `0` |
| reserved_6 | 保留字节 | start_byte=6, length=1 | little | uint8 | 1 |  | 当前源码未写入，保持初始化值 `0` |
| sensor_state | 传感器状态 | start_byte=7, length=1 | little | uint8 | 1 |  | 若传感器未初始化则为 `0`；已初始化且无故障为 `1`；有故障时写入 `sensor_error` 错误码 |

补充说明：
- 信息来源：`/home/miaaaaaa/WS/src/can_26d/src/canNode.cpp`、`/home/miaaaaaa/WS/src/can_26d/src/can3Reader.cpp`、`/home/miaaaaaa/WS/src/can_26d/include/can_26d/canNode.hpp`
- `0x20` 为 `CAN3` 发送报文，DLC 固定为 `8`，在 `canWriteLogic()` 中通过 `writeCan3Frame(0x20, toCAN3Msg20, 8)` 周期发送。
- `byte0` 直接写入当前工作站状态；若已触发安全状态，则优先使用内部 `myDvState_` 的安全状态值。
- 速度和转角在源码中均按“小端 16 位有符号量 ×1000”方式编码，但组包时使用 `uint16_t` 承载原始二进制位模式。
- `byte5`、`byte6` 当前未被源码改写；由于发送缓冲区零初始化，因此默认发送 `0`。

### 021 - INSOutput

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| velocity_x | x 轴线速度 | start_byte=0, length=2 | little | int16（发送时按 `uint16_t` 组包） | 0.001 | m/s | 取自 `/INSOutput.liner_velocity.x`；源码直接乘以 `1000` 后组包，未额外截断 |
| velocity_y | y 轴线速度 | start_byte=2, length=2 | little | int16（发送时按 `uint16_t` 组包） | 0.001 | m/s | 取自 `/INSOutput.liner_velocity.y`；源码直接乘以 `1000` 后组包，未额外截断 |
| acceleration_x | x 轴线加速度 | start_byte=4, length=2 | little | int16（发送时按 `uint16_t` 组包） | 0.001 |  | 取自 `/INSOutput.liner_acceleration.x`；先限制在 `-32.767 ~ 32.767`，再按 `raw = physical × 1000` 编码 |
| acceleration_y | y 轴线加速度 | start_byte=6, length=2 | little | int16（发送时按 `uint16_t` 组包） | 0.001 |  | 取自 `/INSOutput.liner_acceleration.y`；先限制在 `-32.767 ~ 32.767`，再按 `raw = physical × 1000` 编码 |

补充说明：
- 信息来源：`/home/miaaaaaa/WS/src/can_26d/src/canNode.cpp`、`/home/miaaaaaa/WS/src/can_26d/src/can3Reader.cpp`
- `0x21` 为 `CAN3` 发送报文，DLC 固定为 `8`，在 `canWriteLogic()` 中通过 `writeCan3Frame(0x21, toCAN3Msg21, 8)` 周期发送。
- 四个量均按 16 位小端方式发送：每个字段低字节在前，高字节在后。
- 速度字段源码未调用 `clamp`；若上游值超出 `int16 × 0.001` 可表达范围，需以后续联调定义为准。

### 022 - INSOutput2

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| vehicle_speed | 当前车速 | start_byte=0, length=2 | little | uint16 | 0.001 | m/s | 由 `sqrt(vx² + vy²)` 计算得到，源码限制在 `0 ~ 65.535` 后按 `raw = physical × 1000` 编码 |
| yaw_rate | 横摆角速度 | start_byte=2, length=2 | little | int16（发送时按 `uint16_t` 组包） | 0.006666666666666667 | deg/s | 取自 `/INSOutput.angular_velocity.z`；先限制在 `-200 ~ 200`，再按 `raw = physical × 150` 编码，因此 `physical = raw / 150` |
| reserved_4_7 | 保留字节 | start_byte=4, length=4 | little | uint32 | 1 |  | 当前源码未写入 `byte4~7`，发送缓冲区零初始化，因此默认发送 `00 00 00 00` |

补充说明：
- 信息来源：`/home/miaaaaaa/WS/src/can_26d/src/canNode.cpp`、`/home/miaaaaaa/WS/src/can_26d/src/can3Reader.cpp`、`/home/miaaaaaa/WS/src/can_26d/include/can_26d/canNode.hpp`
- `0x22` 为 `CAN3` 发送报文，DLC 固定为 `8`，在 `canWriteLogic()` 中通过 `writeCan3Frame(0x22, toCAN3Msg22, 8)` 周期发送。
- 当前代码只显式写入前 4 个字节：`byte0-1` 为当前车速，`byte2-3` 为横摆角速度；`byte4-7` 未在回调中赋值。
- 由于 `toCAN3Msg22` 在头文件中以全 `0` 初始化，且源码未改写尾部 4 字节，因此当前实际发送的尾部固定为 `0`。

### * 096 - SteerEncoder

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| raw_angle |  | start_byte=3, length=2 | little | uint16 | 1 |  |  |

补充说明：
- 信息来源：`25D电控系统dbc文件汇总/25d报文整理.xlsx`、`25D电控系统dbc文件汇总/ecures-孙广博.dbc`
- 汇总表注明 `0x96` 为“转向编码”，链路备注为“can2收，can3发”。
- DBC `BO_ 150 ZHUANJIAOBIIANMAQI` 给出了转角相关定义：`ZHUANJIAO : 24|16@1+ (0.3516,0)`。
- 当前 `can_decode_config.json` 中 `096` 解析为 `raw_angle`（`start_byte=3, length=2`），若后续需要统一成物理转角，建议再确认 `raw_angle` 与 `ZHUANJIAO` 的换算关系。

### * 156 - ECU_msg

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| ecu_state | Statu_Flag | start_bit=0, bit_length=3 | little | uint, unsigned | 1 |  | 图片说明：0低压，1有人高压，2无人高压，3无人准备(AS READY)，4无人行驶(AS DRIVING)，5无人完成(AS FINISHED)，6无人制动(AS EMERGENCY) |
| ecu_asms | ASMS | start_bit=3, bit_length=1 | little | uint, unsigned | 1 |  | 无人开关标志位：0关，1开 |
| ecu_manualstate | Man_State | start_bit=4, bit_length=4 | little | uint, unsigned | 1 |  | 图片对 bit4~bit6 的说明：0低压，1有人高压，2有人待驶；bit7 未见说明 |
| ecu_match_mode1 | Match_Mode（Byte1） | start_byte=1, length=1 | little | uint8 | 1 |  | 比赛模式：0有人，1直线加速A，2转向标定，3八字绕环，4高速循迹A，5高速循迹B，6制动测试，7无人检查_感知，8调试模式，9无人检查_电气，10有人录包 |
| ecu_error | 掉线标志集（Byte2） | start_byte=2, length=1 | little | uint8 | 1 |  | 图片将 Byte2 解释为多个掉线标志位集合：HUAHAI_LOSE_Flag、EBS_LOSE_Flag、RES_LOSE_Flag、ROS_LOSE_Flag、AMI_LOSE_Flag；单个位含义为 0错误/1正常 |
| ecu_match_mode2 | Match_Mode（Byte3低 4 bit） | start_bit=24, bit_length=4 | little | uint, unsigned | 1 |  | 比赛模式：0有人，1直线加速A，2转向标定，3八字绕环，4高速循迹A，5高速循迹B，6制动测试，7无人检查_感知，8调试模式，9无人检查_电气，10有人录包 |
| ecu_matchflag | KEY2_Flag | start_bit=28, bit_length=1 | little | uint, unsigned | 1 |  | 模式锁定标志位：0未锁，1锁 |
| ecu_lb_state | LB_State | start_bit=32, bit_length=2 | little | uint, unsigned | 1 |  | 控制器上使能状态位：0下使能，1请求上使能，2成功上使能 |
| ecu_lf_state | LF_State | start_bit=34, bit_length=2 | little | uint, unsigned | 1 |  | 控制器上使能状态位：0下使能，1请求上使能，2成功上使能 |
| ecu_rb_state | RB_State | start_bit=36, bit_length=2 | little | uint, unsigned | 1 |  | 控制器上使能状态位：0下使能，1请求上使能，2成功上使能 |
| ecu_rf_state | RF_State | start_bit=38, bit_length=2 | little | uint, unsigned | 1 |  | 控制器上使能状态位：0下使能，1请求上使能，2成功上使能 |
| ecu_emergency | Emergency_Flag | start_bit=40, bit_length=4 | little | uint, unsigned | 1 |  | 图片说明：1ROS，2RES，3EBS，4HUAHAI 为掉线检测；5ROS，6RES，7EBS，8ASMS 为制动检测 |
| ecu_lose_time | Lose_Time | start_byte=6, length=1 | little | uint8 | 1 |  | 设备掉线时间；Emergency_Flag=0 时开始计时，最大至 255（2.55s） |
| ecu_enable | RES_GO | start_bit=56, bit_length=1 | little | uint, unsigned | 1 |  | GO 标志位：进入 AS Driving 蜂鸣完成后置 1 |
| ecu_hv | SC_OUT | start_bit=57, bit_length=1 | little | uint, unsigned | 1 |  | 安全回路闭合标志位：0没闭合，1闭合 |
| res_go_signal | Motor_EN_State | start_bit=60, bit_length=1 | little | uint, unsigned | 1 |  | 电机使能状态位：0电机没有使能，1电机使能 |

补充说明：
- 信息来源：`ECU156.png`、`模式选择0x55.wps`、`25D电控系统dbc文件汇总/ecures-孙广博.dbc`
- DBC `BO_ 342 HRT_Ctrl` 与当前 `156` 的字段布局基本一致，可作为该报文的旁证。
- `ECU156.png` 对该报文做了位级标注：`bit3=ASMS`，`bit4~7=Man_State`，`byte1/byte3` 含 `Match_Mode`，`byte4` 为四轮电机状态，`byte5` 为 `Emergency_Flag`，`byte6` 为 `Lose_Time`，`byte7` 含 `RES_GO / SC_CUT / Motor_EN_State`。
- `模式选择0x55.wps` 给出了模式字对照，可用于理解 `Match_Mode`：`00 00=有人驾驶`、`01 00=直线加速A`、`02 00=转向标定`、`03 00=八字绕环`、`04 00=高速循迹A`、`05 00=高速循迹B`、`06 00=制动测试`、`07 00=无人检查(AS)`、`08 00=调试模式`、`09 00=无人检查_电气`、`0A 00=有人录包`。

### 201 - EPOS4_Mode_or_Stop

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| raw_data | 模式选择 / 急停 | LEN=8 或 2 | little | 原始字节流 |  |  | `01 00 00 00 00 00 00 00`=位置模式选择；`00 00`=急停 |

补充说明：
- 信息来源：`转向电机内置报文解析.docx`
- 转向说明文档中，`0x201` 为主控发往电机控制器的模式选择 / 急停报文。
- `LEN=8, DATA=01 00 00 00 00 00 00 00` 表示切换到位置控制模式。
- `LEN=2, DATA=00 00` 表示急停，急停后若需恢复运行，需要重新执行使能流程。

### * 231 - ECU_Torque

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| torque_lf |  | start_byte=0, length=2 | little | int16 | 1 |  |  |
| torque_rf |  | start_byte=2, length=2 | little | int16 | 1 |  |  |
| torque_lb |  | start_byte=4, length=2 | little | int16 | 1 |  |  |
| torque_rb |  | start_byte=6, length=2 | little | int16 | 1 |  |  |

### * 232 - ECU_Speed

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| speed_rb | 右后轮速 | start_byte=0, length=2 | little | int16 | 0.0016833316500016835 | m/s |  |
| speed_rf | 右前轮速 | start_byte=2, length=2 | little | int16 | 0.0016833316500016835 | m/s |  |
| speed_lb | 左后轮速 | start_byte=4, length=2 | little | int16 | 0.0016833316500016835 | m/s |  |
| speed_lf | 左前轮速 | start_byte=6, length=2 | little | int16 | 0.0016833316500016835 | m/s |  |

### * 233 - ECU_Angle

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| huahai_output_raw |  | start_byte=0, length=2 | little | int16 | 0.001 |  |  |
| huahai_output |  | start_byte=2, length=2 | little | int16 | 0.001 |  |  |
| angle_actual | 转角实际值 | start_byte=6, length=2 | little | int16 | 0.001 | rad |  |

### * 234 - AMK_speed

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| speed_rb |  | start_byte=0, length=2 | little | int16 | 0.0016833316500016835 |  |  |
| speed_rf |  | start_byte=2, length=2 | little | int16 | 0.0016833316500016835 |  |  |
| speed_lb |  | start_byte=4, length=2 | little | int16 | 0.0016833316500016835 |  |  |
| speed_lf |  | start_byte=6, length=2 | little | int16 | 0.0016833316500016835 |  |  |

### * 235 - IVT_Power

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| power_raw | 功率原始值 | start_byte=1, length=4 | big | uint32 | 1 |  |  |

### 381 - EPOS4_Status_Position

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| statusword | 状态字 | start_byte=0, length=2 | little | uint16 | 1 |  | 转向说明明确：前两字节为 Statusword |
| actual_position | 实际位置 | start_byte=2, length=4 | little | int32 | 1 |  | 转向说明明确：后四字节为 Actual Position |

补充说明：
- 信息来源：`转向电机内置报文解析.docx`、`25D电控系统dbc文件汇总/25d报文整理.xlsx`、`25D电控系统dbc文件汇总/381steer.dbc`
- 转向说明文档指出：当前项目实际反馈报文使用 `0x381`，替代了早期手稿中的 `0x481`。
- 固定结构为 `Statusword(2字节) + Actual Position(4字节)`，总长度 6 字节。
- 文档示例状态字包括：`0x0240`（未使能）、`0x0221`（准备使能）、`0x0637`（已使能运行）、`0x1237`、`0x1637`。
- `25d报文整理.xlsx` 也注明 `0x381` 为“转向电机给华海发的实时位置”，链路为 `CAN3`。

### 401 - enable401

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| enable401 | 控制字低字节 | start_byte=0, length=1 | little | uint8 | 1 |  | 转向资料显示常见值：`06`、`0F`、`4F`、`3F` |
| enable401_Copy_1 | 控制字高字节 | start_byte=1, length=1 | little | uint8 | 1 |  | 常见为 `00` |
| enable401_Copy_2 | 目标位置 / 参数区 | start_byte=2, length=4 | little | uint32 | 1 |  | 在位置控制报文中用于目标位置值 |

补充说明：
- 信息来源：`转向电机内置报文解析.docx`、`25D电控系统dbc文件汇总/ecures-孙广博.dbc`
- 转向说明文档明确：`0x401` 为“控制字 / 目标位置”报文，长度 6，结构为“前两字节控制字 + 后四字节目标位置”。
- 常见控制流程：`06 00 00 00 00 00`（准备状态转换）→ `0F 00 00 00 00 00`（使能）→ `4F 00 00 00 00 00`（运行准备）→ `3F 00 xx xx xx xx`（带目标位置运行）。
- 示例：目标位置 5000 时，报文为 `3F 00 88 13 00 00`。

### * 402 - EBS_OIL

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| LF_OIL | 左前油压 | start_byte=0, length=2 | little | uint16 | 1 | 0.01bar |  |
| RF_OIL | 右前油压 | start_byte=2, length=2 | little | uint16 | 1 | 0.01bar |  |
| LB_OIL | 左后油压 | start_byte=4, length=2 | little | uint16 | 1 | 0.01bar |  |
| RB_OIL | 右后油压 | start_byte=6, length=2 | little | uint16 | 1 | 0.01bar |  |

补充说明：
- 信息来源：`EBS CAN.xls`、`25D电控系统dbc文件汇总/ecures-孙广博.dbc`
- `EBS CAN.xls` 对 `0x402` 的字节定义与当前解析一致：Byte0/1=左前油压，Byte2/3=右前油压，Byte4/5=左后油压，Byte6/7=右后油压。

### * 482 - EBS_AIR

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| air1 | 前路气压 | start_byte=0, length=2 | little | uint16 | 1 | 0.01bar | DBC `BO_ 1154 EBS_AIR` 中定义 |
| air2 | 后路气压 | start_byte=2, length=2 | little | uint16 | 1 | 0.01bar | DBC `BO_ 1154 EBS_AIR` 中定义 |
| votage | 电源电压 | start_byte=4, length=2 | little | uint16 | 1 | 0.01V | DBC 中字段名拼写为 `votage` |

补充说明：
- 信息来源：`EBS CAN.xls`、`25D电控系统dbc文件汇总/ecures-孙广博.dbc`
- `EBS CAN.xls` 中将该报文记作 `0x482 - 气压传感器+电压`。
- DBC 里对应 `BO_ 1154 EBS_AIR`，十进制 `1154` 即十六进制 `0x482`。
- 字节定义为：Byte0/1=前路气压，Byte2/3=后路气压，Byte4/5=电压。

### 521 - IVT_Msg_Result_I

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| IVT_ID_Result_I |  | start_bit=7, bit_length=8 | big | uint, unsigned | 1 |  |  |
| IVT_MsgCount_Result_I |  | start_bit=11, bit_length=4 | big | uint, unsigned | 1 |  |  |
| IVT_Result_I_OCS |  | start_bit=12, bit_length=1 | big | uint, unsigned | 1 |  |  |
| IVT_Result_I_Channel_Error |  | start_bit=13, bit_length=1 | big | uint, unsigned | 1 |  |  |
| IVT_Result_I_Measurement_Error |  | start_bit=14, bit_length=1 | big | uint, unsigned | 1 |  |  |
| IVT_Result_I_System_Error |  | start_bit=15, bit_length=1 | big | uint, unsigned | 1 |  |  |
| IVT_Result_I | 电流 | start_bit=23, bit_length=32 | big | int, signed | 1 | mA |  |

### 522 - IVT_Msg_Result_U1

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| IVT_ID_Result_U1 |  | start_bit=7, bit_length=8 | big | uint, unsigned | 1 |  |  |
| IVT_MsgCount_Result_U1 |  | start_bit=11, bit_length=4 | big | uint, unsigned | 1 |  |  |
| IVT_Result_U1_OCS |  | start_bit=12, bit_length=1 | big | uint, unsigned | 1 |  |  |
| IVT_Result_U1_Channel_Error |  | start_bit=13, bit_length=1 | big | uint, unsigned | 1 |  |  |
| IVT_Result_U1_Measurement_Error |  | start_bit=14, bit_length=1 | big | uint, unsigned | 1 |  |  |
| IVT_Result_U1_System_Error |  | start_bit=15, bit_length=1 | big | uint, unsigned | 1 |  |  |
| IVT_Result_U1 | 电压 U1 | start_bit=23, bit_length=32 | big | int, signed | 1 | mV |  |

### 581 - EPOS4_SDO_Response

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| raw_data | SDO 响应 | LEN=8 |  | 原始字节流 |  |  | 转向说明给出用途为参数读写返回值 |

补充说明：
- 信息来源：`转向电机内置报文解析.docx`
- 转向说明文档中，`0x581` 为电机控制器返回的 SDO 响应报文。

### 601 - EPOS4_SDO_Request

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| raw_data | SDO 读写请求 | LEN=8 |  | 原始字节流 |  |  | 转向说明给出用途为参数读写 / 复位请求 |

补充说明：
- 信息来源：`转向电机内置报文解析.docx`、`25D电控系统dbc文件汇总/25d报文整理.xlsx`
- 转向说明文档中，`0x601` 为主控发往电机控制器的 SDO 请求报文。
- `25d报文整理.xlsx` 还提到该 ID 参与参数读写，并可能用于向转向电机发送复位相关报文。

### 701 - EPOS4_Heartbeat

| 信号名 | 展示名 | 解析方式 | 字节序 | 数据类型 | scale（缩放系数） | 单位 | 说明 |
|---|---|---|---|---|---:|---|---|
| node_state | 上线/心跳 | LEN=1 |  | uint8 | 1 |  | 转向说明示例为 `DATA: 00` |

补充说明：
- 信息来源：`转向电机内置报文解析.docx`
- 转向说明文档中，`0x701` 为电机控制器上电后的上线/心跳报文。
- 示例：`ID: 0x701, LEN: 1, DATA: 00`。
