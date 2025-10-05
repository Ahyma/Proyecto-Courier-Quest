from dataclasses import dataclass

@dataclass
class DeliveryResult:
    status: str        # "early" | "on_time" | "late_<=30" | "late_31_120" | "late_>120" | "expired"
    lateness: float    # seg (negativo si llegó antes)
    early_ratio: float # fracción de anticipo respecto a la ventana (0..1)

class ReputationSystem:
    """
    Tabla pedida:
      +3  entrega a tiempo
      +5  entrega temprana (≥20% antes)
      -2  ≤30 s tarde
      -5  31–120 s tarde
      -10 >120 s tarde
      -4  cancelar pedido aceptado  (función for_cancel)
      -6  perder/expirar paquete    (se usa si corresponde)
      +2  racha 3 entregas sin penalización (se maneja en Courier.update_reputation)
      Bono pagos +5% si reputación ≥90 (lo aplica el main al cobrar)
      Derrota si reputación <20 (lo verifica el main)
    """

    @staticmethod
    def for_delivery(res: DeliveryResult, base_delta=0) -> int:
        if res.status == "expired":
            return -6
        if res.status == "early":
            return +5
        if res.status == "on_time":
            return +3
        if res.status == "late_<=30":
            return -2
        if res.status == "late_31_120":
            return -5
        if res.status == "late_>120":
            return -10
        return base_delta

    @staticmethod
    def for_cancel() -> int:
        return -4
