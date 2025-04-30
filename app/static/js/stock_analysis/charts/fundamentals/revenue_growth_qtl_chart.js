window.renderRevenueGrowthChart = function () {
    fetch(`/revenue_qtl_and_change_data/${STOCK_TICKER}`)
        .then(res => res.json())
        .then(data => {
            const labels = data.periods;
            const revenues = data.revenues.map(v => v / 1_000_000);
            const growthRates = data.change_rate;

            const last = labels.length - 1;
            const yearAgoIndex = labels.findIndex(p =>
                p === labels[last].replace(/(\d{2})$/, m => (parseInt(m) - 1).toString().padStart(2, "0"))
            );

            const barColors = labels.map((_, i) =>
                i === last || i === yearAgoIndex ? chartTheme.teal.active : chartTheme.teal.base
            );
            const hoverColors = barColors.map(c => c);

            const revMax = Math.max(...revenues);
            const grwMax = Math.max(...growthRates);

            const nice = (rawMax, step) => {
                const max = Math.ceil(rawMax / step) * step;
                return { max, step };
            };

            const y = nice(revMax, 100);
            const y1 = nice(grwMax, grwMax < 20 ? 2 : grwMax < 50 ? 5 : 10);

            createBarLineChart({
                canvasId: "revenueQTLandChange",
                labels,
                barDataset: {
                    type: "bar",
                    label: "Venituri",
                    data: revenues,
                    backgroundColor: barColors,
                    hoverBackgroundColor: hoverColors,
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
        .catch(err => console.error("❌ Eroare la încărcarea graficului de venituri:", err));
};
