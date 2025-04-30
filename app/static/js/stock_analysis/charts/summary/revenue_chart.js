window.renderRevenueChart = function () {
    fetch(`/revenue_data/${STOCK_TICKER}`)
        .then(res => res.json())
        .then(data => {
            if (!data?.values?.length || !data?.periods?.length) {
                return console.warn("🚫 Incomplete data");
            }

            const values = data.values.map(v => v / 1_000_000);
            createBarChart({
                canvasId: "revenueChartCanvas",
                labels: data.periods,
                values,
                label: "Venituri",
                backgroundColor: chartTheme.primary.base,
                hoverColor: chartTheme.primary.hover
            });
        })
        .catch(err => console.error("❌ Revenue chart error:", err));
};
