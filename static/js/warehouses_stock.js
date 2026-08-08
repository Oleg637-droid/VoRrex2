(function() {
    let stockData = [];
    let currentWarehouse = 'all';

    async function fetchStockData() {
        try {
            const response = await fetch('/api/warehouses-stock');
            stockData = await response.json();
            renderTable();
        } catch (error) {
            console.error('Ошибка загрузки данных из БД:', error);
        }
    }

    function renderTable(filterText = '') {
        const tbody = document.getElementById('stockTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';

        const query = filterText.toLowerCase().trim();
        const filtered = stockData.filter(item => {
            const matchesQuery = item.title.toLowerCase().includes(query) || (item.code && item.code.toLowerCase().includes(query));
            return matchesQuery;
        });

        if (filtered.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 30px;">Позиции не найдены в базе данных</td></tr>';
            return;
        }

        filtered.forEach(item => {
            const tr = document.createElement('tr');
            
            // Фильтрация отображения колонок складов при выборе конкретного склада в табах
            const showWh1 = (currentWarehouse === 'all' || currentWarehouse === '1');
            const showWh2 = (currentWarehouse === 'all' || currentWarehouse === '2');
            const showWh3 = (currentWarehouse === 'all' || currentWarehouse === '3');

            tr.innerHTML = `
                <td>
                    <div class="item-name-cell">
                        <strong>${item.title}</strong>
                        <span>Код: ${item.code || 'N/A'}</span>
                    </div>
                </td>
                <td>${item.category || 'Комплектующие'}</td>
                <td><span class="stock-badge ${item.wh1 <= 2 ? 'low' : ''}">${item.wh1} шт</span></td>
                <td><span class="stock-badge ${item.wh2 <= 2 ? 'low' : ''}">${item.wh2} шт</span></td>
                <td><span class="stock-badge ${item.wh3 <= 2 ? 'low' : ''}">${item.wh3} шт</span></td>
                <td><strong>${item.total} шт</strong></td>
                <td>
                    <button type="button" class="btn-action-sm" data-id="${item.id}">Переместить</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        fetchStockData();

        // Поиск
        const searchInput = document.getElementById('stockSearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                renderTable(e.target.value);
            });
        }

        // Переключение табов складов
        const tabsContainer = document.getElementById('warehouseTabs');
        if (tabsContainer) {
            tabsContainer.addEventListener('click', (e) => {
                const btn = e.target.closest('.wh-tab');
                if (!btn) return;
                
                document.querySelectorAll('.wh-tab').forEach(t => t.classList.remove('active'));
                btn.classList.add('active');
                currentWarehouse = btn.getAttribute('data-warehouse');
                
                renderTable(searchInput ? searchInput.value : '');
            });
        }
    });
})();
