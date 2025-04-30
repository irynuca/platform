window.renderProfitabilityChart = function () {
    fetch(`/profit_and_margin_data/${STOCK_TICKER}`)
        .then(response => {
            if (!response.ok) throw new Error("Backend error");
            return response.json();
        })
        .then(data => {
            if (!data?.periods?.length || !data.profit?.length || !data.margin?.length) {
                return console.warn("🚫 Incomplete chart data");
            }

            const labels = data.periods;
            const profits = data.profit.map(v => v / 1_000_000);
            const margins = data.margin;

            const maxProfit = Math.max(...profits);
            const maxMargin = Math.max(...margins);

            // Utility: scale logic
            const autoScale = (rawMax, stepCandidates = [1, 2, 5, 10, 20]) => {
                const roundTo = stepCandidates.find(s => rawMax <= s * 5) || 10;
                const niceMax = Math.ceil(rawMax / roundTo) * roundTo;
                const step = Math.ceil(niceMax / 4);
                return { max: step * 4, step };
            };

            const { max: yMax, step: yStep } = autoScale(maxProfit, [50, 100, 200]);
            const { max: y1Max, step: y1Step } = autoScale(maxMargin, [5, 10, 20]);

            createBarLineChart({
                canvasId: "profitabilityChartCanvas",
                labels,
                barDataset: {
                    label: "Profit net",
                    data: profits,
                    backgroundColor: chartTheme.secondary.base,
                    hoverBackgroundColor: chartTheme.secondary.hover,
                    borderRadius: 4
                },
                lineDataset: {
                    type: 'line',
                    label: "Marjă netă",
                    data: margins,
                    borderColor: "#A9DDD6",
                    backgroundColor: "#A9DDD6",
                    tension: 0.3,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                yScale: {
                    max: yMax,
                    ticks: {
                        stepSize: yStep,
                        callback: v => `${v.toFixed(0)} mn`
                    }
                },
                y1Scale: {
                    max: y1Max,
                    ticks: {
                        stepSize: y1Step,
                        callback: v => `${v.toFixed(1)}%`
                    }
                }
            });
        })
        .catch(err => console.error("❌ Profitability chart load failed:", err));
};
