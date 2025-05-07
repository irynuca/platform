window.renderDPSChart = function () {
    fetch(`/dividends/dps_and_growth/${STOCK_TICKER}`)
        .then(res => res.json())
        .then(data => {
            const labels = data.map(d => d.year);
            const dpsValues = data.map(d => d.DPS_value);
            const yoyChange = data.map(d => d.dividends_yoy_change * 100);

            const last = labels.length - 1;
            const yearAgoIndex = labels.findIndex(p =>
                p === labels[last].toString().replace(/(\d{2})$/, m => (parseInt(m) - 1).toString().padStart(2, "0"))
            );

            const barColors = labels.map((_, i) =>
                i === last || i === yearAgoIndex ? chartTheme.primary.active : chartTheme.primary.base
            );
            const hoverColors = labels.map((_, i) =>
                i === last || i === yearAgoIndex ? chartTheme.primary.hover : chartTheme.primary.hover
            );

            const maxDPS = Math.max(...dpsValues);
            const maxChange = Math.max(...yoyChange.map(v => Math.abs(v)));

            const nice = (max, step) => {
                const rounded = Math.ceil(max / step) * step;
                return { max: rounded, step };
            };

            const y = nice(maxDPS, maxDPS < 0.1 ? 0.01 : 0.05);
            const y1 = nice(maxChange, maxChange < 20 ? 5 : maxChange < 50 ? 10 : 20);

            // ✅ Create the chart with line animation
            createBarLineChart({
                canvasId: "dividendsDPSChart",
                labels,
                barDataset: {
                    type: "bar",
                    label: "Dividend / acțiune",
                    data: dpsValues,
                    backgroundColor: barColors,
                    hoverBackgroundColor: hoverColors,
                    borderRadius: 4,
                    yAxisID: "y",
                    order: 2,
                    z: 1
                },
                lineDataset: {
                    type: "line",
                    label: "Variație an/an",
                    data: yoyChange,
                    borderColor: "#ffc107",
                    backgroundColor: "#ffc107",
                    tension: 0.3,
                    fill: false,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    borderWidth: 2,
                    yAxisID: "y1",
                    order: 1,
                    z: 2
                },
                yAxisOptions: {
                    max: y.max,
                    ticks: {
                        stepSize: y.step,
                        callback: v => `${v.toFixed(2)} RON`
                    }
                },
                y1AxisOptions: {
                    max: y1.max,
                    ticks: {
                        stepSize: y1.step,
                        callback: v => `${v.toFixed(1)}%`
                    }
                },
                tooltipFormatter: ctx => {
                    const label = ctx.dataset.label || "";
                    return `${label}: ${ctx.raw.toFixed(2)}${ctx.dataset.yAxisID === "y1" ? "%" : " RON"}`;
                },
                animationOptions: {
                    duration: 2000,
                    easing: 'easeOutQuart'
                }
            });
        })
        .catch(err => console.error("❌ Eroare la încărcarea graficului DPS:", err));
};
