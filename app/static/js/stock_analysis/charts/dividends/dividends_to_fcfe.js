window.renderDividendtoFCFEChart = function () {
    fetch(`/dividends/dividends_to_fcfe/${STOCK_TICKER}`)
        .then(res => res.json())
        .then(data => {
            const labels = data.map(d => d.year);
            const values = data.map(d => d.dividends_to_fcfe * 100);  // Convert to %

            createLineChart({
                canvasId: "DividendFCFECanvas",
                labels,
                values,
                label: "Dividende / FCFE",
                borderColor: "#20c997", // Bootstrap green
                pointColor: "#20c997"
            });
        })
        .catch(err => console.error("❌ Eroare la încărcarea graficului Dividende/FCFE:", err));
};
