window.renderAnnualNetProfitChart = function () {
    fetch(`/net_profit_annual_and_margin_data/${STOCK_TICKER}`)
        .then(response => {
            if (!response.ok) throw new Error("Backend returned an error");
            return response.json();
        })
        .then(data => {
            if (!data || !data.periods?.length || !data.net_profit?.length || !data.net_margin?.length) {
                console.warn("🚫 Incomplete data received");
                return;
            }

            const labels = data.periods;
            const netProfit = data.net_profit.map(v => v / 1_000_000); // → mn RON
            const netMargin = data.net_margin;      

            const profitMax = Math.max(...netProfit);
            const marginMax = Math.max(...netMargin);

            const calcScale = (rawMax, steps) => {
                const step = steps.find(s => rawMax <= s * 5) || steps[steps.length - 1];
                const max = Math.ceil(rawMax / step) * step;
                return { max: max, step: Math.ceil(max / 4) };
            };

            const y = calcScale(profitMax, [100, 200, 500]);
            const y1 = calcScale(marginMax, [2, 5, 10, 20]);

            createBarLineChart({
                canvasId: "NetProfitAnnualandMargin",
                labels,
                barDataset: {
                    type: "bar",
                    label: "Profit net atribuibil",
                    data: netProfit,
                    backgroundColor: chartTheme.info.base,
                    hoverBackgroundColor: chartTheme.info.hover,
                    borderRadius: 4,
                    yAxisID: "y",
                    order: 2,
                    z: 1
                },
                lineDataset: {
                    type: "line",
                    label: "Marja neta",
                    data: netMargin,
                    borderColor: chartTheme.secondary.base,
                    backgroundColor: chartTheme.secondary.base,
                    fill: false,
                    tension: 0.3,
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
                        callback: v => `${v.toFixed(0)}%`
                    }
                }
            });
        })
        .catch(err => {
            console.error("❌ Eroare la încărcarea graficului de profit operational:", err);
        });
};
