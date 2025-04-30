window.renderOperatingProfitChart = function () {
    fetch(`/operating_profit_qtl_and_margin_data/${STOCK_TICKER}`)
        .then(res => res.json())
        .then(data => {
            const { periods, operating_profit, operating_margin } = data;

            const barData = operating_profit.map(v => v / 1_000_000);
            const lineData = operating_margin;

            const last = periods.length - 1;
            const yearAgoIndex = periods.findIndex(p =>
                p === periods[last].replace(/(\d{2})$/, m => (parseInt(m) - 1).toString().padStart(2, "0"))
            );

            const barColors = periods.map((_, i) =>
                i === last || i === yearAgoIndex ? chartTheme.secondary.active : chartTheme.secondary.base
            );
            const barHoverColors = periods.map((_, i) =>
                i === last || i === yearAgoIndex ? chartTheme.secondary.hover : chartTheme.secondary.hover
            );

            const maxProfit = Math.max(...barData);
            const maxMargin = Math.max(...lineData);

            const niceAxis = (max, step) => {
                const rounded = Math.ceil(max / step) * step;
                return { max: rounded, step };
            };

            const y = niceAxis(maxProfit, 100);
            const y1 = niceAxis(maxMargin, maxMargin < 20 ? 2 : maxMargin < 50 ? 5 : 10);

            createBarLineChart({
                canvasId: "OperatingProfitandMarginCanvas",
                labels: periods,
                barDataset: {
                    type: "bar",
                    label: "Profit operațional",
                    data: barData,
                    backgroundColor: barColors,
                    hoverBackgroundColor: barHoverColors,
                    borderRadius: 4,
                    yAxisID: "y",
                    order: 2,
                    z: 1
                },
                lineDataset: {
                    type: "line",
                    label: "Marjă operațională",
                    data: lineData,
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
        .catch(err => console.error("❌ Error loading operating profit chart:", err));
};
