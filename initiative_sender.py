#!/usr/bin/env python3
"""
initiative_sender.py

后台守护脚本：定期调用 Orchestrator.generate_initiative(user_id)
若返回非空文本，则通过 AstrBot / OneBot HTTP API 发送私聊消息。

说明（中文注释）：
- 本脚本与 Orchestrator 的 process 流程完全解耦，只以只读方式调用 generate_initiative。
- generate_initiative 不会写入对话历史或记忆，本脚本收到非空返回才进行发送。
- 配置优先级：config.yaml -> 环境变量。
- 支持 AstrBot 的 action: send_private_msg（统一 HTTP POST）和 OneBot 的 /send_private_msg 端点。
- 包含随机化间隔、连续空结果 backoff、日志记录、错误处理。

依赖：requests, pyyaml (pyyaml 可选，脚本在无 yaml 时回退使用环境变量)
"""

import os
import time
import random
import logging
from typing import Optional

try:
    import yaml
except Exception:
    yaml = None

import requests

from src.orchestrator import Orchestrator

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("initiative_sender")


def load_config(path: str = "config.yaml") -> dict:
    """加载配置：优先读取 config.yaml（若存在），再以环境变量覆盖。

    返回一个包含必要字段的字典。
    """
    cfg = {}
    if yaml and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"load_config: 读取 {path} 失败：{e}")
            cfg = {}

    # config.yaml 中的 initiative 字段为主命名空间
    ini = cfg.get("initiative", {}) if isinstance(cfg, dict) else {}

    # 环境变量覆盖
    cfg_out = {}
    cfg_out["astrbot_url"] = os.getenv("ASTRBOT_URL", ini.get("astrbot_url", "http://127.0.0.1:11451"))
    cfg_out["onebot_url"] = os.getenv("ONEBOT_URL", ini.get("onebot_url", "http://127.0.0.1:3000"))
    cfg_out["api_type"] = os.getenv("API_TYPE", ini.get("api_type", "astrbot"))
    cfg_out["target_user_qq"] = os.getenv("TARGET_USER_QQ", ini.get("target_user_qq", 0))
    cfg_out["min_check_seconds"] = int(os.getenv("MIN_CHECK_SECONDS", str(ini.get("min_check_seconds", 300))))
    cfg_out["max_check_seconds"] = int(os.getenv("MAX_CHECK_SECONDS", str(ini.get("max_check_seconds", 900))))
    cfg_out["check_randomize"] = ini.get("check_randomize", True)
    cfg_out["max_backoff_multiplier"] = float(os.getenv("MAX_BACKOFF_MULTIPLIER", str(ini.get("max_backoff_multiplier", 4.0))))
    cfg_out["request_timeout"] = float(os.getenv("REQUEST_TIMEOUT", str(ini.get("request_timeout", 8.0))))

    return cfg_out


def send_private_msg_astrbot(api_url: str, user_id: str, message: str, timeout: float = 8.0) -> bool:
    """通过 AstrBot HTTP API 发送私聊消息，action=send_private_msg。"""
    payload = {
        "action": "send_private_msg",
        "params": {
            "user_id": int(user_id),
            "message": message,
        }
    }
    try:
        r = requests.post(api_url, json=payload, timeout=timeout)
        r.raise_for_status()
        logger.info(f"[AstrBot] 已发送给 {user_id}: {message[:60]!r}")
        return True
    except Exception as e:
        logger.exception(f"send_private_msg_astrbot 失败: {e}")
        return False


def send_private_msg_onebot(api_url: str, user_id: str, message: str, timeout: float = 8.0) -> bool:
    """通过 OneBot 标准 HTTP 接口发送私聊消息（POST /send_private_msg）。"""
    try:
        r = requests.post(f"{api_url.rstrip('/')}/send_private_msg", json={"user_id": int(user_id), "message": message}, timeout=timeout)
        r.raise_for_status()
        logger.info(f"[OneBot] 已发送给 {user_id}: {message[:60]!r}")
        return True
    except Exception as e:
        logger.exception(f"send_private_msg_onebot 失败: {e}")
        return False


def main_loop(orchestrator: Orchestrator, cfg: dict):
    """主循环：周期性调用 orchestrator.generate_initiative 并在非空时发送。"""
    consecutive_empty = 0
    min_s = cfg.get("min_check_seconds", 300)
    max_s = cfg.get("max_check_seconds", 900)
    max_backoff = cfg.get("max_backoff_multiplier", 4.0)
    target_user = str(cfg.get("target_user_qq", "0"))
    api_type = cfg.get("api_type", "astrbot")
    api_url = cfg.get("astrbot_url") if api_type == "astrbot" else cfg.get("onebot_url")
    req_timeout = cfg.get("request_timeout", 8.0)

    logger.info(f"initiative_sender 启动，target_user={target_user} api_type={api_type} api_url={api_url}")

    while True:
        try:
            # 计算 sleep 时间：先随机化，再根据 consecutive_empty 做 backoff
            base_interval = random.randint(min_s, max_s) if cfg.get("check_randomize", True) else min_s
            backoff = min(max_backoff, 1.0 + consecutive_empty * 0.5)
            sleep_seconds = int(base_interval * backoff)
            logger.debug(f"下次检查间隔 {sleep_seconds}s (base={base_interval} backoff={backoff})")
            time.sleep(sleep_seconds)

            # 调用 orchestrator.generate_initiative（只读，不写历史）
            try:
                msg = orchestrator.generate_initiative(target_user)
            except Exception as e:
                logger.exception(f"调用 generate_initiative 异常: {e}")
                msg = ""

            if msg:
                # 若有多目标 QQ 支持，可按逗号分割
                targets = [t.strip() for t in str(target_user).split(",") if t.strip()]
                success_all = True
                for t in targets:
                    if api_type == "astrbot":
                        ok = send_private_msg_astrbot(api_url, t, msg, timeout=req_timeout)
                    else:
                        ok = send_private_msg_onebot(api_url, t, msg, timeout=req_timeout)
                    success_all = success_all and ok

                if success_all:
                    logger.info("主动消息发送成功")
                    consecutive_empty = 0
                else:
                    logger.warning("主动消息部分或全部发送失败")
                    # 失败不计入 consecutive_empty（认为是传输问题）
            else:
                consecutive_empty += 1
                logger.debug(f"未生成主动消息 (consecutive_empty={consecutive_empty})")

                if consecutive_empty > 10:
                    logger.info("连续多次未生成主动消息，额外休眠以降低调用频率")
                    time.sleep(min_s * 3)

        except KeyboardInterrupt:
            logger.info("initiative_sender 已由用户中断，退出")
            break
        except Exception as e:
            logger.exception(f"主循环发生未捕获异常: {e}")
            time.sleep(10)


if __name__ == "__main__":
    cfg = load_config()
    orch = Orchestrator(config={})
    # 将 target_user_qq 注入 orchestrator 以便某些 assemble_context 使用
    orch.target_user_id = str(cfg.get("target_user_qq", ""))
    main_loop(orch, cfg)
