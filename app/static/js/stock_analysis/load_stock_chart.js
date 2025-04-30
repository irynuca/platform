// --- Load Stock Price Chart (Lightweight Charts) ---

window.loadStockChart = function(period = '1y') {
    const ticker = STOCK_TICKER; // Use a global variable instead of Jinja

    fetch(`/historical_data/${ticker}/${period}`)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById("lightweight-stock-chart");

            if (!data || data.error) {
                container.innerHTML = "<p>Date indisponibile.</p>";
                return;
            }

            // Clear chart before redrawing
            container.innerHTML = "";

            const chart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: 300,
                layout: {
                    background: { color: 'transparent' },
                    textColor: '#ffffff',
                },
                grid: {
                    vertLines: { visible: false },
                    horzLines: { color: 'rgba(255,255,255,0.1)' },
                },
                timeScale: {
                    timeVisible: true,
                    borderColor: '#ffffff33',
                },
                rightPriceScale: {
                    borderColor: '#ffffff33',
                },
            });

            const areaSeries = chart.addAreaSeries({
                topColor: 'rgba(79, 209, 197, 0.5)',
                bottomColor: 'rgba(79, 209, 197, 0)',
                lineColor: '#4FD1C5',
                lineWidth: 2,
            });

            const chartData = data.dates.map((date, i) => ({
                time: date.split('T')[0],
                value: parseFloat(data.prices[i]),
            }));

            areaSeries.setData(chartData);
            chart.timeScale().fitContent();

            window.addEventListener('resize', () => {
                chart.resize(container.clientWidth, 300);
            });
        })
        .catch(err => console.error("❌ Error loading stock chart:", err));
}

