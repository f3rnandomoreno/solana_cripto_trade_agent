#!/usr/bin/env python3
"""
Script para visualizar los datos guardados de trading.
Útil para revisar historial de precios, trades y performance.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.data_manager import data_manager
from src.utils.data_analytics import print_quick_stats, generate_trading_report, export_data_for_analysis
import json


def main():
    print("📊 VISOR DE DATOS DE TRADING")
    print("=" * 60)
    
    while True:
        print("\nOpciones disponibles:")
        print("1. 📈 Ver estadísticas rápidas")
        print("2. 💰 Ver historial de precios (últimas 24h)")
        print("3. 🔄 Ver historial de trades")
        print("4. 📊 Ver snapshots del portfolio")
        print("5. 📋 Generar reporte completo")
        print("6. 📤 Exportar datos para análisis")
        print("7. 🧹 Limpiar datos antiguos")
        print("0. ❌ Salir")
        
        choice = input("\nSelecciona una opción (0-7): ").strip()
        
        if choice == "0":
            print("👋 ¡Hasta luego!")
            break
        elif choice == "1":
            show_quick_stats()
        elif choice == "2":
            show_price_history()
        elif choice == "3":
            show_trade_history()
        elif choice == "4":
            show_portfolio_history()
        elif choice == "5":
            generate_report()
        elif choice == "6":
            export_data()
        elif choice == "7":
            cleanup_data()
        else:
            print("❌ Opción inválida. Intenta de nuevo.")


def show_quick_stats():
    """Muestra estadísticas rápidas"""
    print("\n" + "="*50)
    print_quick_stats()


def show_price_history(hours=24):
    """Muestra historial de precios"""
    print(f"\n💰 HISTORIAL DE PRECIOS (Últimas {hours}h)")
    print("=" * 50)
    
    price_history = data_manager.get_price_history(hours=hours)
    
    if not price_history:
        print("❌ No hay datos de precios disponibles")
        return
    
    print(f"📊 {len(price_history)} registros de precios encontrados")
    print()
    
    # Mostrar los últimos 10 registros
    recent_prices = price_history[-10:] if len(price_history) > 10 else price_history
    
    print("Últimos precios registrados:")
    print("-" * 70)
    print(f"{'Timestamp':<20} {'Precio':<12} {'Fuente':<15} {'Volumen 24h':<15}")
    print("-" * 70)
    
    for price_data in recent_prices:
        timestamp = price_data["datetime"][:19]  # Remove timezone info for display
        price = f"${price_data['price']:.2f}"
        source = price_data["source"]
        volume = f"${price_data['volume_24h']:,.0f}" if price_data['volume_24h'] else "N/A"
        
        print(f"{timestamp:<20} {price:<12} {source:<15} {volume:<15}")
    
    if len(price_history) > 10:
        print(f"\n... y {len(price_history) - 10} registros más")
    
    # Estadísticas básicas
    prices = [p["price"] for p in price_history]
    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / len(prices)
    
    print(f"\n📊 Estadísticas del período:")
    print(f"   Precio mínimo: ${min_price:.2f}")
    print(f"   Precio máximo: ${max_price:.2f}")
    print(f"   Precio promedio: ${avg_price:.2f}")
    print(f"   Variación: {((max_price - min_price) / min_price * 100):.2f}%")


def show_trade_history(hours=24):
    """Muestra historial de trades"""
    print(f"\n🔄 HISTORIAL DE TRADES (Últimas {hours}h)")
    print("=" * 50)
    
    trade_history = data_manager.get_trade_history(hours=hours)
    
    if not trade_history:
        print("❌ No hay trades disponibles")
        return
    
    print(f"📊 {len(trade_history)} trades encontrados")
    print()
    
    print("-" * 90)
    print(f"{'Timestamp':<20} {'Tipo':<6} {'Cantidad':<12} {'Precio':<12} {'Valor USD':<12} {'Modo':<8}")
    print("-" * 90)
    
    for trade in trade_history:
        from datetime import datetime
        timestamp = datetime.fromtimestamp(trade["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        side = trade["side"]
        amount = f"{trade['amount_sol']:.4f} SOL"
        price = f"${trade['price']:.2f}"
        value = f"${trade['value_usd']:.2f}"
        mode = "SIM" if trade["simulation"] else "REAL"
        
        print(f"{timestamp:<20} {side:<6} {amount:<12} {price:<12} {value:<12} {mode:<8}")
    
    # Estadísticas de trading
    sim_trades = [t for t in trade_history if t["simulation"]]
    real_trades = [t for t in trade_history if not t["simulation"]]
    
    total_volume = sum(t["value_usd"] for t in trade_history)
    
    print(f"\n📊 Estadísticas de trading:")
    print(f"   Total trades: {len(trade_history)}")
    print(f"   Trades simulados: {len(sim_trades)}")
    print(f"   Trades reales: {len(real_trades)}")
    print(f"   Volumen total: ${total_volume:.2f}")


def show_portfolio_history(hours=24):
    """Muestra historial del portfolio"""
    print(f"\n📊 HISTORIAL DEL PORTFOLIO (Últimas {hours}h)")
    print("=" * 50)
    
    portfolio_history = data_manager.get_portfolio_history(hours=hours)
    
    if not portfolio_history:
        print("❌ No hay snapshots del portfolio disponibles")
        return
    
    print(f"📊 {len(portfolio_history)} snapshots encontrados")
    print()
    
    # Mostrar los últimos 10 snapshots
    recent_snapshots = portfolio_history[-10:] if len(portfolio_history) > 10 else portfolio_history
    
    print("-" * 100)
    print(f"{'Timestamp':<20} {'SOL':<12} {'USD':<12} {'Valor Total':<12} {'P&L Real':<12} {'P&L No Real':<12}")
    print("-" * 100)
    
    for snapshot in recent_snapshots:
        from datetime import datetime
        timestamp = datetime.fromtimestamp(snapshot["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        sol_balance = f"{snapshot['sol_balance']:.4f}"
        usd_balance = f"${snapshot['usd_balance']:.2f}"
        total_value = f"${snapshot['total_value_usd']:.2f}"
        realized_pnl = f"${snapshot['realized_pnl']:.2f}"
        unrealized_pnl = f"${snapshot['unrealized_pnl']:.2f}"
        
        print(f"{timestamp:<20} {sol_balance:<12} {usd_balance:<12} {total_value:<12} {realized_pnl:<12} {unrealized_pnl:<12}")
    
    if len(portfolio_history) > 10:
        print(f"\n... y {len(portfolio_history) - 10} snapshots más")
    
    # Estadísticas del portfolio
    first_snapshot = portfolio_history[0]
    last_snapshot = portfolio_history[-1]
    
    initial_value = first_snapshot["total_value_usd"]
    final_value = last_snapshot["total_value_usd"]
    total_return = final_value - initial_value
    total_return_pct = (total_return / initial_value * 100) if initial_value > 0 else 0
    
    print(f"\n📊 Performance del portfolio:")
    print(f"   Valor inicial: ${initial_value:.2f}")
    print(f"   Valor final: ${final_value:.2f}")
    print(f"   Retorno total: ${total_return:.2f} ({total_return_pct:.2f}%)")
    print(f"   P&L realizado: ${last_snapshot['realized_pnl']:.2f}")
    print(f"   P&L no realizado: ${last_snapshot['unrealized_pnl']:.2f}")


def generate_report():
    """Genera reporte completo"""
    print("\n📋 GENERANDO REPORTE COMPLETO")
    print("=" * 50)
    
    hours = input("¿Cuántas horas de historial analizar? (default: 24): ").strip()
    hours = int(hours) if hours.isdigit() else 24
    
    print(f"\n🔄 Generando reporte para las últimas {hours} horas...")
    
    report = generate_trading_report(hours=hours)
    
    # Mostrar resumen del reporte
    print(f"\n📊 RESUMEN DEL REPORTE")
    print("-" * 30)
    print(f"Período analizado: {hours} horas")
    print(f"Datos de precios: {report['raw_data']['price_count']} registros")
    print(f"Trades analizados: {report['raw_data']['trade_count']}")
    print(f"Snapshots de portfolio: {report['raw_data']['portfolio_snapshots']}")
    
    # Mostrar análisis de precios si está disponible
    if "price_analysis" in report and "error" not in report["price_analysis"]:
        price_analysis = report["price_analysis"]
        print(f"\n💰 ANÁLISIS DE PRECIOS:")
        print(f"   Precio actual: ${price_analysis['current_price']:.2f}")
        print(f"   Rango: ${price_analysis['min_price']:.2f} - ${price_analysis['max_price']:.2f}")
        print(f"   Cambio: ${price_analysis['price_change']:.2f} ({price_analysis['price_change_pct']:.2f}%)")
        print(f"   Tendencia: {price_analysis['trend']}")
        print(f"   Volatilidad: {price_analysis['volatility_pct']:.2f}%")
    
    # Mostrar análisis de trading si está disponible
    if "trading_analysis" in report:
        trading_analysis = report["trading_analysis"]
        print(f"\n🔄 ANÁLISIS DE TRADING:")
        print(f"   Total trades: {trading_analysis['total_trades']}")
        print(f"   Trades simulados: {trading_analysis['simulation_trades']}")
        print(f"   Trades reales: {trading_analysis['real_trades']}")
    
    # Preguntar si guardar el reporte
    save = input("\n¿Guardar reporte completo en archivo? (s/N): ").strip().lower()
    if save in ['s', 'si', 'sí', 'y', 'yes']:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"data/exports/reporte_{timestamp}.json"
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📤 Reporte guardado en: {filepath}")


def export_data():
    """Exporta todos los datos"""
    print("\n📤 EXPORTAR DATOS")
    print("=" * 50)
    
    filepath = export_data_for_analysis()
    if filepath:
        print(f"✅ Datos exportados exitosamente a: {filepath}")
    else:
        print("❌ Error exportando datos")


def cleanup_data():
    """Limpia datos antiguos"""
    print("\n🧹 LIMPIAR DATOS ANTIGUOS")
    print("=" * 50)
    
    days = input("¿Eliminar datos más antiguos de cuántos días? (default: 30): ").strip()
    days = int(days) if days.isdigit() else 30
    
    confirm = input(f"\n⚠️  ¿Estás seguro de eliminar datos más antiguos de {days} días? (s/N): ").strip().lower()
    
    if confirm in ['s', 'si', 'sí', 'y', 'yes']:
        print(f"\n🔄 Limpiando datos más antiguos de {days} días...")
        success = data_manager.cleanup_old_data(days=days)
        
        if success:
            print("✅ Limpieza completada exitosamente")
        else:
            print("❌ Error durante la limpieza")
    else:
        print("❌ Limpieza cancelada")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Por favor reporta este error si persiste.")