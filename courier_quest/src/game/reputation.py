from dataclasses import dataclass

@dataclass
class DeliveryResult:
    """
    Resultado de una entrega con métricas de puntualidad.
    
    Attributes:
        status: Categoría de puntualidad
        lateness: Segundos de tardanza (negativo si llegó antes)
        early_ratio: Porcentaje de anticipación (0-1)
    """
    status: str        # "early" | "on_time" | "late_<=30" | "late_31_120" | "late_>120" | "expired"
    lateness: float    # seg (negativo si llegó antes)
    early_ratio: float # fracción de anticipo respecto a la ventana (0..1)

class ReputationSystem:
    """
    Sistema de gestión de reputación para el repartidor.
    
    Tabla de puntuación:
      +3  entrega a tiempo
      +5  entrega temprana (≥20% antes)
      -2  ≤30 s tarde
      -5  31–120 s tarde
      -10 >120 s tarde
      -4  cancelar pedido aceptado
      -6  perder/expirar paquete
      +2  racha 3 entregas sin penalización
      Bono +5% en pagos si reputación ≥90
      Derrota si reputación <20
    """

    @staticmethod
    def for_delivery(res: DeliveryResult, courier_reputation=70, is_first_late=False) -> int:
        """
        Calcula el cambio de reputación por una entrega.
        
        Args:
            res: Resultado de la entrega con métricas
            courier_reputation: Reputación actual del repartidor
            is_first_late: Si es la primera entrega tardía del día
            
        Returns:
            Cambio de reputación (-10 a +5)
        """
        # Pedido expirado (no entregado a tiempo)
        if res.status == "expired":
            return -6
            
        # Entrega temprana (≥20% antes del tiempo previsto)
        if res.status == "early":
            return +5
            
        # Entrega a tiempo
        if res.status == "on_time":
            return +3
        
        # NUEVO: Mitigar primera tardanza si reputación es alta (≥85)
        if res.status in ("late_<=30", "late_31_120", "late_>120") and is_first_late and courier_reputation >= 85:
            print("🛡️  Primera tardanza mitigada (reputación ≥85)")
            if res.status == "late_<=30":
                return -1  # Mitigado de -2 a -1
            elif res.status == "late_31_120":
                return -3  # Mitigado de -5 a -3
            elif res.status == "late_>120":
                return -5  # Mitigado de -10 a -5
        
        # Aplicar penalizaciones normales por tardanza
        if res.status == "late_<=30":
            return -2
        if res.status == "late_31_120":
            return -5
        if res.status == "late_>120":
            return -10
            
        return 0  # Caso por defecto

    @staticmethod
    def for_cancel() -> int:
        """
        Penalización por cancelar un pedido aceptado.
        
        Returns:
            -4 puntos de reputación
        """
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
            DeliveryResult con estado y métricas
        """
        # Entrega tardía
        if delivery_time > deadline:
            lateness = delivery_time - deadline
            if lateness <= 30:
                status = "late_<=30"
            elif lateness <= 120:
                status = "late_31_120"
            else:
                status = "late_>120"
            early_ratio = 0.0  # No aplica para entregas tardías
        else:
            # Entrega a tiempo o temprana
            lateness = delivery_time - deadline  # Negativo si llegó antes
            delivery_window = deadline - pickup_time  # Tiempo total disponible
            
            if delivery_window > 0:
                early_ratio = (deadline - delivery_time) / delivery_window
            else:
                early_ratio = 0.0
                
            # Clasificar como temprana si llegó ≥20% antes
            if early_ratio >= 0.20:
                status = "early"
            else:
                status = "on_time"
        
        return DeliveryResult(
            status=status,
            lateness=lateness,
            early_ratio=early_ratio
        )