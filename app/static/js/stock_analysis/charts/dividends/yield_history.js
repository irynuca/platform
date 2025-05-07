window.renderDividendYieldChart = function () {
    fetch(`/dividends/yield_history/${STOCK_TICKER}`)
        .then(res => res.json())
        .then(data => {
            const labels = data.map(d => d.year);
            const values = data.map(d => d.dividend_yield * 100);  // Convert to %

            createLineChart({
                canvasId: "DividendYieldCanvas",
                labels,
                values,
                label: "Randament dividend",
                borderColor: "#20c997", // Bootstrap green
                pointColor: "#20c997"
            });
        })
        .catch(err => console.error("❌ Eroare la încărcarea graficului de randament:", err));
};
