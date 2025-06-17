"""
Utilidades para análisis de datos históricos y reporting.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from ..data.data_manager import data_manager

# Optional imports for advanced analytics
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def generate_trading_report(hours: int = 24, export_path: str = None) -> Dict:
    """
    Genera un reporte completo de trading con análisis de performance.
    
    Args:
        hours: Horas de historial a analizar
        export_path: Ruta donde guardar el reporte (opcional)
    
    Returns:
        Dict con el reporte completo
    """
    print(f"📊 Generando reporte de trading para las últimas {hours} horas...")
    
    # Obtener datos históricos
    price_history = data_manager.get_price_history(hours=hours)
    trade_history = data_manager.get_trade_history(hours=hours)
    portfolio_history = data_manager.get_portfolio_history(hours=hours)
    stats = data_manager.get_statistics()
    
    # Análisis de precios
    price_analysis = analyze_price_data(price_history)
    
    # Análisis de trading
    trading_analysis = analyze_trading_performance(trade_history, portfolio_history)
    
    # Compilar reporte
    report = {
        "generated_at": datetime.now().isoformat(),
        "period_hours": hours,
        "database_stats": stats,
        "price_analysis": price_analysis,
        "trading_analysis": trading_analysis,
        "raw_data": {
            "price_count": len(price_history),
            "trade_count": len(trade_history),
            "portfolio_snapshots": len(portfolio_history)
        }
    }
    
    # Exportar si se especifica ruta
    if export_path:
        with open(export_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"📤 Reporte exportado a: {export_path}")
    
    return report


def analyze_price_data(price_history: List[Dict]) -> Dict:
    """Analiza datos históricos de precios"""
    if not price_history:
        return {"error": "No hay datos de precios disponibles"}
    
    prices = [p["price"] for p in price_history]
    timestamps = [p["timestamp"] for p in price_history]
    
    if len(prices) < 2:
        return {"error": "Insuficientes datos para análisis"}
    
    # Estadísticas básicas
    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / len(prices)
    current_price = prices[-1]
    
    # Cambios de precio
    price_change = current_price - prices[0]
    price_change_pct = (price_change / prices[0]) * 100 if prices[0] > 0 else 0
    
    # Volatilidad (desviación estándar)
    variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
    volatility = variance ** 0.5
    volatility_pct = (volatility / avg_price) * 100 if avg_price > 0 else 0
    
    # Análisis de tendencia (simple)
    mid_point = len(prices) // 2
    first_half_avg = sum(prices[:mid_point]) / mid_point if mid_point > 0 else 0
    second_half_avg = sum(prices[mid_point:]) / (len(prices) - mid_point)
    trend = "ALCISTA" if second_half_avg > first_half_avg else "BAJISTA"
    
    return {
        "data_points": len(prices),
        "period_start": datetime.fromtimestamp(timestamps[0]).isoformat(),
        "period_end": datetime.fromtimestamp(timestamps[-1]).isoformat(),
        "min_price": round(min_price, 4),
        "max_price": round(max_price, 4),
        "avg_price": round(avg_price, 4),
        "current_price": round(current_price, 4),
        "price_change": round(price_change, 4),
        "price_change_pct": round(price_change_pct, 2),
        "volatility": round(volatility, 4),
        "volatility_pct": round(volatility_pct, 2),
        "trend": trend
    }


def analyze_trading_performance(trade_history: List[Dict], portfolio_history: List[Dict]) -> Dict:
    """Analiza performance de trading"""
    if not trade_history:
        return {"message": "No hay trades para analizar"}
    
    # Separar trades por simulación vs real
    sim_trades = [t for t in trade_history if t.get("simulation")]
    real_trades = [t for t in trade_history if not t.get("simulation")]
    
    # Análisis por tipo
    analysis = {
        "total_trades": len(trade_history),
        "simulation_trades": len(sim_trades),
        "real_trades": len(real_trades)
    }
    
    if sim_trades:
        analysis["simulation_analysis"] = _analyze_trade_set(sim_trades)
    
    if real_trades:
        analysis["real_analysis"] = _analyze_trade_set(real_trades)
    
    # Análisis de portfolio si hay datos
    if portfolio_history:
        analysis["portfolio_analysis"] = _analyze_portfolio_performance(portfolio_history)
    
    return analysis


def _analyze_trade_set(trades: List[Dict]) -> Dict:
    """Analiza un conjunto de trades"""
    if not trades:
        return {}
    
    buy_trades = [t for t in trades if t["side"] == "BUY"]
    sell_trades = [t for t in trades if t["side"] == "SELL"]
    
    total_volume_sol = sum(t["amount_sol"] for t in trades)
    total_volume_usd = sum(t["value_usd"] for t in trades)
    
    total_fees = sum(t.get("fees_sol", 0) for t in trades)
    
    # Precio promedio de compras y ventas
    avg_buy_price = sum(t["price"] for t in buy_trades) / len(buy_trades) if buy_trades else 0
    avg_sell_price = sum(t["price"] for t in sell_trades) / len(sell_trades) if sell_trades else 0
    
    return {
        "total_trades": len(trades),
        "buy_trades": len(buy_trades),
        "sell_trades": len(sell_trades),
        "total_volume_sol": round(total_volume_sol, 4),
        "total_volume_usd": round(total_volume_usd, 2),
        "total_fees_sol": round(total_fees, 4),
        "avg_buy_price": round(avg_buy_price, 2),
        "avg_sell_price": round(avg_sell_price, 2),
        "avg_trade_size_sol": round(total_volume_sol / len(trades), 4) if trades else 0
    }


def _analyze_portfolio_performance(portfolio_history: List[Dict]) -> Dict:
    """Analiza performance del portfolio"""
    if len(portfolio_history) < 2:
        return {"error": "Insuficientes snapshots para análisis"}
    
    first_snapshot = portfolio_history[0]
    last_snapshot = portfolio_history[-1]
    
    # Cambio en valor total
    initial_value = first_snapshot.get("total_value_usd", 0)
    final_value = last_snapshot.get("total_value_usd", 0)
    
    total_return = final_value - initial_value
    total_return_pct = (total_return / initial_value) * 100 if initial_value > 0 else 0
    
    # P&L acumulado
    final_realized_pnl = last_snapshot.get("realized_pnl", 0)
    final_unrealized_pnl = last_snapshot.get("unrealized_pnl", 0)
    total_pnl = final_realized_pnl + final_unrealized_pnl
    
    # Máximo y mínimo valor del portfolio
    all_values = [s.get("total_value_usd", 0) for s in portfolio_history]
    max_value = max(all_values)
    min_value = min(all_values)
    
    # Drawdown máximo
    max_drawdown = 0
    peak_value = 0
    
    for value in all_values:
        if value > peak_value:
            peak_value = value
        drawdown = (peak_value - value) / peak_value if peak_value > 0 else 0
        max_drawdown = max(max_drawdown, drawdown)
    
    return {
        "snapshots_analyzed": len(portfolio_history),
        "initial_value": round(initial_value, 4),
        "final_value": round(final_value, 4),
        "total_return": round(total_return, 4),
        "total_return_pct": round(total_return_pct, 2),
        "realized_pnl": round(final_realized_pnl, 4),
        "unrealized_pnl": round(final_unrealized_pnl, 4),
        "total_pnl": round(total_pnl, 4),
        "max_value": round(max_value, 4),
        "min_value": round(min_value, 4),
        "max_drawdown_pct": round(max_drawdown * 100, 2)
    }


def export_data_for_analysis(filepath: str = None) -> str:
    """
    Exporta todos los datos en formato CSV para análisis externo.
    
    Returns:
        Ruta del archivo exportado
    """
    if filepath is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"data/exports/trading_data_{timestamp}.json"
    
    # Crear directorio si no existe
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    # Exportar usando el data_manager
    success = data_manager.export_data(filepath)
    
    if success:
        print(f"📊 Datos exportados para análisis: {filepath}")
        return filepath
    else:
        print("❌ Error exportando datos")
        return None


def backup_database(backup_path: str = None) -> str:
    """
    Crea backup de la base de datos.
    
    Returns:
        Ruta del backup creado
    """
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"data/backups/trading_db_backup_{timestamp}.db"
    
    # Crear directorio si no existe
    Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Copiar archivo de base de datos
        import shutil
        shutil.copy2(data_manager.db_path, backup_path)
        
        print(f"💾 Backup creado: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Error creando backup: {e}")
        return None


def print_quick_stats():
    """Imprime estadísticas rápidas de la base de datos"""
    stats = data_manager.get_statistics()
    
    print("\n📊 ESTADÍSTICAS DE LA BASE DE DATOS")
    print("=" * 50)
    
    # Estadísticas de precios
    price_stats = stats.get("price_data", {})
    print(f"💰 Datos de Precios:")
    print(f"  Total registros: {price_stats.get('total_records', 0)}")
    print(f"  Primer registro: {price_stats.get('first_record', 'N/A')}")
    print(f"  Último registro: {price_stats.get('last_record', 'N/A')}")
    
    # Estadísticas de trades
    trade_stats = stats.get("trade_data", {})
    print(f"\n🔄 Datos de Trading:")
    sim_trades = trade_stats.get(True, 0)  # True = simulation
    real_trades = trade_stats.get(False, 0)  # False = real
    print(f"  Trades simulados: {sim_trades}")
    print(f"  Trades reales: {real_trades}")
    print(f"  Total trades: {sim_trades + real_trades}")
    
    # Estadísticas del portfolio
    portfolio_stats = stats.get("portfolio_snapshots", {})
    print(f"\n📈 Snapshots de Portfolio:")
    print(f"  Total snapshots: {portfolio_stats.get('total_records', 0)}")
    
    # Info de la base de datos
    db_stats = stats.get("database", {})
    print(f"\n💾 Base de Datos:")
    print(f"  Tamaño: {db_stats.get('file_size_mb', 0)} MB")
    print(f"  Ubicación: {db_stats.get('path', 'N/A')}")
    
    print("=" * 50)


if __name__ == "__main__":
    # Ejemplo de uso
    print_quick_stats()
    
    # Generar reporte de las últimas 24 horas
    report = generate_trading_report(hours=24)
    print(f"\n🎯 Reporte generado con {report['raw_data']['trade_count']} trades")