window.renderOperatingProfitChart = function () {
  fetch(`/operating_profit_qtl_and_margin_data/${STOCK_TICKER}`)
    .then(res => {
      if (!res.ok) throw new Error("Backend error");
      return res.json();
    })
    .then(data => {
      const { periods, operating_profit, operating_margin } = data;
      const barData  = operating_profit.map(v => v / 1_000_000);
      const lineData = operating_margin;

      // find “last” and “year-ago” for highlighting…
      const last = periods.length - 1;
      const yearAgo = periods[last]
        .replace(/(\d{2})$/, m => (parseInt(m) - 1).toString().padStart(2, "0"));
      const yearAgoIndex = periods.indexOf(yearAgo);

      const barColors = periods.map((_, i) =>
        (i === last || i === yearAgoIndex)
          ? chartTheme.secondary.active
          : chartTheme.secondary.base
      );
      const barHoverColors = periods.map((_, i) =>
        chartTheme.secondary.hover
      );
  
      // finally, call the chart helper
      createBarLineChart({
        canvasId: "OperatingProfitandMarginCanvas",
        labels:   periods,
        barDataset: {
          label: "Profit operațional",
          data: barData,
          backgroundColor:    barColors,
          hoverBackgroundColor: barHoverColors,
          borderRadius: 4,
          order: 1           // ← draw bars first
        },
        lineDataset: {
          label: "Marjă operațională",
          data:  lineData,
          borderColor:         "#A9DDD6",
          tension:             0.3,
          fill:                false,
          pointRadius:         4,
          pointHoverRadius:    6,
          order: 2            // ← draw lines on top
        },
        barUnit:  "mn",
        lineUnit: "%"
      });
    })
    .catch(err => console.error("❌ Error loading operating profit chart:", err));
};
