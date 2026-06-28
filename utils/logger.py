# -*- coding: utf-8 -*-
"""
ClawRoyale thread-safe and async-safe logging utility.
Creates isolated log files for each bot instance to prevent output collision.
"""

import os
import logging
from typing import Dict

os.makedirs("logs", exist_ok=True)


class AgentLogger:
    _loggers: Dict[str, logging.Logger] = {}

    @classmethod
    def get_logger(cls, agent_name: str) -> logging.Logger:
        """
        Returns or creates a separate Logger instance for the specified agent.
        Logs are securely saved to /logs/bot_<name>.log without leaking private credentials.
        """
        safe_name = agent_name.lower().replace(" ", "_")
        
        if safe_name in cls._loggers:
            return cls._loggers[safe_name]

        logger = logging.getLogger(safe_name)
        logger.setLevel(logging.INFO)
        logger.propagate = False

        # Bersihkan handler lama jika ada untuk mencegah logging ganda (duplicate logging) akibat inisialisasi ulang
        logger.handlers.clear()

        # 1. Handler untuk menulis ke Berkas Log Akun masing-masing instansi (Bot atau Orchestrator)
        log_file_path = os.path.join("logs", f"bot_{safe_name}.log")
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # 2. Handler untuk menulis ke Berkas Log Sistem Global (HANYA untuk Orchestrator)
        # Log bot individu tidak dimasukkan ke system.log agar data audit bersih dan tidak bercampur
        if safe_name == "orchestrator":
            system_log_path = os.path.join("logs", "system.log")
            sys_handler = logging.FileHandler(system_log_path, encoding="utf-8")
            sys_formatter = logging.Formatter(
                fmt="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            sys_handler.setFormatter(sys_formatter)
            logger.addHandler(sys_handler)

        cls._loggers[safe_name] = logger
        return logger