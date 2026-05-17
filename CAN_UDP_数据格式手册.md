# CAN over UDP 数据格式手册

## 1. UDP 封装格式

- 字节序：小端序（Little Endian）
- UDP 报文 = Header(16字节) + N*Frame(16字节)

### Header（16字节）

| 偏移 | 长度 | 类型 | 字段 | 说明 |
|---|---:|---|---|---|
| 0 | 4 | char[4] | magic | 固定 `CUDP` |
| 4 | 1 | uint8 | version | 当前=1 |
| 5 | 1 | uint8 | channel | 当前=0 |
| 6 | 1 | uint8 | frame_count | 帧数 |
| 7 | 1 | uint8 | reserved | 0 |
| 8 | 8 | uint64 | timestamp_us | 时间戳（微秒） |

### Frame（16字节）

| 偏移 | 长度 | 类型 | 字段 |
|---|---:|---|---|
| 0 | 4 | uint32 | can_id |
| 4 | 1 | uint8 | dlc |
| 5 | 1 | uint8 | flags |
| 6 | 2 | uint16 | reserved |
| 8 | 8 | uint8[8] | data |

---

## 2. CAN ID 配置

CAN ID 全部从 `can_id_config.json` 读取，后续改 ID 只改配置文件。

当前默认映射：

- 电机控制器（AMK）：`0x283/0x284/0x287/0x288/0x234`
- EBS：`0x002/0x402/0x482`
- 转向系统（EPOS + 转向编码器）：`0x096/0x381/0x401/0x581/0x601/0x701`
- 能量计（IVT）：`0x521/0x522/0x235`
- ECU：`0x156/0x231/0x232/0x233`
- 安全回路：无相关报文

---

## 3. 页面分组

GUI 选项卡分组如下：

1. 安全回路：无相关信息（留空）
2. 电机控制器：AMK 相关
3. 转向系统：EPOS + 转向电机/编码器
4. EBS：EBS 相关
5. 能量计：IVT 相关
6. ECU：ECU 相关

每个数据项显示：原始报文、解析结果、状态指示灯（2秒超时红灯）。

---

## 4. 运行命令

发送端：

```powershell
python .\can_udp_sender.py --ip 127.0.0.1 --port 5005 --hz 20
```

解析端（CLI）：

```powershell
python .\can_udp_parser.py --ip 127.0.0.1 --port 5005
```

GUI：

```powershell
python .\can_udp_gui.py --ip 127.0.0.1 --port 5005
```
