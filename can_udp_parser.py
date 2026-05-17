import argparse
import json
import socket
import struct
from typing import Callable, Dict, List

from can_id_config import get_can_id


MAGIC = b"CUDP"
HEADER_FMT = "<4sBBBBQ"
HEADER_SIZE = struct.calcsize(HEADER_FMT)
FRAME_FMT = "<IBBH8s"
FRAME_SIZE = struct.calcsize(FRAME_FMT)


def _u16_le(data8: bytes, start: int) -> int:
    return struct.unpack("<H", data8[start : start + 2])[0]


def _i16_le(data8: bytes, start: int) -> int:
    return struct.unpack("<h", data8[start : start + 2])[0]


def _i32_le(data8: bytes, start: int) -> int:
    return struct.unpack("<i", data8[start : start + 4])[0]


def _u32_be(data8: bytes, start: int) -> int:
    return struct.unpack(">I", data8[start : start + 4])[0]


def _i32_be(data8: bytes, start: int) -> int:
    return struct.unpack(">i", data8[start : start + 4])[0]


def _get_bits_le(data8: bytes, start_bit: int, length: int) -> int:
    raw = int.from_bytes(data8, byteorder="little", signed=False)
    return (raw >> start_bit) & ((1 << length) - 1)


def _decode_amk_actual(data8: bytes) -> Dict[str, object]:
    return {
        "status": _u16_le(data8, 0),
        "velocity_rpm": _i16_le(data8, 2),
        "torque_current": _i16_le(data8, 4),
        "magnetizing_current": _i16_le(data8, 6),
    }


def _decode_amk_speed(data8: bytes) -> Dict[str, object]:
    scale = 0.0016833316500016835
    return {
        "speed_rb_mps": _i16_le(data8, 0) * scale,
        "speed_rf_mps": _i16_le(data8, 2) * scale,
        "speed_lb_mps": _i16_le(data8, 4) * scale,
        "speed_lf_mps": _i16_le(data8, 6) * scale,
    }


def _decode_epos_raw(data8: bytes) -> Dict[str, object]:
    return {"raw_data": data8.hex()}


def _decode_ebs_status(data8: bytes) -> Dict[str, object]:
    return {
        "ebs_error": _get_bits_le(data8, 0, 1),
        "ebs_ready": _get_bits_le(data8, 4, 1),
        "ecu_disconnected": _get_bits_le(data8, 5, 1),
        "timeout": _get_bits_le(data8, 31, 1),
    }


def _decode_command(data8: bytes) -> Dict[str, object]:
    return {
        "workstation_status": data8[0],
        "velocity_cmd_mps": _i16_le(data8, 1) * 0.001,
        "angle_cmd": _i16_le(data8, 3) * 0.001,
        "sensor_state": data8[7],
    }


def _decode_ins_output(data8: bytes) -> Dict[str, object]:
    return {
        "velocity_x_mps": _i16_le(data8, 0) * 0.001,
        "velocity_y_mps": _i16_le(data8, 2) * 0.001,
        "acceleration_x": _i16_le(data8, 4) * 0.001,
        "acceleration_y": _i16_le(data8, 6) * 0.001,
    }


def _decode_ins_output2(data8: bytes) -> Dict[str, object]:
    return {
        "vehicle_speed_mps": _u16_le(data8, 0) * 0.001,
        "yaw_rate_dps": _i16_le(data8, 2) / 150.0,
    }


def _decode_ebs_oil(data8: bytes) -> Dict[str, object]:
    return {
        "lf_oil_bar": _u16_le(data8, 0) * 0.01,
        "rf_oil_bar": _u16_le(data8, 2) * 0.01,
        "lb_oil_bar": _u16_le(data8, 4) * 0.01,
        "rb_oil_bar": _u16_le(data8, 6) * 0.01,
    }


def _decode_ebs_air(data8: bytes) -> Dict[str, object]:
    return {
        "air1_bar": _u16_le(data8, 0) * 0.01,
        "air2_bar": _u16_le(data8, 2) * 0.01,
        "voltage_v": _u16_le(data8, 4) * 0.01,
    }


def _decode_steer_encoder(data8: bytes) -> Dict[str, object]:
    return {"raw_angle": _u16_le(data8, 3)}


def _decode_epos_status_position(data8: bytes) -> Dict[str, object]:
    return {
        "statusword": _u16_le(data8, 0),
        "actual_position": _i32_le(data8, 2),
    }


def _decode_epos_control(data8: bytes) -> Dict[str, object]:
    return {
        "control_low": data8[0],
        "control_high": data8[1],
        "target_position": _i32_le(data8, 2),
    }


def _decode_epos_heartbeat(data8: bytes) -> Dict[str, object]:
    return {"node_state": data8[0]}


def _decode_ivt_result_i(data8: bytes) -> Dict[str, object]:
    return {"current_ma": _i32_be(data8, 3)}


def _decode_ivt_result_u1(data8: bytes) -> Dict[str, object]:
    return {"voltage_mv": _i32_be(data8, 3)}


def _decode_ivt_power(data8: bytes) -> Dict[str, object]:
    return {"power_raw": _u32_be(data8, 1)}


def _decode_ecu_msg(data8: bytes) -> Dict[str, object]:
    return {
        "statu_flag": _get_bits_le(data8, 0, 3),
        "asms": _get_bits_le(data8, 3, 1),
        "man_state": _get_bits_le(data8, 4, 4),
        "match_mode_byte1": data8[1],
        "lose_flag_set": data8[2],
        "match_mode_low4": _get_bits_le(data8, 24, 4),
        "key2_flag": _get_bits_le(data8, 28, 1),
        "lb_state": _get_bits_le(data8, 32, 2),
        "lf_state": _get_bits_le(data8, 34, 2),
        "rb_state": _get_bits_le(data8, 36, 2),
        "rf_state": _get_bits_le(data8, 38, 2),
        "emergency_flag": _get_bits_le(data8, 40, 4),
        "lose_time": data8[6],
        "res_go": _get_bits_le(data8, 56, 1),
        "sc_out": _get_bits_le(data8, 57, 1),
        "motor_en_state": _get_bits_le(data8, 60, 1),
    }


def _decode_ecu_torque(data8: bytes) -> Dict[str, object]:
    return {
        "torque_lf": _i16_le(data8, 0),
        "torque_rf": _i16_le(data8, 2),
        "torque_lb": _i16_le(data8, 4),
        "torque_rb": _i16_le(data8, 6),
    }


def _decode_ecu_speed(data8: bytes) -> Dict[str, object]:
    scale = 0.0016833316500016835
    return {
        "speed_rb_mps": _i16_le(data8, 0) * scale,
        "speed_rf_mps": _i16_le(data8, 2) * scale,
        "speed_lb_mps": _i16_le(data8, 4) * scale,
        "speed_lf_mps": _i16_le(data8, 6) * scale,
    }


def _decode_ecu_angle(data8: bytes) -> Dict[str, object]:
    return {
        "huahai_output_raw": _i16_le(data8, 0) * 0.001,
        "huahai_output": _i16_le(data8, 2) * 0.001,
        "angle_actual_rad": _i16_le(data8, 6) * 0.001,
    }


MESSAGE_SPECS: List[Dict[str, object]] = [
    {"key": "epos_pdo_start", "name": "EPOS4_PDO_Start", "tab": "转向系统", "decoder": _decode_epos_raw},
    {"key": "amk_actual_lf", "name": "AMK_ActualValue1_LF", "tab": "电机控制器", "decoder": _decode_amk_actual},
    {"key": "amk_actual_rf", "name": "AMK_ActualValue1_RF", "tab": "电机控制器", "decoder": _decode_amk_actual},
    {"key": "amk_actual_rb", "name": "AMK_ActualValue1_RB", "tab": "电机控制器", "decoder": _decode_amk_actual},
    {"key": "amk_actual_lb", "name": "AMK_ActualValue1_LB", "tab": "电机控制器", "decoder": _decode_amk_actual},
    {"key": "amk_speed", "name": "AMK_speed", "tab": "电机控制器", "decoder": _decode_amk_speed},
    {"key": "ebs_status", "name": "EBS_Status", "tab": "EBS", "decoder": _decode_ebs_status},
    {"key": "command", "name": "command", "tab": "ECU", "decoder": _decode_command},
    {"key": "ins_output", "name": "INSOutput", "tab": "ECU", "decoder": _decode_ins_output},
    {"key": "ins_output2", "name": "INSOutput2", "tab": "ECU", "decoder": _decode_ins_output2},
    {"key": "ebs_oil", "name": "EBS_OIL", "tab": "EBS", "decoder": _decode_ebs_oil},
    {"key": "ebs_air", "name": "EBS_AIR", "tab": "EBS", "decoder": _decode_ebs_air},
    {"key": "steer_encoder", "name": "SteerEncoder", "tab": "转向系统", "decoder": _decode_steer_encoder},
    {"key": "epos_mode_or_stop", "name": "EPOS4_Mode_or_Stop", "tab": "转向系统", "decoder": _decode_epos_raw},
    {"key": "epos_status_position", "name": "EPOS4_Status_Position", "tab": "转向系统", "decoder": _decode_epos_status_position},
    {"key": "epos_control", "name": "enable401", "tab": "转向系统", "decoder": _decode_epos_control},
    {"key": "epos_sdo_response", "name": "EPOS4_SDO_Response", "tab": "转向系统", "decoder": _decode_epos_raw},
    {"key": "epos_sdo_request", "name": "EPOS4_SDO_Request", "tab": "转向系统", "decoder": _decode_epos_raw},
    {"key": "epos_heartbeat", "name": "EPOS4_Heartbeat", "tab": "转向系统", "decoder": _decode_epos_heartbeat},
    {"key": "ivt_result_i", "name": "IVT_Msg_Result_I", "tab": "能量计", "decoder": _decode_ivt_result_i},
    {"key": "ivt_result_u1", "name": "IVT_Msg_Result_U1", "tab": "能量计", "decoder": _decode_ivt_result_u1},
    {"key": "ivt_power", "name": "IVT_Power", "tab": "能量计", "decoder": _decode_ivt_power},
    {"key": "ecu_msg", "name": "ECU_msg", "tab": "ECU", "decoder": _decode_ecu_msg},
    {"key": "ecu_torque", "name": "ECU_Torque", "tab": "ECU", "decoder": _decode_ecu_torque},
    {"key": "ecu_speed", "name": "ECU_Speed", "tab": "ECU", "decoder": _decode_ecu_speed},
    {"key": "ecu_angle", "name": "ECU_Angle", "tab": "ECU", "decoder": _decode_ecu_angle},
]


MESSAGE_BY_ID: Dict[int, Dict[str, object]] = {
    get_can_id(spec["key"]): spec for spec in MESSAGE_SPECS
}


def _format_decoded(decoded: Dict[str, object]) -> str:
    parts = []
    for k, v in decoded.items():
        if isinstance(v, float):
            parts.append(f"{k}: {v:.3f}")
        else:
            parts.append(f"{k}: {v}")
    return "\n".join(parts)


def parse_packet(packet: bytes) -> Dict[str, object]:
    if len(packet) < HEADER_SIZE:
        raise ValueError("packet too short for header")

    magic, version, channel, frame_count, _reserved, timestamp_us = struct.unpack(
        HEADER_FMT, packet[:HEADER_SIZE]
    )
    if magic != MAGIC:
        raise ValueError(f"invalid magic: {magic!r}")

    expected_size = HEADER_SIZE + frame_count * FRAME_SIZE
    if len(packet) != expected_size:
        raise ValueError(f"packet size mismatch: got {len(packet)}, expected {expected_size}")

    offset = HEADER_SIZE
    frames: List[Dict[str, object]] = []
    message_values: Dict[str, Dict[str, object]] = {}
    for _ in range(frame_count):
        can_id, dlc, flags, _rsv, data8 = struct.unpack(
            FRAME_FMT, packet[offset : offset + FRAME_SIZE]
        )
        offset += FRAME_SIZE

        frame: Dict[str, object] = {
            "can_id": hex(can_id),
            "dlc": dlc,
            "flags": flags,
            "data_hex": data8.hex(),
        }
        spec = MESSAGE_BY_ID.get(can_id)
        if spec is not None:
            decoder = spec["decoder"]
            decoded = decoder(data8)  # type: ignore[operator]
            frame["message_key"] = spec["key"]
            frame["message_name"] = spec["name"]
            frame["tab"] = spec["tab"]
            frame["decoded"] = decoded
            frame["decoded_text"] = _format_decoded(decoded)
            message_values[spec["key"]] = decoded

        frames.append(frame)

    return {
        "version": version,
        "channel": channel,
        "timestamp_us": timestamp_us,
        "frame_count": frame_count,
        "messages": message_values,
        "frames": frames,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="UDP CAN packet parser/receiver.")
    parser.add_argument("--ip", default="127.0.0.1", help="Local bind IP")
    parser.add_argument("--port", type=int, default=5005, help="Local bind port")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.ip, args.port))
    print(f"Listening on {args.ip}:{args.port}")

    try:
        while True:
            packet, addr = sock.recvfrom(4096)
            try:
                result = parse_packet(packet)
                result["from"] = f"{addr[0]}:{addr[1]}"
                print(json.dumps(result, ensure_ascii=False))
            except Exception as exc:
                print(json.dumps({"error": str(exc), "from": f"{addr[0]}:{addr[1]}"}, ensure_ascii=False))
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
