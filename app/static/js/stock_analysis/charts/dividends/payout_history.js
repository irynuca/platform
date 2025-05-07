window.renderDividendPayoutChart = function () {
    fetch(`/dividends/payout_ratio/${STOCK_TICKER}`)
        .then(res => res.json())
        .then(data => {
            const labels = data.map(d => d.year);
            const values = data.map(d => d.payout_ratio * 100);  // Convert to %

            createLineChart({
                canvasId: "DividendPayoutCanvas",
                labels,
                values,
                label: "Rata distribuire dividende",
                borderColor: "#20c997", // Bootstrap green
                pointColor: "#20c997"
            });
        })
        .catch(err => console.error("❌ Eroare la încărcarea graficului ratei de distribuire:", err));
};
