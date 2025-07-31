"""
Logging utilities voor Radio PrideSync
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False

def setup_logger(name, level=logging.INFO, log_to_file=True):
    """
    Setup logger met console en file output
    
    Args:
        name (str): Logger naam
        level (int): Log level
        log_to_file (bool): Of naar bestand loggen
        
    Returns:
        logging.Logger: Geconfigureerde logger
    """
    logger = logging.getLogger(name)
    
    # Voorkom dubbele handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Console handler met kleuren (als beschikbaar)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    if HAS_COLORLOG:
        # Gekleurde console output
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    else:
        # Standaard console formatter
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (als gewenst)
    if log_to_file:
        # Maak logs directory
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Log bestand met datum
        log_filename = f"radio_pridesync_{datetime.now().strftime('%Y%m%d')}.log"
        log_path = log_dir / log_filename
        
        # Rotating file handler (max 10MB, 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # File krijgt alle logs
        
        # File formatter (meer gedetailleerd)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name):
    """
    Krijg bestaande logger of maak nieuwe
    
    Args:
        name (str): Logger naam
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)

def set_log_level(level):
    """
    Stel log level in voor alle loggers
    
    Args:
        level (int): Nieuwe log level
    """
    # Root logger
    logging.getLogger().setLevel(level)
    
    # Alle Radio PrideSync loggers
    for name in logging.getLogger().manager.loggerDict:
        if name.startswith('radio') or name.startswith('audio') or name.startswith('utils'):
            logging.getLogger(name).setLevel(level)

def log_system_info():
    """Log systeem informatie"""
    logger = get_logger(__name__)
    
    try:
        import platform
        import psutil
        
        logger.info("=== Systeem Informatie ===")
        logger.info(f"Platform: {platform.platform()}")
        logger.info(f"Python: {platform.python_version()}")
        logger.info(f"CPU: {platform.processor()}")
        logger.info(f"Geheugen: {psutil.virtual_memory().total / (1024**3):.1f} GB")
        logger.info(f"Schijfruimte: {psutil.disk_usage('/').free / (1024**3):.1f} GB vrij")
        
        # Raspberry Pi specifieke info
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'Model' in line:
                        logger.info(f"RPi Model: {line.split(':')[1].strip()}")
                        break
        except:
            pass
            
        logger.info("========================")
        
    except ImportError:
        logger.debug("psutil niet beschikbaar voor systeem info")
    except Exception as e:
        logger.error(f"Systeem info ophalen gefaald: {e}")

class PerformanceLogger:
    """Context manager voor performance logging"""
    
    def __init__(self, operation_name, logger=None):
        self.operation_name = operation_name
        self.logger = logger or get_logger(__name__)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Start: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.now() - self.start_time
        duration_ms = duration.total_seconds() * 1000
        
        if exc_type is None:
            self.logger.debug(f"Voltooid: {self.operation_name} ({duration_ms:.1f}ms)")
        else:
            self.logger.error(f"Gefaald: {self.operation_name} ({duration_ms:.1f}ms) - {exc_val}")

def log_function_call(func):
    """Decorator voor function call logging"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Aanroep: {func.__name__}({args}, {kwargs})")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Resultaat: {func.__name__} -> {result}")
            return result
        except Exception as e:
            logger.error(f"Fout in {func.__name__}: {e}")
            raise
    
    return wrapper
