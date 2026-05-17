import json
from pathlib import Path
from typing import Dict


CONFIG_PATH = Path(__file__).with_name("can_id_config.json")

DEFAULT_CAN_IDS: Dict[str, int] = {
    "amk_actual_lf": 0x283,
    "amk_actual_rf": 0x284,
    "amk_actual_rb": 0x287,
    "amk_actual_lb": 0x288,
    "amk_speed": 0x234,
    "epos_pdo_start": 0x000,
    "ebs_status": 0x002,
    "command": 0x020,
    "ins_output": 0x021,
    "ins_output2": 0x022,
    "ebs_oil": 0x402,
    "ebs_air": 0x482,
    "steer_encoder": 0x096,
    "epos_mode_or_stop": 0x201,
    "epos_status_position": 0x381,
    "epos_control": 0x401,
    "epos_sdo_response": 0x581,
    "epos_sdo_request": 0x601,
    "epos_heartbeat": 0x701,
    "ivt_result_i": 0x521,
    "ivt_result_u1": 0x522,
    "ivt_power": 0x235,
    "ecu_msg": 0x156,
    "ecu_torque": 0x231,
    "ecu_speed": 0x232,
    "ecu_angle": 0x233,
}


def _parse_can_id(value: object) -> int:
    if isinstance(value, int):
        can_id = value
    elif isinstance(value, str):
        can_id = int(value, 0)
    else:
        raise ValueError(f"Invalid CAN ID type: {type(value).__name__}")

    if can_id < 0 or can_id > 0x1FFFFFFF:
        raise ValueError(f"CAN ID out of range: {can_id}")
    return can_id


def _write_default_config() -> None:
    content = {"can_ids": {key: hex(value) for key, value in DEFAULT_CAN_IDS.items()}}
    CONFIG_PATH.write_text(
        json.dumps(content, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_can_ids() -> Dict[str, int]:
    if not CONFIG_PATH.exists():
        _write_default_config()

    raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    can_ids_node = raw.get("can_ids")
    if not isinstance(can_ids_node, dict):
        raise ValueError("can_id_config.json must contain object field 'can_ids'")

    can_ids: Dict[str, int] = {}
    for key in DEFAULT_CAN_IDS:
        if key not in can_ids_node:
            raise ValueError(f"Missing CAN ID config for key: {key}")
        can_ids[key] = _parse_can_id(can_ids_node[key])

    unique_ids = set(can_ids.values())
    if len(unique_ids) != len(can_ids):
        raise ValueError("Duplicate CAN IDs found in can_id_config.json")
    return can_ids


def get_can_id(key: str) -> int:
    can_ids = load_can_ids()
    if key not in can_ids:
        raise KeyError(f"Unknown CAN ID key: {key}")
    return can_ids[key]

