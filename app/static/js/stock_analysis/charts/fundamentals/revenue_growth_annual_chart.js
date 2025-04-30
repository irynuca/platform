window.renderAnnualRevenueGrowthChart = function () {
    fetch(`/revenue_annual_and_change_data/${STOCK_TICKER}`)
        .then(response => {
            if (!response.ok) throw new Error("Backend returned an error");
            return response.json();
        })
        .then(data => {
            if (!data || !data.periods?.length || !data.revenues?.length || !data.change_rate?.length) {
                console.warn("🚫 Incomplete data received");
                return;
            }

            const labels = data.periods;
            const revenues = data.revenues.map(v => v / 1_000_000); // → mn RON
            const growthRates = data.change_rate;

            const lastIndex = labels.length - 1;
            const yearAgoIndex = labels.findIndex(p =>
                p === labels[lastIndex].replace(/(\d{2})$/, match =>
                    (parseInt(match) - 1).toString().padStart(2, "0"))
            );

            const barColors = labels.map((_, i) =>
                i === lastIndex || i === yearAgoIndex ? chartTheme.teal.active : chartTheme.teal.base
            );

            const barHoverColors = labels.map((_, i) =>
                i === lastIndex || i === yearAgoIndex ? chartTheme.teal.hover : chartTheme.teal.hover
            );

            const revMax = Math.max(...revenues);
            const growthMax = Math.max(...growthRates);

            const calcScale = (rawMax, steps) => {
                const step = steps.find(s => rawMax <= s * 5) || steps[steps.length - 1];
                const max = Math.ceil(rawMax / step) * step;
                return { max: max, step: Math.ceil(max / 4) };
            };

            const y = calcScale(revMax, [100, 200, 500]);
            const y1 = calcScale(growthMax, [2, 5, 10, 20]);

            createBarLineChart({
                canvasId: "revenueAnnualandChange",
                labels,
                barDataset: {
                    type: "bar",
                    label: "Venituri (mnRON)",
                    data: revenues,
                    backgroundColor: barColors,
                    hoverBackgroundColor: barHoverColors,
                    borderRadius: 4,
                    yAxisID: "y",
                    order: 2,
                    z: 1
                },
                lineDataset: {
                    type: "line",
                    label: "Creștere venit y/y",
                    data: growthRates,
                    borderColor: chartTheme.orange.base,
                    backgroundColor: chartTheme.orange.base,
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
            console.error("❌ Eroare la încărcarea graficului de venituri:", err);
        });
};
