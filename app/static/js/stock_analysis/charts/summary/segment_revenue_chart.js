window.renderSegmentRevenueChart = function () {
    fetch(`/segment_revenue_data/${STOCK_TICKER}`)
        .then(response => {
            if (!response.ok) throw new Error("Bad response");
            return response.json();
        })
        .then(data => {
            if (!data?.data?.length) {
                document.getElementById("segmentRevenueChart").innerHTML =
                    "<p class='text-white'>📊 Nicio structură de venit disponibilă.</p>";
                return;
            }

            const segments = data.data;
            const period = data.period || "Perioadă necunoscută";
            const labels = segments.map(item => item.label);
            const values = segments.map(item => item.value);

            const backgroundColors = [
                chartTheme.orange.base,
                chartTheme.teal.base,
                chartTheme.cyan.base,
                chartTheme.pink.base,
                chartTheme.primary.base
            ];

            createDonutChart({
                canvasId: "segmentRevenueChartCanvas",
                labels,
                values,
                backgroundColors,
                centerLabel: period
            });
        })
        .catch(err => {
            console.error("❌ Eroare la încărcarea veniturilor pe segmente:", err);
            document.getElementById("segmentRevenueChart").innerHTML =
                "<p class='text-white'>Eroare la încărcarea datelor.</p>";
        });
};
