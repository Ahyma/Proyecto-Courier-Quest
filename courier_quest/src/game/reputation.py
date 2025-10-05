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
    def for_delivery(res: DeliveryResult, courier_reputation=70, is_first_late=False) -> int:
        """
        Calcula el cambio de reputación por entrega.
        
        Args:
            res: Resultado de la entrega
            courier_reputation: Reputación actual del courier
            is_first_late: Si es la primera tardanza del día
        """
        if res.status == "expired":
            return -6
        if res.status == "early":
            return +5
        if res.status == "on_time":
            return +3
        
        # NUEVO: Mitigar primera tardanza si reputación ≥85
        if res.status in ("late_<=30", "late_31_120", "late_>120") and is_first_late and courier_reputation >= 85:
            print("🛡️  Primera tardanza mitigada (reputación ≥85)")
            if res.status == "late_<=30":
                return -1  # Mitigado de -2 a -1
            elif res.status == "late_31_120":
                return -3  # Mitigado de -5 a -3
            elif res.status == "late_>120":
                return -5  # Mitigado de -10 a -5
        
        if res.status == "late_<=30":
            return -2
        if res.status == "late_31_120":
            return -5
        if res.status == "late_>120":
            return -10
        return 0

    @staticmethod
    def for_cancel() -> int:
        """Penalización por cancelar pedido aceptado"""
        return -4

    @staticmethod
    def calculate_delivery_result(pickup_time: float, delivery_time: float, deadline: float) -> DeliveryResult:
        """
        Calcula el resultado de una entrega basado en los tiempos.
        
        Args:
            pickup_time: Tiempo cuando se recogió el pedido
            delivery_time: Tiempo cuando se entregó
            deadline: Tiempo límite para la entrega
            
        Returns:
            DeliveryResult con el estado y métricas
        """
        if delivery_time > deadline:
            # Entrega tardía
            lateness = delivery_time - deadline
            if lateness <= 30:
                status = "late_<=30"
            elif lateness <= 120:
                status = "late_31_120"
            else:
                status = "late_>120"
            early_ratio = 0.0
        else:
            # Entrega a tiempo o temprana
            lateness = delivery_time - deadline  # Negativo si llegó antes
            delivery_window = deadline - pickup_time
            if delivery_window > 0:
                early_ratio = (deadline - delivery_time) / delivery_window
            else:
                early_ratio = 0.0
                
            if early_ratio >= 0.20:  # ≥20% antes
                status = "early"
            else:
                status = "on_time"
        
        return DeliveryResult(
            status=status,
            lateness=lateness,
            early_ratio=early_ratio
        )