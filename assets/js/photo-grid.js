// Split the photos of every .photo-grid into rows that fill the width. Each row's height follows from its photos'
// aspect ratios, so pick the row breaks that keep every row's height closest to a target (a linear partition).
for (const grid of document.querySelectorAll(".photo-grid")) {
  const photos = [...grid.querySelectorAll(":scope > a")];
  const ratios = photos.map((photo) => parseFloat(photo.style.getPropertyValue("--ratio")));
  let laidOutWidth = 0;
  const layOut = () => {
    const width = grid.clientWidth;
    // The grid only changes height after a layout; a hidden grid has no width to fill.
    if (width === laidOutWidth || width === 0) return;
    laidOutWidth = width;
    const gap = parseFloat(getComputedStyle(grid).columnGap);
    const target = Math.min(Math.max(width / 3, 150), 240);
    // cost[j] is the lowest cost of laying out the first j photos; rowStart[j] is where its last row starts.
    const cost = [0];
    const rowStart = [0];
    for (let j = 1; j <= photos.length; j++) {
      cost[j] = Infinity;
      let ratioSum = 0;
      for (let i = j - 1; i >= 0; i--) {
        ratioSum += ratios[i];
        const height = (width - gap * (j - i - 1)) / ratioSum;
        const rowCost = cost[i] + Math.log(height / target) ** 2;
        if (rowCost < cost[j]) [cost[j], rowStart[j]] = [rowCost, i];
      }
    }
    const rows = [];
    for (let j = photos.length; j > 0; j = rowStart[j]) {
      const row = document.createElement("div");
      row.className = "photo-row";
      row.append(...photos.slice(rowStart[j], j));
      rows.unshift(row);
    }
    grid.replaceChildren(...rows);
  };
  layOut();
  new ResizeObserver(layOut).observe(grid);
}
