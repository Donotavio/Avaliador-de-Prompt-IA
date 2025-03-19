from datetime import datetime
from typing import Dict, Tuple, Any
from config.settings import USAGE_LIMITS


class UserUsage:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.premium_evaluations_count = 0
        self.free_evaluations_count = 0
        self.premium_activations_count = 0
        self.last_evaluation_date = None
        self.is_premium_active = False
        self.last_payment_date = None

    def can_use_premium(self) -> Tuple[bool, str, bool]:
        """
        Verifica se o usuário pode usar o plano premium.

        Returns:
            Tuple[bool, str, bool]: (pode_usar, mensagem, expirou)
                - pode_usar: Se o usuário pode usar o plano premium
                - mensagem: Mensagem explicativa
                - expirou: Se o plano premium expirou (atingiu limite de ativações)
        """
        if not self.is_premium_active:
            return False, "Plano premium não está ativo", False

        return True, "Uso ilimitado (Plano Premium)", False

    def can_use_free(self) -> Tuple[bool, str]:
        """Verifica se o usuário pode usar o plano gratuito"""
        today = datetime.now().date()
        if self.last_evaluation_date is None or self.last_evaluation_date.date() < today:
            self.free_evaluations_count = 0
            # Não retornar mensagem de status para uso normal
            return True, ""

        if self.free_evaluations_count >= USAGE_LIMITS["free"]["daily_limit"]:
            return (
                False,
                f"Limite diário de {USAGE_LIMITS['free']['daily_limit']} avaliações gratuitas atingido",
            )

        # Não retornar mensagem de status para uso normal
        return True, ""

    def increment_premium_usage(self):
        """Incrementa o contador de uso premium"""
        self.premium_evaluations_count += 1
        self.last_evaluation_date = datetime.now()

    def increment_free_usage(self):
        """Incrementa o contador de uso gratuito"""
        self.free_evaluations_count += 1
        self.last_evaluation_date = datetime.now()

    def activate_premium(self):
        """Ativa o plano premium após pagamento"""
        self.is_premium_active = True
        self.last_payment_date = datetime.now()
        self.premium_evaluations_count = 0

    def reset_usage(self) -> None:
        self.premium_evaluations_count = 0
        self.free_evaluations_count = 0
        self.last_evaluation_date = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte o objeto para dicionário para serialização"""
        return {
            "user_id": self.user_id,
            "premium_evaluations_count": self.premium_evaluations_count,
            "free_evaluations_count": self.free_evaluations_count,
            "premium_activations_count": self.premium_activations_count,
            "last_evaluation_date": self.last_evaluation_date.isoformat()
            if self.last_evaluation_date
            else None,
            "is_premium_active": self.is_premium_active,
            "last_payment_date": self.last_payment_date.isoformat()
            if self.last_payment_date
            else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserUsage":
        """Cria uma instância a partir de um dicionário"""
        if "user_id" not in data:
            raise ValueError("user_id é obrigatório")

        instance = cls(user_id=data["user_id"])
        instance.premium_evaluations_count = data.get("premium_evaluations_count", 0)
        instance.free_evaluations_count = data.get("free_evaluations_count", 0)
        instance.premium_activations_count = data.get("premium_activations_count", 0)

        last_eval_date = data.get("last_evaluation_date")
        if last_eval_date:
            instance.last_evaluation_date = datetime.fromisoformat(last_eval_date)

        instance.is_premium_active = data.get("is_premium_active", False)

        last_payment_date = data.get("last_payment_date")
        if last_payment_date:
            instance.last_payment_date = datetime.fromisoformat(last_payment_date)

        return instance
