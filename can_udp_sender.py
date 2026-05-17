import argparse
import random
import socket
import struct
import time
from dataclasses import dataclass
from typing import List

from can_id_config import get_can_id


MAGIC = b"CUDP"
VERSION = 1
CAN_CHANNEL = 0


@dataclass
class CanFrame:
    can_id: int
    dlc: int
    data: bytes
    flags: int = 0

    def pack(self) -> bytes:
        if len(self.data) != 8:
            raise ValueError("CAN data must be exactly 8 bytes")
        return struct.pack("<IBBH8s", self.can_id, self.dlc, self.flags, 0, self.data)


def _pack_u16x4(a: int, b: int, c: int, d: int) -> bytes:
    return struct.pack("<HHHH", a, b, c, d)


def _pack_i16x4(a: int, b: int, c: int, d: int) -> bytes:
    return struct.pack("<hhhh", a, b, c, d)


def _pack_amk_actual() -> bytes:
    status = random.choice([1, 82, 121, 129])
    velocity = random.randint(-12000, 12000)
    torque = random.randint(-2500, 2500)
    magnetizing = random.randint(-2500, 2500)
    return _pack_u16x4(status, velocity & 0xFFFF, torque & 0xFFFF, magnetizing & 0xFFFF)


def _pack_amk_actual_safe() -> bytes:
    status = random.choice([1, 82, 121, 129])
    velocity = random.randint(-12000, 12000)
    torque = random.randint(-2500, 2500)
    magnetizing = random.randint(-2500, 2500)
    return struct.pack("<Hhhh", status, velocity, torque, magnetizing)


def _pack_amk_speed_like() -> bytes:
    return _pack_i16x4(
        random.randint(0, 3000),
        random.randint(0, 3000),
        random.randint(0, 3000),
        random.randint(0, 3000),
    )


def _pack_ebs_status() -> bytes:
    flags = 0
    flags |= random.randint(0, 1) << 0   # ebs_error
    flags |= random.randint(0, 1) << 4   # ebs_ready
    flags |= random.randint(0, 1) << 5   # ecu_disconnected
    flags |= random.randint(0, 1) << 31  # timeout
    return struct.pack("<I", flags) + b"\x00\x00\x00\x00"


def _pack_command() -> bytes:
    workstation_status = random.randint(0, 7)
    velocity_cmd = random.randint(-32767, 32767)
    angle_cmd = random.randint(-32767, 32767)
    sensor_state = random.randint(0, 8)
    payload = bytearray(8)
    payload[0] = workstation_status
    payload[1:3] = struct.pack("<h", velocity_cmd)
    payload[3:5] = struct.pack("<h", angle_cmd)
    payload[7] = sensor_state
    return bytes(payload)


def _pack_ins_output() -> bytes:
    return struct.pack(
        "<hhhh",
        random.randint(-32000, 32000),
        random.randint(-32000, 32000),
        random.randint(-32000, 32000),
        random.randint(-32000, 32000),
    )


def _pack_ins_output2() -> bytes:
    payload = bytearray(8)
    payload[0:2] = struct.pack("<H", random.randint(0, 65535))
    payload[2:4] = struct.pack("<h", random.randint(-30000, 30000))
    return bytes(payload)


def _pack_steer_encoder() -> bytes:
    payload = bytearray(8)
    raw_angle = random.randint(0, 65535)
    payload[3:5] = struct.pack("<H", raw_angle)
    return bytes(payload)


def _pack_epos_status_position() -> bytes:
    statusword = random.choice([0x0240, 0x0221, 0x0637, 0x1237, 0x1637])
    actual_position = random.randint(-200000, 200000)
    return struct.pack("<Hi", statusword, actual_position) + b"\x00\x00"


def _pack_epos_control() -> bytes:
    control_low = random.choice([0x06, 0x0F, 0x4F, 0x3F])
    control_high = 0x00
    target_position = random.randint(-200000, 200000)
    return bytes([control_low, control_high]) + struct.pack("<i", target_position) + b"\x00\x00"


def _pack_epos_raw() -> bytes:
    return bytes(random.randint(0, 255) for _ in range(8))


def _pack_epos_pdo_start() -> bytes:
    return b"\x01\x00\x00\x00\x00\x00\x00\x00"


def _pack_epos_mode_or_stop() -> bytes:
    if random.random() < 0.2:
        return b"\x00\x00\x00\x00\x00\x00\x00\x00"
    return b"\x01\x00\x00\x00\x00\x00\x00\x00"


def _pack_epos_heartbeat() -> bytes:
    return bytes([random.choice([0x00, 0x05, 0x7F])]) + b"\x00\x00\x00\x00\x00\x00\x00"


def _pack_ivt_result_i() -> bytes:
    current_ma = random.randint(-250000, 250000)
    payload = bytearray(8)
    payload[3:7] = struct.pack(">i", current_ma)
    return bytes(payload)


def _pack_ivt_result_u1() -> bytes:
    voltage_mv = random.randint(200000, 900000)
    payload = bytearray(8)
    payload[3:7] = struct.pack(">i", voltage_mv)
    return bytes(payload)


def _pack_ivt_power() -> bytes:
    power_raw = random.randint(0, 1_000_000)
    payload = bytearray(8)
    payload[1:5] = struct.pack(">I", power_raw)
    return bytes(payload)


def _pack_ecu_msg() -> bytes:
    raw = 0
    raw |= random.randint(0, 7) << 0   # ecu_state
    raw |= random.randint(0, 1) << 3   # ecu_asms
    raw |= random.randint(0, 15) << 4  # ecu_manualstate
    raw |= random.randint(0, 15) << 24  # ecu_match_mode2
    raw |= random.randint(0, 1) << 28   # ecu_matchflag
    raw |= random.randint(0, 3) << 32   # ecu_lb_state
    raw |= random.randint(0, 3) << 34   # ecu_lf_state
    raw |= random.randint(0, 3) << 36   # ecu_rb_state
    raw |= random.randint(0, 3) << 38   # ecu_rf_state
    raw |= random.randint(0, 15) << 40  # ecu_emergency
    raw |= random.randint(0, 1) << 56   # ecu_enable
    raw |= random.randint(0, 1) << 57   # ecu_hv
    raw |= random.randint(0, 1) << 60   # res_go_signal
    payload = bytearray(raw.to_bytes(8, byteorder="little", signed=False))
    payload[1] = random.randint(0, 255)  # ecu_match_mode1
    payload[2] = random.randint(0, 255)  # ecu_error
    payload[6] = random.randint(0, 255)  # ecu_lose_time
    return bytes(payload)


def _frame(key: str, data: bytes, dlc: int = 8) -> CanFrame:
    return CanFrame(get_can_id(key), dlc, data)


def build_random_frames() -> List[CanFrame]:
    return [
        _frame("epos_pdo_start", _pack_epos_pdo_start()),
        _frame("amk_actual_lf", _pack_amk_actual_safe()),
        _frame("amk_actual_rf", _pack_amk_actual_safe()),
        _frame("amk_actual_rb", _pack_amk_actual_safe()),
        _frame("amk_actual_lb", _pack_amk_actual_safe()),
        _frame("amk_speed", _pack_amk_speed_like()),
        _frame("ebs_status", _pack_ebs_status()),
        _frame("command", _pack_command()),
        _frame("ins_output", _pack_ins_output()),
        _frame("ins_output2", _pack_ins_output2()),
        _frame("ebs_oil", _pack_u16x4(random.randint(0, 8000), random.randint(0, 8000), random.randint(0, 8000), random.randint(0, 8000))),
        _frame("ebs_air", struct.pack("<HHH", random.randint(0, 8000), random.randint(0, 8000), random.randint(1200, 2800)) + b"\x00\x00"),
        _frame("steer_encoder", _pack_steer_encoder()),
        _frame("epos_mode_or_stop", _pack_epos_mode_or_stop()),
        _frame("epos_status_position", _pack_epos_status_position()),
        _frame("epos_control", _pack_epos_control()),
        _frame("epos_sdo_response", _pack_epos_raw()),
        _frame("epos_sdo_request", _pack_epos_raw()),
        _frame("epos_heartbeat", _pack_epos_heartbeat(), dlc=1),
        _frame("ivt_result_i", _pack_ivt_result_i()),
        _frame("ivt_result_u1", _pack_ivt_result_u1()),
        _frame("ivt_power", _pack_ivt_power()),
        _frame("ecu_msg", _pack_ecu_msg()),
        _frame("ecu_torque", _pack_i16x4(random.randint(-3000, 3000), random.randint(-3000, 3000), random.randint(-3000, 3000), random.randint(-3000, 3000))),
        _frame("ecu_speed", _pack_amk_speed_like()),
        _frame("ecu_angle", struct.pack("<hh", random.randint(-30000, 30000), random.randint(-30000, 30000)) + b"\x00\x00" + struct.pack("<h", random.randint(-30000, 30000))),
    ]


def build_udp_packet(frames: List[CanFrame], timestamp_us: int) -> bytes:
    if not (0 <= len(frames) <= 255):
        raise ValueError("frame count must be in [0, 255]")

    header = struct.pack(
        "<4sBBBBQ",
        MAGIC,
        VERSION,
        CAN_CHANNEL,
        len(frames),
        0,
        timestamp_us,
    )
    body = b"".join(frame.pack() for frame in frames)
    return header + body


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate random CAN frames and send via UDP.")
    parser.add_argument("--ip", default="127.0.0.1", help="UDP destination IP")
    parser.add_argument("--port", type=int, default=5005, help="UDP destination port")
    parser.add_argument("--hz", type=float, default=20.0, help="Send frequency (packets/s)")
    args = parser.parse_args()

    if args.hz <= 0:
        raise ValueError("--hz must be > 0")

    interval = 1.0 / args.hz
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    target = (args.ip, args.port)

    print(f"Sending UDP CAN packets to {args.ip}:{args.port} at {args.hz:.3f} Hz")
    try:
        while True:
            now_us = time.time_ns() // 1000
            frames = build_random_frames()
            packet = build_udp_packet(frames, now_us)
            sock.sendto(packet, target)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
