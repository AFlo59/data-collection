# setup_logger.py
import os
import logging
from pathlib import Path

def setup_logger(logger_name: str, subfolder: str = None) -> logging.Logger:
    """
    Configure un logger avec des handlers pour fichier et console.
    
    Args:
        logger_name (str): Nom du logger (ex. : 'spells', 'items')
        subfolder (str, optionnel): Chemin du sous-dossier sous le dossier logs (ex. : 'data_extraction/run')
    
    Returns:
        logging.Logger: L'instance configurée du logger
    """
    # Déterminer la racine du projet (3 niveaux au-dessus de ce fichier)
    project_root = Path(__file__).parent.parent.parent
    logs_dir = project_root / 'logs'

    # Créer le dossier principal des logs s'il n'existe pas
    logs_dir.mkdir(exist_ok=True)

    # Créer le sous-dossier si spécifié
    if subfolder:
        # On peut autoriser un chemin multi-niveaux (ex. "data_extraction/run")
        # Remplacer les tirets par des underscores si nécessaire
        subfolder = subfolder.replace('-', '_')
        logs_dir = logs_dir / subfolder
        logs_dir.mkdir(parents=True, exist_ok=True)

    # Créer le logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Eviter d'ajouter plusieurs handlers si le logger a déjà été configuré
    if not logger.handlers:
        # Créer un handler pour le fichier de log
        log_file = logs_dir / f"{logger_name}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # Créer un handler pour la sortie console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Définir les formatteurs pour les handlers
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )

        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)

        # Ajouter les handlers au logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
