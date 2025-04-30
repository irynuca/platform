window.renderNetProfitChart = function () {
    fetch(`/net_profit_qtl_and_margin_data/${STOCK_TICKER}`)
        .then(res => res.json())
        .then(data => {
            const labels = data.periods;
            const netProfit = data.net_profit.map(v => v / 1_000_000);
            const netMargin = data.net_margin;

            const last = labels.length - 1;
            const yearAgoIndex = labels.findIndex(p =>
                p === labels[last].replace(/(\d{2})$/, m => (parseInt(m) - 1).toString().padStart(2, "0"))
            );

            const barColors = labels.map((_, i) =>
                i === last || i === yearAgoIndex ? chartTheme.pink.active : chartTheme.pink.base
            );
            const hoverColors = labels.map((_, i) =>
                i === last || i === yearAgoIndex ? chartTheme.pink.hover : chartTheme.pink.hover
            );

            const maxProfit = Math.max(...netProfit);
            const maxMargin = Math.max(...netMargin);

            const nice = (max, step) => {
                const rounded = Math.ceil(max / step) * step;
                return { max: rounded, step };
            };

            const y = nice(maxProfit, 100);
            const y1 = nice(maxMargin, maxMargin < 20 ? 2 : maxMargin < 50 ? 5 : 10);

            createBarLineChart({
                canvasId: "NetProfitandMarginCanvas",
                labels,
                barDataset: {
                    type: "bar",
                    label: "Profit net",
                    data: netProfit,
                    backgroundColor: barColors,
                    hoverBackgroundColor: hoverColors,
                    borderRadius: 4,
                    yAxisID: "y",
                    order: 2,
                    z: 1
                },
                lineDataset: {
                    type: "line",
                    label: "Marjă netă",
                    data: netMargin,
                    borderColor: "#A9DDD6",
                    backgroundColor: "#A9DDD6",
                    tension: 0.3,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    yAxisID: "y1",
                    order: 1,
                    z: 2
                },
                yAxisOptions: {
                    max: y.max,
                    ticks: {
                        stepSize: y.step,
                        callback: v => `${v.toFixed(0)} mn`
                    }
                },
                y1AxisOptions: {
                    max: y1.max,
                    ticks: {
                        stepSize: y1.step,
                        callback: v => `${v.toFixed(1)}%`
                    }
                }
            });
        })
        .catch(err => console.error("❌ Eroare la încărcarea graficului de profit net:", err));
};
