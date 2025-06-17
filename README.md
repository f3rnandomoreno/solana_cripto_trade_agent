
# 🛠️ Bot AI Trading Solana (Python)

> Proyecto abierto para crear un **agente de trading automático y “mínimo viable”** que:
>
> 1. Obtiene precios en tiempo real (Jupiter + Pyth).  
> 2. Genera señales mediante indicadores técnicos + IA ligera.  
> 3. Ejecuta swaps en la red Solana con comisiones ínfimas.  
> 4. Registra todas las operaciones, P/L y métricas en consola.  
> 5. Escala con estrategias más complejas (ML supervisado o RL).  

---

## 0. Tabla de contenido
1. [Requisitos mínimos](#1-requisitos-mínimos)  
2. [Estructura del proyecto](#2-estructura-del-proyecto)  
3. [Instalación rápida](#3-instalación-rápida)  
4. [Configuración `.env`](#4-configuración-env)  
5. [Arquitectura y módulos](#5-arquitectura-y-módulos)  
6. [Flujo de ejecución](#6-flujo-de-ejecución)  
7. [Estrategia por defecto](#7-estrategia-por-defecto)  
8. [Back-testing y simulación](#8-back-testing-y-simulación)  
9. [Seguridad & buenas prácticas](#9-seguridad--buenas-prácticas)  
10. [Road-map](#10-road-map)  
11. [Licencia](#11-licencia)  

---

## 1. Requisitos mínimos

| Software | Versión recomendada | Notas |
|----------|--------------------|-------|
| Python   | ≥ 3.10             | Necesario para `solders` y async modernos. |
| `pip` / `virtualenv` | Última | Gestión de entornos. |
| **Wallet Phantom** | — | Crea un wallet exclusivo para el bot. Carga 0,3–0,5 SOL. |
| Nodo RPC fiable | QuickNode / Helius / Triton | Menos *rate-limit* que los públicos |
| Claves API opcionales | CryptoCompare, CoinGecko | Para histórico de precios. |

---

## 2. Estructura del proyecto

```text
solana-ai-bot/
├─ README.md               ← esta guía
├─ requirements.txt        ← librerías Python
├─ .env.example            ← plantilla de variables
└─ src/
   ├─ bot.py               ← loop principal
   ├─ main.py              ← CLI (`trade` y `backtest`)
   ├─ config.py
   ├─ data/
   │  ├─ pyth_feed.py
   │  ├─ jupiter_quote.py
   │  └─ mock_feed.py      ← feed simulado
   ├─ strategy/
   │  ├─ indicators.py
   │  ├─ model.py          ← ML ligero (opcional)
   │  └─ risk.py
   ├─ execution/
   │  ├─ jupiter_client.py
   │  └─ portfolio.py
   ├─ utils/
   │  ├─ logger.py
   │  └─ backtest.py
   └─ tests/
```

---

## 3. Instalación rápida

```bash
git clone https://github.com/tu-usuario/solana-ai-bot.git
cd solana-ai-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # añade tus claves
python src/main.py trade --steps 10 --mock   # demo con feed simulado
```

**`requirements.txt` mínimo**

```
solana>=0.31
solders>=0.20
anchorpy>=0.18
jupiter-python-sdk>=0.4
ta
pandas
numpy
aiohttp
websockets
python-dotenv
rich
```

---

## 4. Configuración `.env`

```dotenv
# Clave privada del wallet (array base58 o semilla en hex)
PRIVATE_KEY="[...]"
# RPC endpoint – usa tu proveedor o mainnet-beta público
RPC_ENDPOINT="https://mainnet.helius-rpc.com/?api-key=TU_API"
# API de precios históricos (opcional)
CRYPTOCOMPARE_KEY="..."
# Parámetros de trading
BASE_MINT="So11111111111111111111111111111111111111112"   # SOL
QUOTE_MINT="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" # USDC
TRADING_INTERVAL_SEC=60
SLIPPAGE_BPS=50
MAX_DRAWDOWN_PCT=20
```

---

## 5. Arquitectura y módulos

### 5.1 Data Feed
| Fuente | Uso | Implementación |
|--------|-----|----------------|
| **Jupiter API** | Cotizaciones instantáneas + rutas de swap | `src/data/jupiter_quote.py` |
| **Pyth Network** | Precio fiable on-chain (SOL/USD) | WebSocket vía `pyth-client-py` |
| **Mock Feed** | Generación local de precios | `src/data/mock_feed.py` |
| **Aggregated Feed** | Promedio Jupiter + Pyth (fallback) | `src/data/aggregated_feed.py` |

### 5.2 Strategy
- **Indicadores técnicos (EMA 12/50, RSI 14, Bollinger 20/2)**
- Implementación en `strategy/indicators.py` y señales básicas en
  `strategy/simple_strategy.py`.
- Filtro de volumen (evita operar con liquidez baja)
- Validación IA: modelo ligero (random-forest) que aprende qué señales históricas fueron rentables

### 5.3 Execution
- Implementación en `execution/jupiter_client.py` para solicitar cotizaciones a Jupiter (stub si no hay red).
- `execution/portfolio.py` mantiene el saldo de SOL/USDC y calcula P/L.
- La versión completa usaría Jupiter Python SDK para construir la transacción, firmarla con `solana.Keypair` y enviarla mediante `client.send_raw_transaction`.

### 5.4 Logger / Console UI
- `utils/logger.py` configura el logging con `rich` y guarda cada trade en `logs/trades.csv`.
- `utils/backtest.py` permite pruebas rápidas de la estrategia con datos históricos simulados.

### 5.5 Trading loop
- `bot.TradingBot` integra feed, estrategia y cartera en un loop asíncrono.
- Cada trade consulta un `quote` a Jupiter para estimar la ejecución.

---

## 6. Flujo de ejecución

```mermaid
flowchart TD
  Ticker[Price feed (Jupiter/Pyth)] --> Strat
  Strat[Strategy + IA] -->|BUY/SELL| Exec
  Exec[Execute swap] --> RPC[(Solana RPC)]
  Exec --> Log[Console / CSV]
  Log --> PnL[Dashboard P/L]
```

1. **Loop** cada `TRADING_INTERVAL_SEC`  
2. Calcula indicadores y predicción IA  
3. Si señal válida → solicita swap en Jupiter  
4. Firma y envía transacción  
5. Espera confirmación y actualiza P/L  

---

## 7. Estrategia por defecto

| Regla | Condición | Acción |
|-------|-----------|--------|
| **Tendencia alcista** | EMA12 > EMA50 ∧ RSI < 70 | Mantener SOL |
| **Reversión bajista** | Precio toca banda superior BB ∧ RSI > 70 | Vender SOL → USDC |
| **Sobreventa** | RSI < 30 ∧ precio < banda inferior BB | Comprar SOL |
| **Stop-loss** | Pérdida ≥ `MAX_DRAWDOWN_PCT` | Salir a USDC |

> Ajusta los parámetros en `strategy/config.yaml`.

---

## 8. Back-testing y simulación

```bash
python src/main.py backtest datos.csv
```

`datos.csv` debe contener una columna con precios históricos de SOL.
El comando muestra el retorno total y el número de operaciones simuladas.

---

## 9. Seguridad & buenas prácticas
* **Wallet dedicado** y sin otros fondos  
* Clave en `.env`, nunca en el repo  
* Validar mint y cantidades antes de firmar  
* Probar primero en `devnet`  
* Límite de peticiones a Jupiter para evitar 429  
* Auditar dependencias (instalar `solana`, no `solana-py`)  

---

## 10. Road-map
- [ ] Websocket live-UI con `rich.Live`  
- [ ] Telegram/Discord bot para alertas  
- [ ] Modelo ML supervisado + *auto-retrain* semanal  
- [ ] Aprendizaje por refuerzo con TensorTrade  
- [ ] Estrategias multi-token y arbitraje triangular  

---

## 11. Licencia
Este proyecto se publica bajo **GPL-3.0**.  
Úsalo bajo tu propio riesgo. Nada de esto constituye asesoría financiera.

---

¡Forkea este repo, ajusta la estrategia a tu estilo y comienza a probar en devnet!

## 12. Development Log
El progreso del desarrollo se documenta en [docs/devlog.md](docs/devlog.md).
