// Initialize Chart
const chartContainer = document.getElementById('chart-container');
const chart = LightweightCharts.createChart(chartContainer, {
    layout: {
        background: { type: 'solid', color: 'transparent' },
        textColor: '#a0a0a0',
    },
    grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
    },
    rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
    },
    timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
        timeVisible: true,
    },
    crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal,
    },
});

const candleSeries = chart.addCandlestickSeries({
    upColor: '#00ff9d',
    downColor: '#ff4d4d',
    borderVisible: false,
    wickUpColor: '#00ff9d',
    wickDownColor: '#ff4d4d',
});

// Resize Observer
new ResizeObserver(entries => {
    if (entries.length === 0 || entries[0].target !== chartContainer) { return; }
    const newRect = entries[0].contentRect;
    chart.applyOptions({ height: newRect.height, width: newRect.width });
}).observe(chartContainer);

// Data Fetching
async function fetchHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        updateHistoryUI(data);
    } catch (error) {
        console.error('Error fetching history:', error);
    }
}

async function fetchMarketData() {
    try {
        const response = await fetch('/api/market_data');
        const data = await response.json();
        if (data.data && data.data.length > 0) {
            // Sort data by time just in case
            const sortedData = data.data.sort((a, b) => a.time - b.time).map(item => ({
                time: item.time / 1000, // Lightweight charts expects seconds
                open: item.open,
                high: item.high,
                low: item.low,
                close: item.close
            }));
            candleSeries.setData(sortedData);
            document.getElementById('chart-title').innerText = data.symbol;
        }
    } catch (error) {
        console.error('Error fetching market data:', error);
    }
}

async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        updateStatusUI(data);
    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

// UI Updates
function updateHistoryUI(data) {
    const container = document.getElementById('history-content');
    container.innerHTML = '';

    // Combine trades and logs if needed, for now just showing trades
    data.trades.forEach(trade => {
        const item = document.createElement('div');
        item.className = `history-item ${trade.side}`; // 'buy' or 'sell'

        const date = new Date(trade.time).toLocaleTimeString();

        item.innerHTML = `
            <div class="history-header">
                <span>${trade.symbol}</span>
                <span>${date}</span>
            </div>
            <div class="history-details">
                ${trade.side.toUpperCase()} ${trade.size} @ ${trade.price}
            </div>
            <div style="font-size: 0.8em; color: #888; margin-top: 4px;">
                Status: ${trade.status}
            </div>
        `;
        container.appendChild(item);
    });

    // You could also append recent logs/cycles below
}

function updateStatusUI(data) {
    if (data.balance) {
        document.getElementById('balance-total').innerText = formatCurrency(data.balance.total.USDT);
        document.getElementById('balance-free').innerText = formatCurrency(data.balance.free.USDT);
    }
    if (data.status) {
        document.getElementById('status-text').innerText = data.status;
    }
}

function formatCurrency(value) {
    if (value === undefined || value === null) return '--';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
}

// Initial Load & Polling
fetchMarketData(); // Fetch once initially heavy data
fetchHistory();
fetchStatus();

setInterval(fetchHistory, 5000);
setInterval(fetchStatus, 2000);
setInterval(fetchMarketData, 60000); // Update chart every minute
