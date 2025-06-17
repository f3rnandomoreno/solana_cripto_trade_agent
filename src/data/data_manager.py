"""
Sistema de persistencia de datos para precios de Solana y trading.
Guarda toda la información localmente para análisis histórico.
"""

import sqlite3
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from ..config import settings


@dataclass
class PriceData:
    """Datos de precio con timestamp"""
    timestamp: float
    price: float
    source: str  # "pyth", "jupiter", "aggregated", etc.
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None
    metadata: Optional[Dict] = None


@dataclass
class TradeData:
    """Datos de trade ejecutado o simulado"""
    timestamp: float
    side: str  # "BUY", "SELL"
    amount_sol: float
    price: float
    value_usd: float
    fees_sol: float
    simulation: bool
    slippage_pct: Optional[float] = None
    portfolio_value_before: Optional[float] = None
    portfolio_value_after: Optional[float] = None
    metadata: Optional[Dict] = None


@dataclass
class PortfolioSnapshot:
    """Snapshot del portfolio en un momento dado"""
    timestamp: float
    sol_balance: float
    usd_balance: float
    total_value_usd: float
    realized_pnl: float
    unrealized_pnl: float
    simulation: bool
    metadata: Optional[Dict] = None


class DataManager:
    """
    Gestor de persistencia de datos para el bot de trading.
    Guarda precios, trades y snapshots del portfolio en SQLite.
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Crear directorio data si no existe
            data_dir = Path("data/storage")
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "trading_data.db"
        
        self.db_path = str(db_path)
        self._init_database()
        
        print(f"📊 DataManager inicializado - DB: {self.db_path}")
    
    def _init_database(self):
        """Inicializa las tablas de la base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            # Tabla de precios
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    price REAL NOT NULL,
                    source TEXT NOT NULL,
                    volume_24h REAL,
                    market_cap REAL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de trades
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    side TEXT NOT NULL,
                    amount_sol REAL NOT NULL,
                    price REAL NOT NULL,
                    value_usd REAL NOT NULL,
                    fees_sol REAL NOT NULL,
                    simulation BOOLEAN NOT NULL,
                    slippage_pct REAL,
                    portfolio_value_before REAL,
                    portfolio_value_after REAL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de snapshots del portfolio
            conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    sol_balance REAL NOT NULL,
                    usd_balance REAL NOT NULL,
                    total_value_usd REAL NOT NULL,
                    realized_pnl REAL NOT NULL,
                    unrealized_pnl REAL NOT NULL,
                    simulation BOOLEAN NOT NULL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para consultas rápidas
            conn.execute("CREATE INDEX IF NOT EXISTS idx_price_timestamp ON price_data(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trade_timestamp ON trade_data(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_timestamp ON portfolio_snapshots(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_price_source ON price_data(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trade_simulation ON trade_data(simulation)")
            
            conn.commit()
    
    def save_price_data(self, price: float, source: str, volume_24h: float = None, 
                       market_cap: float = None, metadata: Dict = None) -> bool:
        """Guarda datos de precio"""
        try:
            price_data = PriceData(
                timestamp=time.time(),
                price=price,
                source=source,
                volume_24h=volume_24h,
                market_cap=market_cap,
                metadata=metadata
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO price_data 
                    (timestamp, price, source, volume_24h, market_cap, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    price_data.timestamp,
                    price_data.price,
                    price_data.source,
                    price_data.volume_24h,
                    price_data.market_cap,
                    json.dumps(price_data.metadata) if price_data.metadata else None
                ))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"❌ Error guardando precio: {e}")
            return False
    
    def save_trade_data(self, side: str, amount_sol: float, price: float, 
                       value_usd: float, fees_sol: float, simulation: bool,
                       slippage_pct: float = None, portfolio_value_before: float = None,
                       portfolio_value_after: float = None, metadata: Dict = None) -> bool:
        """Guarda datos de trade"""
        try:
            trade_data = TradeData(
                timestamp=time.time(),
                side=side,
                amount_sol=amount_sol,
                price=price,
                value_usd=value_usd,
                fees_sol=fees_sol,
                simulation=simulation,
                slippage_pct=slippage_pct,
                portfolio_value_before=portfolio_value_before,
                portfolio_value_after=portfolio_value_after,
                metadata=metadata
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO trade_data 
                    (timestamp, side, amount_sol, price, value_usd, fees_sol, simulation,
                     slippage_pct, portfolio_value_before, portfolio_value_after, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_data.timestamp,
                    trade_data.side,
                    trade_data.amount_sol,
                    trade_data.price,
                    trade_data.value_usd,
                    trade_data.fees_sol,
                    trade_data.simulation,
                    trade_data.slippage_pct,
                    trade_data.portfolio_value_before,
                    trade_data.portfolio_value_after,
                    json.dumps(trade_data.metadata) if trade_data.metadata else None
                ))
                conn.commit()
            
            print(f"💾 Trade guardado: {side} {amount_sol:.4f} SOL @ ${price} ({'SIM' if simulation else 'REAL'})")
            return True
        except Exception as e:
            print(f"❌ Error guardando trade: {e}")
            return False
    
    def save_portfolio_snapshot(self, sol_balance: float, usd_balance: float,
                              total_value_usd: float, realized_pnl: float,
                              unrealized_pnl: float, simulation: bool,
                              metadata: Dict = None) -> bool:
        """Guarda snapshot del portfolio"""
        try:
            snapshot = PortfolioSnapshot(
                timestamp=time.time(),
                sol_balance=sol_balance,
                usd_balance=usd_balance,
                total_value_usd=total_value_usd,
                realized_pnl=realized_pnl,
                unrealized_pnl=unrealized_pnl,
                simulation=simulation,
                metadata=metadata
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO portfolio_snapshots 
                    (timestamp, sol_balance, usd_balance, total_value_usd, 
                     realized_pnl, unrealized_pnl, simulation, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot.timestamp,
                    snapshot.sol_balance,
                    snapshot.usd_balance,
                    snapshot.total_value_usd,
                    snapshot.realized_pnl,
                    snapshot.unrealized_pnl,
                    snapshot.simulation,
                    json.dumps(snapshot.metadata) if snapshot.metadata else None
                ))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"❌ Error guardando snapshot del portfolio: {e}")
            return False
    
    def get_price_history(self, source: str = None, hours: int = 24) -> List[Dict]:
        """Obtiene historial de precios"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                if source:
                    cursor = conn.execute("""
                        SELECT timestamp, price, source, volume_24h, market_cap, metadata
                        FROM price_data 
                        WHERE timestamp > ? AND source = ?
                        ORDER BY timestamp ASC
                    """, (cutoff_time, source))
                else:
                    cursor = conn.execute("""
                        SELECT timestamp, price, source, volume_24h, market_cap, metadata
                        FROM price_data 
                        WHERE timestamp > ?
                        ORDER BY timestamp ASC
                    """, (cutoff_time,))
                
                rows = cursor.fetchall()
                
                return [
                    {
                        "timestamp": row[0],
                        "price": row[1],
                        "source": row[2],
                        "volume_24h": row[3],
                        "market_cap": row[4],
                        "metadata": json.loads(row[5]) if row[5] else None,
                        "datetime": datetime.fromtimestamp(row[0], tz=timezone.utc).isoformat()
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"❌ Error obteniendo historial de precios: {e}")
            return []
    
    def get_trade_history(self, simulation: bool = None, hours: int = 24) -> List[Dict]:
        """Obtiene historial de trades"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                if simulation is not None:
                    cursor = conn.execute("""
                        SELECT * FROM trade_data 
                        WHERE timestamp > ? AND simulation = ?
                        ORDER BY timestamp ASC
                    """, (cutoff_time, simulation))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM trade_data 
                        WHERE timestamp > ?
                        ORDER BY timestamp ASC
                    """, (cutoff_time,))
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                return [
                    dict(zip(columns, row))
                    for row in rows
                ]
        except Exception as e:
            print(f"❌ Error obteniendo historial de trades: {e}")
            return []
    
    def get_portfolio_history(self, simulation: bool = None, hours: int = 24) -> List[Dict]:
        """Obtiene historial del portfolio"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                if simulation is not None:
                    cursor = conn.execute("""
                        SELECT * FROM portfolio_snapshots 
                        WHERE timestamp > ? AND simulation = ?
                        ORDER BY timestamp ASC
                    """, (cutoff_time, simulation))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM portfolio_snapshots 
                        WHERE timestamp > ?
                        ORDER BY timestamp ASC
                    """, (cutoff_time,))
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                return [
                    dict(zip(columns, row))
                    for row in rows
                ]
        except Exception as e:
            print(f"❌ Error obteniendo historial del portfolio: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                # Estadísticas de precios
                cursor = conn.execute("SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM price_data")
                price_count, price_min_ts, price_max_ts = cursor.fetchone()
                stats["price_data"] = {
                    "total_records": price_count,
                    "first_record": datetime.fromtimestamp(price_min_ts, tz=timezone.utc).isoformat() if price_min_ts else None,
                    "last_record": datetime.fromtimestamp(price_max_ts, tz=timezone.utc).isoformat() if price_max_ts else None
                }
                
                # Estadísticas de trades
                cursor = conn.execute("SELECT COUNT(*), simulation FROM trade_data GROUP BY simulation")
                trade_stats = {row[1]: row[0] for row in cursor.fetchall()}
                stats["trade_data"] = trade_stats
                
                # Estadísticas del portfolio
                cursor = conn.execute("SELECT COUNT(*) FROM portfolio_snapshots")
                portfolio_count = cursor.fetchone()[0]
                stats["portfolio_snapshots"] = {"total_records": portfolio_count}
                
                # Tamaño de la base de datos
                db_size = os.path.getsize(self.db_path)
                stats["database"] = {
                    "file_size_mb": round(db_size / (1024 * 1024), 2),
                    "path": self.db_path
                }
                
                return stats
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas: {e}")
            return {}
    
    def export_data(self, filepath: str, format: str = "json") -> bool:
        """Exporta todos los datos a un archivo"""
        try:
            data = {
                "exported_at": datetime.now(tz=timezone.utc).isoformat(),
                "statistics": self.get_statistics(),
                "price_history": self.get_price_history(hours=24*30),  # 30 días
                "trade_history": self.get_trade_history(hours=24*30),
                "portfolio_history": self.get_portfolio_history(hours=24*30)
            }
            
            if format.lower() == "json":
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            else:
                raise ValueError(f"Formato no soportado: {format}")
            
            print(f"📤 Datos exportados a: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error exportando datos: {e}")
            return False
    
    def cleanup_old_data(self, days: int = 30) -> bool:
        """Limpia datos antiguos"""
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                # Contar registros antes
                cursor = conn.execute("SELECT COUNT(*) FROM price_data WHERE timestamp < ?", (cutoff_time,))
                old_price_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM trade_data WHERE timestamp < ?", (cutoff_time,))
                old_trade_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM portfolio_snapshots WHERE timestamp < ?", (cutoff_time,))
                old_portfolio_count = cursor.fetchone()[0]
                
                # Limpiar datos antiguos
                conn.execute("DELETE FROM price_data WHERE timestamp < ?", (cutoff_time,))
                conn.execute("DELETE FROM trade_data WHERE timestamp < ?", (cutoff_time,))
                conn.execute("DELETE FROM portfolio_snapshots WHERE timestamp < ?", (cutoff_time,))
                
                conn.commit()
                
                print(f"🧹 Limpieza completada - Eliminados {old_price_count} precios, {old_trade_count} trades, {old_portfolio_count} snapshots")
                return True
        except Exception as e:
            print(f"❌ Error limpiando datos: {e}")
            return False


# Instancia global del gestor de datos
data_manager = DataManager()