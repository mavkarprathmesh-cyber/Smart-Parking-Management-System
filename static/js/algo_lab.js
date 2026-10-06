/**
 * Algorithm Lab Module
 * Provides benchmarking, live sorting visualizer, and complexity comparisons.
 */

const AlgoLab = {
  currentDataset: [],

  init() {
    this.generateNewDataset(30, 'RANDOM');
  },

  async generateNewDataset(size = 30, type = 'RANDOM') {
    try {
      const res = await API.getLabDataset(size, type);
      this.currentDataset = res.array || [];
      const inputField = document.getElementById('lab-array-input');
      if (inputField) {
        inputField.value = this.currentDataset.join(', ');
      }
      this.renderSortingBars('sorting-canvas', this.currentDataset);
    } catch (err) {
      UI.showToast('Error', 'Failed to generate dataset', 'error');
    }
  },

  getArrayFromInput() {
    const inputField = document.getElementById('lab-array-input');
    if (!inputField || !inputField.value.trim()) return this.currentDataset;
    try {
      const nums = inputField.value.split(',').map(x => parseInt(x.trim(), 10)).filter(x => !isNaN(x));
      if (nums.length === 0) return this.currentDataset;
      this.currentDataset = nums;
      return nums;
    } catch {
      return this.currentDataset;
    }
  },

  async runSortingSuite() {
    const arr = this.getArrayFromInput();
    const tableBody = document.getElementById('sort-results-tbody');
    if (!tableBody) return;

    tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:20px;"><i class="fas fa-spinner fa-spin"></i> Executing sorting algorithms...</td></tr>`;

    try {
      const res = await API.runSortBenchmark(arr);
      const results = res.results || [];
      
      let html = '';
      const algoNames = [];
      const times = [];

      results.forEach(r => {
        if (r.skipped) {
          html += `
            <tr>
              <td><strong>${r.algorithm}</strong></td>
              <td colspan="6" style="color:var(--text-muted);font-style:italic;">${r.reason}</td>
            </tr>
          `;
          return;
        }

        algoNames.push(r.algorithm.replace(' Sort', ''));
        times.push(r.execution_time_ms);

        html += `
          <tr>
            <td><strong>${r.algorithm}</strong></td>
            <td><span class="badge badge-free">${r.execution_time_ms} ms</span></td>
            <td>${r.comparisons.toLocaleString()}</td>
            <td>${r.swaps.toLocaleString()}</td>
            <td><code>${r.time_complexity_best}</code></td>
            <td><code>${r.time_complexity_avg}</code></td>
            <td><code>${r.time_complexity_worst}</code></td>
          </tr>
        `;
      });

      tableBody.innerHTML = html;

      // Draw comparison bar chart
      UI.drawBarChart('sort-chart-canvas', algoNames, times, '#38bdf8');
      UI.showToast('Benchmark Complete', `Successfully compared ${results.length} sorting algorithms on n=${arr.length}.`, 'success');
    } catch (err) {
      tableBody.innerHTML = `<tr><td colspan="7" style="color:#ef4444;text-align:center;">Benchmark failed: ${err.message}</td></tr>`;
      UI.showToast('Error', err.message, 'error');
    }
  },

  async runSearchSuite() {
    const arr = this.getArrayFromInput();
    const targetVal = parseInt(document.getElementById('search-target-input')?.value || '42', 10);
    const container = document.getElementById('search-lab-results');
    if (!container) return;

    try {
      const res = await API.runSearchBenchmark(arr, targetVal);
      const lin = res.linear_search;
      const bin = res.binary_search;

      container.innerHTML = `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
          <div class="card" style="border-left:4px solid #3b82f6;">
            <div class="card-title">Linear Search (Unsorted)</div>
            <div style="margin-top:10px;font-size:13px;display:flex;flex-direction:column;gap:6px;">
              <div>Result: <strong>${lin.found ? `Found at Index ${lin.index}` : 'Not Found'}</strong></div>
              <div>Comparisons: <strong>${lin.comparisons}</strong></div>
              <div>Execution Time: <strong>${lin.execution_time_ms} ms</strong></div>
              <div>Average Complexity: <code>${lin.time_complexity_avg}</code></div>
            </div>
          </div>
          <div class="card" style="border-left:4px solid #10b981;">
            <div class="card-title">Binary Search (Sorted)</div>
            <div style="margin-top:10px;font-size:13px;display:flex;flex-direction:column;gap:6px;">
              <div>Result: <strong>${bin.found ? `Found at Index ${bin.index}` : 'Not Found'}</strong></div>
              <div>Comparisons: <strong>${bin.comparisons}</strong></div>
              <div>Execution Time: <strong>${bin.execution_time_ms} ms</strong></div>
              <div>Average Complexity: <code>${bin.time_complexity_avg}</code></div>
            </div>
          </div>
        </div>
      `;
    } catch (err) {
      UI.showToast('Error', 'Search benchmark failed', 'error');
    }
  },

  renderSortingBars(canvasId, array) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    if (!array || !array.length) return;

    const maxVal = Math.max(...array, 10);
    const barWidth = Math.max(2, (width / array.length) - 2);

    array.forEach((val, i) => {
      const barHeight = (val / maxVal) * (height - 20);
      const x = i * (width / array.length);
      const y = height - barHeight;

      ctx.fillStyle = '#60a5fa';
      ctx.fillRect(x, y, barWidth, barHeight);
    });
  }
};
