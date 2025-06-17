"""
Mock price feed - SOLO PARA TESTING
NO usar en producción - solo para tests unitarios
"""

import random
import asyncio
from typing import Optional


class MockPriceFeed:
    """
    Mock price feed que genera precios aleatorios realistas.
    
    ⚠️  IMPORTANTE: SOLO PARA TESTING
    La aplicación principal NO debe usar este feed.
    Solo está permitido en tests unitarios.
    """
    
    def __init__(self, base_price: float = 200.0, volatility: float = 0.02):
        """
        Args:
            base_price: Precio base alrededor del cual fluctuar
            volatility: Volatilidad (0.02 = 2%)
        """
        self.base_price = base_price
        self.volatility = volatility
        self.current_price = base_price
        
        # Warning para que quede claro que es solo testing
        print("⚠️  MockPriceFeed inicializado - SOLO PARA TESTING")
    
    async def get_price(self) -> Optional[float]:
        """
        Genera un precio mock con movimiento browniano simple.
        
        Returns:
            Precio simulado realista
        """
        # Simular pequeño delay como API real
        await asyncio.sleep(0.01)
        
        # Movimiento browniano simple
        change_pct = random.gauss(0, self.volatility)
        self.current_price *= (1 + change_pct)
        
        # Evitar precios extremos
        if self.current_price < self.base_price * 0.5:
            self.current_price = self.base_price * 0.5
        elif self.current_price > self.base_price * 2.0:
            self.current_price = self.base_price * 2.0
        
        return round(self.current_price, 2)
    
    def reset_price(self, new_base: float = None):
        """Reset price para tests determinísticos"""
        if new_base:
            self.base_price = new_base
        self.current_price = self.base_price