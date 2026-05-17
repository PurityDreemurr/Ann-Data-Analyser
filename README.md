# Ann Data Analyser

![](icon/icon.png)

一个基于 **UDP + CAN 报文** 的上位机项目，支持随机报文发送、协议解析和 PyQt 图形化监控 。

## 功能简介

- 通过 UDP 打包发送多条 CAN 帧（带时间戳）
- 按 `data_sheet` 中定义解析 AMK / EBS / EPOS / IVT / ECU 报文
- GUI 实时展示：
  - 按选项卡分组显示报文
  - 原始报文与解析结果
  - 状态指示灯（超时自动变红）
  - 接收速率与报文统计
- 支持通过 `can_id_config.json` 统一修改 CAN ID

## 项目文件

- `can_udp_sender.py`：随机生成并发送 UDP-CAN 报文
- `can_udp_parser.py`：命令行接收并解析 UDP-CAN 报文
- `gui.py`：图形界面监控程序
- `can_id_config.json`：CAN ID 配置文件
- `data_sheet/CAN_ID报文整理 (1).md`：报文定义依据

## 安装依赖

```powershell
pip install -r .\requirements.txt
```

## 使用方法

1. 启动 GUI（接收端）：

```powershell
python .\gui.py --ip 0.0.0.0 --port 5005
```

2. 启动发送端：

```powershell
python .\can_udp_sender.py --ip 127.0.0.1 --port 5005 --hz 20
```

3. 如需命令行解析调试：

```powershell
python .\can_udp_parser.py --ip 0.0.0.0 --port 5005
```

## 说明

- 局域网场景下，发送端 `--ip` 应填写 **GUI 所在主机 IP**。
- GUI 监听地址建议使用 `0.0.0.0`（监听本机所有网卡）。
