window.renderAnnualOperatingProfitChart = function () {
    fetch(`/operating_profit_annual_and_margin_data/${STOCK_TICKER}`)
        .then(response => {
            if (!response.ok) throw new Error("Backend returned an error");
            return response.json();
        })
        .then(data => {
            if (!data || !data.periods?.length || !data.operating_profit?.length || !data.operating_margin?.length) {
                console.warn("🚫 Incomplete data received");
                return;
            }

            const labels = data.periods;
            const operatingProfit = data.operating_profit.map(v => v / 1_000_000); // → mn RON
            const operatingMargin = data.operating_margin;      

            const profitMax = Math.max(...operatingProfit);
            const marginMax = Math.max(...operatingMargin);

            const calcScale = (rawMax, steps) => {
                const step = steps.find(s => rawMax <= s * 5) || steps[steps.length - 1];
                const max = Math.ceil(rawMax / step) * step;
                return { max: max, step: Math.ceil(max / 4) };
            };

            const y = calcScale(profitMax, [100, 200, 500]);
            const y1 = calcScale(marginMax, [2, 5, 10, 20]);

            createBarLineChart({
                canvasId: "OperatingProfitAnnualandMargin",
                labels,
                barDataset: {
                    type: "bar",
                    label: "Profit operational",
                    data: operatingProfit,
                    backgroundColor: chartTheme.teal.base,
                    hoverBackgroundColor: chartTheme.teal.hover,
                    borderRadius: 4,
                    yAxisID: "y",
                    order: 2,
                    z: 1
                },
                lineDataset: {
                    type: "line",
                    label: "Marja operationala",
                    data: operatingMargin,
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
