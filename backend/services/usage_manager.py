import json
import os
from typing import Dict, Tuple
from models.user_usage import UserUsage
from config.settings import USAGE_LIMITS
from utils.logger import logger


class UsageManager:
    def __init__(self):
        self.user_usage: Dict[str, UserUsage] = {}
        self.storage_file = "user_usage.json"
        self._load_data()

    def _load_data(self):
        """Carrega os dados do arquivo"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, "r") as f:
                    data = json.load(f)
                    for user_id, usage_data in data.items():
                        self.user_usage[user_id] = UserUsage.from_dict(usage_data)
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {str(e)}")

    def _save_data(self):
        """Salva os dados no arquivo"""
        try:
            data = {
                user_id: usage.to_dict() for user_id, usage in self.user_usage.items()
            }
            with open(self.storage_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {str(e)}")

    def get_user_usage(self, user_id: str) -> UserUsage:
        """Obtém ou cria o controle de uso para um usuário"""
        if user_id not in self.user_usage:
            self.user_usage[user_id] = UserUsage(user_id=user_id)
            self._save_data()
            logger.info(f"Novo usuário criado: {user_id}")
        return self.user_usage[user_id]

    def _get_or_create_user(self, user_id: str) -> UserUsage:
        if user_id not in self.user_usage:
            self.user_usage[user_id] = UserUsage(user_id=user_id)
            self._save_data()
            logger.info(f"Novo usuário criado: {user_id}")
        return self.user_usage[user_id]

    def can_use_premium(self, user_id: str) -> Tuple[bool, str, bool]:
        """
        Verifica se o usuário pode usar o plano premium.

        Args:
            user_id: ID do usuário

        Returns:
            Tuple[bool, str, bool]: (pode_usar, mensagem, expirou)
                - pode_usar: Se o usuário pode usar o plano premium
                - mensagem: Mensagem explicativa
                - expirou: Se o plano premium expirou (atingiu limite de ativações)
        """
        user = self._get_or_create_user(user_id)
        can_use, message, has_expired = user.can_use_premium()

        if (
            not can_use
            and user.premium_activations_count
            >= USAGE_LIMITS["premium"]["max_activations"]
        ):
            return (
                False,
                "Limite de ativações premium atingido. Assine o plano premium para continuar.",
                True,
            )

        if not can_use:
            logger.info(f"Usuário {user_id} não pode usar premium: {message}")
        return can_use, message, has_expired

    def can_use_free(self, user_id: str) -> Tuple[bool, str]:
        """Verifica se o usuário pode usar o plano gratuito"""
        user = self._get_or_create_user(user_id)
        can_use, message = user.can_use_free()
        if not can_use:
            logger.info(f"Usuário {user_id} não pode usar plano gratuito: {message}")
        return can_use, message

    def register_premium_usage(self, user_id: str):
        """Registra um uso do plano premium"""
        user = self._get_or_create_user(user_id)
        user.increment_premium_usage()
        self._save_data()
        logger.info(f"Uso premium registrado para usuário {user_id}")

    def register_free_usage(self, user_id: str):
        """Registra um uso do plano gratuito"""
        user = self._get_or_create_user(user_id)
        user.increment_free_usage()
        self._save_data()
        logger.info(f"Uso gratuito registrado para usuário {user_id}")

    def activate_premium(self, user_id: str):
        """Ativa o plano premium para um usuário"""
        user = self._get_or_create_user(user_id)

        if user.premium_activations_count >= USAGE_LIMITS["premium"]["max_activations"]:
            logger.warning(
                f"Usuário {user_id} tentou ativar premium após atingir o limite"
            )
            raise ValueError("premium_expired")

        user.activate_premium()
        user.premium_activations_count += 1
        self._save_data()
        logger.info(f"Plano premium ativado para usuário {user_id}")

    def reset_premium_usage(self, user_id: str):
        """Reseta o uso premium de um usuário"""
        if user_id in self.user_usage:
            self.user_usage[user_id].reset_usage()
            self._save_data()
            logger.info(f"Uso premium resetado para usuário {user_id}")
            return {"message": "Uso premium resetado com sucesso"}


usage_manager = UsageManager()
