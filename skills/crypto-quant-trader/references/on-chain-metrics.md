# On-Chain Metrics Reference

## Core Concepts

On-chain metrics analyze data recorded on the blockchain to understand network health, investor behavior, and market sentiment. These metrics provide fundamental insights that complement technical analysis.

## Key Metrics Categories

### Exchange Flows

**Exchange Inflows**
- Coins moving TO exchanges
- Indicates potential selling pressure
- Spike in inflows = bearish signal
- Data sources: CryptoQuant, Glassnode

**Exchange Outflows**
- Coins moving FROM exchanges
- Indicates accumulation/hodling
- Spike in outflows = bullish signal
- Self-custody trend = strong bullish

**Exchange Reserve**
- Total coins held on exchanges
- Decreasing trend = scarcity, bullish
- Increasing trend = potential sell wall, bearish

**Interpretation:**
```
Net Flow = Outflows - Inflows
Positive Net Flow = Accumulation
Negative Net Flow = Distribution
```

### Address Metrics

**Active Addresses**
- Unique addresses with transactions
- Network activity indicator
- Rising + rising price = sustainable trend
- Falling + rising price = weak trend

**New Addresses**
- Addresses appearing for first time
- Adoption metric
- Spike in new addresses = fresh interest

**Whale Activity**
- Addresses holding 100+ BTC
- Whale accumulation = bullish
- Whale distribution = bearish
- Track whale movements for early signals

**HODL Waves**
- Age distribution of coins
- Long-term holder (LTH) coins > 155 days
- LTH increasing = strong hands, bullish
- LTH decreasing = weak hands, bearish

### Supply Metrics

**Circulating Supply**
- Total coins available in market
- Changes due to burns, unlocks, staking
- Decreasing supply (burn) = deflationary, bullish

**Liquid Supply**
- Coins actively traded (last 90 days)
- High liquid supply = volatility

**Staked Supply**
- Coins locked in staking
- Higher staked supply = less selling pressure
- Unstaking events = potential sell pressure

**Realized Cap**
- Sum of all coins at their last moved price
- Better than market cap for valuing dormant coins
- Realized cap increasing = value flowing in

**MVRV Ratio**
```
MVRV = Market Cap / Realized Cap
```
- MVRV > 3.7: Overvalued, distribution phase
- MVRV < 1: Undervalued, accumulation phase
- MVRV = 1: Fair value

**NUPL (Network Unrealized Profit/Loss)**
```
NUPL = (Market Cap - Realized Cap) / Market Cap
```
- NUPL > 0.75: Euphoria, bubble territory
- 0.5 < NUPL < 0.75: Belief, bull market
- 0 < NUPL < 0.5: Hope/optimism, early bull
- NUPL < 0: Capitulation, bear market bottom

### Network Activity

**Transaction Count**
- Total transactions on network
- Usage metric
- Increasing = growing adoption
- Decreasing = declining interest

**Transaction Volume**
- Total value transferred
- Economic activity metric
- Volume spike with price rise = sustainable

**Average Transaction Value**
- Total volume / transaction count
- High value = institutional activity
- Low value = retail activity

**Fees**
- Network fees paid
- High fees = high demand, congestion
- Fee spikes often precede price moves

**Hash Rate (PoW)**
- Total mining power
- Mining profitability indicator
- Rising = secure, long-term bullish
- Falling = miners capitulating

### Profit/Loss Metrics

**SOPR (Spent Output Profit Ratio)**
```
SOPR = Value of spent outputs / Value when created
```
- SOPR > 1: Profit-taking, selling
- SOPR < 1: Loss-taking, capitulation
- SOPR = 1: Break-even
- SOPR crossing 1 from below = capitulation over

**aSOPR (Adjusted SOPR)**
- SOPR adjusted for noise (coin days destroyed)
- More accurate signal

**Liveliness**
- Cumulative days coins are not destroyed
- Decreasing = older coins moving (selling)
- Increasing = accumulation

## Key Data Sources

### Free
- **Blockchain.com**: Basic metrics
- **CoinMetrics**: Some free metrics
- **Glassnode**: Limited free tier
- **CryptoQuant**: Limited free tier

### Paid
- **Glassnode**: Comprehensive, expensive
- **CryptoQuant**: Exchange-focused data
- **Santiment**: Social + on-chain
- **IntoTheBlock**: ML-driven insights
- **Nansen**: NFT + DeFi focus

## Metric Combinations

### Bull Market Signal Stack
1. Exchange outflows increasing
2. Whale accumulation
3. LTH supply rising
4. MVRV 1-2 (not overvalued)
5. NUPL 0.5-0.75 (belief phase)

### Bear Market Signal Stack
1. Exchange inflows spiking
2. Whale distribution
3. LTH supply falling
4. MVRV < 1 (undervalued)
5. NUPL < 0 (capitulation)

### Top Signal (Market Peak)
1. Exchange reserve rising
2. LTH selling (HODL waves shift)
3. MVRV > 3.7 (extreme overvalued)
4. NUPL > 0.75 (euphoria)
5. Retail FOMO (new address spikes + high volume)

### Bottom Signal (Market Low)
1. Exchange outflows (whale accumulation)
2. Long-term holders not selling
3. MVRV < 1 (undervalued)
4. NUPL < 0 (capitulation)
5. Low volume + apathy

## Token-Specific Metrics

### Ethereum (ETH)
- **Gas Used**: Network utilization
- **ETH Burn (EIP-1559)**: Deflationary pressure
- **DeFi TVL**: Economic activity
- **Staked ETH ( validators)**: Beacon chain health

### DeFi Tokens
- **TVL in protocol**: Protocol adoption
- **Unique users**: Growth metric
- **Revenue generation**: Value capture
- **Treasury value**: Protocol resilience

### Stablecoins
- **Circulating supply**: Demand indicator
- **Peg stability**: Trust metric
- **Redemptions**: De-risking signal
- **Exchange ratio**: Market sentiment (USDT/USDC)

## Timeframe Considerations

**Short-term (Days-Weeks)**
- Exchange flows
- Whale movements
- SOPR spikes

**Medium-term (Weeks-Months)**
- Address trends
- HODL waves
- MVRV trends

**Long-term (Months-Quarters)**
- Realized cap
- Network growth
- Adoption metrics

## Limitations

- **Exchange labeling**: Some exchanges not identified
- **Privacy coins**: Harder to track
- **Custodial wallets**: May not reflect true holder behavior
- **Wormhole bridges**: Cross-chain complexity
- **Lagging indicators**: Some metrics react after price moves

## Quick Reference Table

| Metric | Bullish | Bearish | Use Case |
|--------|---------|---------|----------|
| Exchange Outflows | ↑ | ↓ | Accumulation signal |
| Exchange Inflows | ↓ | ↑ | Distribution signal |
| Active Addresses | ↑ | ↓ | Adoption trend |
| Whale Holdings | ↑ | ↓ | Smart money positioning |
| MVRV | 1-2 | >3.7 | Valuation |
| NUPL | 0.5-0.75 | >0.75 or <0 | Market cycle |
| SOPR | Crosses 1↑ | Crosses 1↓ | Profit-taking |

---

Remember: On-chain metrics are powerful but should be combined with technical analysis and market context for best results.
