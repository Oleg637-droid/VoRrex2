(function() {
    // Демонстрационный набор данных (замените на динамическую подгрузку из бэкенда при необходимости)
    const ALL_PRODUCTS_FULL = [
        { 
            id: "1", 
            title: "Рукав высокого давления (РВД) 4SH", 
            description: "Четырехслойный стальной каркас для экстремальных гидравлических нагрузок спецтехники.", 
            price: 5200, 
            stock: 32, 
            image: "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=500",
            category: "Рукава" 
        },
        { 
            id: "2", 
            title: "Фитинг DKOL прямой М20x1.5", 
            description: "Высокопрочный стальной фитинг с метрической резьбой под обжимку.", 
            price: 1400, 
            stock: 180, 
            image: "https://images.unsplash.com/photo-1581092335397-9583fe92d232?w=500",
            category: "Фитинги" 
        },
        { 
            id: "3", 
            title: "Адаптер переходной BSP / NPT", 
            description: "Универсальный резьбовой соединитель для гидравлических магистралей.", 
            price: 2500, 
            stock: 45, 
            image: "", 
            category: "Адаптеры" 
        }
    ];

    let cart = {};
    let currentCategory = 'all';

    function initCategories() {
        const categoriesSet = new Set();
        ALL_PRODUCTS_FULL.forEach(p => categoriesSet.add(p.category));
        
        const tabsContainer = document.getElementById('categoriesTabs');
        if (!tabsContainer) return;
        
        tabsContainer.innerHTML = '<button type="button" class="cat-chip active" data-category="all">Все позиции</button>';
        
        categoriesSet.forEach(cat => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'cat-chip';
            btn.setAttribute('data-category', cat);
            btn.textContent = cat;
            tabsContainer.appendChild(btn);
        });
    }

    function renderCatalogGrid(filterText = '') {
        const grid = document.getElementById('mainProductsGrid');
        if (!grid) return;
        grid.innerHTML = '';

        const query = filterText.toLowerCase().trim();
        const filtered = ALL_PRODUCTS_FULL.filter(p => {
            const matchesCategory = (currentCategory === 'all' || p.category === currentCategory);
            const matchesQuery = p.title.toLowerCase().includes(query) || p.description.toLowerCase().includes(query);
            return matchesCategory && matchesQuery;
        });

        if (filtered.length === 0) {
            grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #9ca3af;">Позиции не найдены</div>';
            return;
        }

        filtered.forEach(p => {
            const card = document.createElement('div');
            card.className = 'product-card';
            
            const hasImage = p.image && p.image !== 'None' && p.image !== '';
            const imgSrc = hasImage ? p.image : 'https://placehold.co/300x200/111827/9ca3af?text=No+Photo';

            card.innerHTML = `
                <div>
                    <div class="product-img-wrap">
                        <img src="${imgSrc}" alt="${p.title}" onerror="this.onerror=null; this.src='https://placehold.co/300x200/111827/ef4444?text=Error';">
                    </div>
                    <div class="product-title">${p.title}</div>
                    <div class="product-desc">${p.description}</div>
                </div>
                <div>
                    <div class="product-info-row">
                        <span class="product-price">${p.price.toLocaleString()} тг</span>
                        <span class="product-stock">Остаток: ${p.stock}</span>
                    </div>
                    <div class="product-actions">
                        <button type="button" class="btn-detail" data-id="${p.id}">Обзор</button>
                        <button type="button" class="btn-add" data-id="${p.id}">+</button>
                    </div>
                </div>
            `;

            card.addEventListener('click', (e) => {
                if (!e.target.closest('button')) openDetailModal(p.id);
            });

            grid.appendChild(card);
        });
    }

    function openDetailModal(productId) {
        const product = ALL_PRODUCTS_FULL.find(p => p.id === productId);
        if (!product) return;

        const modalContent = document.getElementById('modalDetailContent');
        const hasImage = product.image && product.image !== 'None' && product.image !== '';
        const imgSrc = hasImage ? product.image : 'https://placehold.co/400x300/111827/9ca3af?text=No+Photo';
        const currentQtyInCart = cart[product.id] ? cart[product.id].quantity : 1;

        modalContent.innerHTML = `
            <div style="display: flex; gap: 24px; flex-wrap: wrap; align-items: center;">
                <img src="${imgSrc}" alt="${product.title}" style="width: 240px; height: 200px; object-fit: cover; border-radius: 10px; background: #161e2e;" onerror="this.onerror=null; this.src='https://placehold.co/240x200/111827/ef4444?text=Error';">
                <div style="flex: 1; min-width: 240px;">
                    <span style="background: rgba(59,130,246,0.1); color: #3b82f6; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">${product.category}</span>
                    <h2 style="margin: 12px 0 8px 0; font-size: 1.25rem; color: white;">${product.title}</h2>
                    <p style="color: #9ca3af; font-size: 0.85rem; line-height: 1.5; margin-bottom: 15px;">${product.description}</p>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #34d399; margin-bottom: 6px;">${product.price.toLocaleString()} тг</div>
                    <div style="font-size: 0.8rem; color: #9ca3af; margin-bottom: 20px;">На складе: <strong style="color: white;">${product.stock} шт.</strong></div>
                </div>
            </div>
            <div style="border-top: 1px solid var(--border-color); margin-top: 24px; padding-top: 20px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 0.9rem; font-weight: 500;">Количество:</span>
                    <input type="number" id="modalProductQty" value="${currentQtyInCart}" min="1" max="${product.stock > 0 ? product.stock : 9999}" class="qty-input" style="width: 70px; padding: 8px;">
                </div>
                <button type="button" id="modalAddToCartBtn" data-id="${product.id}" class="btn-checkout" style="width: auto; padding: 10px 24px;">Добавить в корзину</button>
            </div>
        `;

        document.getElementById('productDetailModal').style.display = 'flex';
    }

    function updateCartItem(productId, quantity) {
        const product = ALL_PRODUCTS_FULL.find(p => p.id === productId);
        if (!product) return;

        quantity = parseInt(quantity) || 1;
        if (quantity <= 0) {
            delete cart[productId];
        } else {
            cart[productId] = {
                id: product.id,
                title: product.title,
                price: product.price,
                quantity: quantity
            };
        }
        renderCart();
    }

    function renderCart() {
        const container = document.getElementById('cartItemsContainer');
        const badge = document.getElementById('cartBadge');
        const totalPriceEl = document.getElementById('cartTotalPrice');
        const submitBtn = document.getElementById('submitOrderBtn');

        if (!container || !badge || !totalPriceEl || !submitBtn) return;
        
        let totalCount = 0;
        let totalPrice = 0;
        const keys = Object.keys(cart);

        container.innerHTML = '';

        if (keys.length === 0) {
            container.innerHTML = `
                <div class="empty-cart">
                    <div class="empty-ico">📦</div>
                    <p>Корзина пуста<br><span>Выберите комплектующие из каталога слева</span></p>
                </div>
            `;
            badge.textContent = '0';
            totalPriceEl.textContent = '0 тг';
            submitBtn.disabled = true;
            return;
        }

        keys.forEach(id => {
            const item = cart[id];
            totalCount += item.quantity;
            totalPrice += item.price * item.quantity;

            const row = document.createElement('div');
            row.className = 'cart-item-card';
            row.innerHTML = `
                <div style="overflow: hidden;">
                    <div class="cart-item-title" title="${item.title}">${item.title}</div>
                    <div class="cart-item-sub">${item.price.toLocaleString()} тг × ${item.quantity}</div>
                </div>
                <div class="cart-item-controls">
                    <input type="number" value="${item.quantity}" min="1" class="qty-input cart-item-qty-input" data-id="${item.id}">
                    <button type="button" class="btn-remove" data-id="${item.id}" title="Удалить">✕</button>
                </div>
                <input type="hidden" name="product_id[]" value="${item.id}">
                <input type="hidden" name="quantity[]" value="${item.quantity}">
            `;
            container.appendChild(row);
        });

        badge.textContent = totalCount;
        totalPriceEl.textContent = totalPrice.toLocaleString() + ' тг';
        submitBtn.disabled = false;
    }

    // События
    document.addEventListener('DOMContentLoaded', () => {
        initCategories();
        renderCatalogGrid();
        renderCart();
    });

    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-add')) {
            const id = e.target.getAttribute('data-id');
            const currentQty = cart[id] ? cart[id].quantity + 1 : 1;
            updateCartItem(id, currentQty);
        }
        if (e.target.classList.contains('btn-detail')) {
            openDetailModal(e.target.getAttribute('data-id'));
        }
        if (e.target.classList.contains('btn-remove')) {
            delete cart[e.target.getAttribute('data-id')];
            renderCart();
        }
        if (e.target.classList.contains('cat-chip')) {
            document.querySelectorAll('.cat-chip').forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
            currentCategory = e.target.getAttribute('data-category');
            const searchInput = document.getElementById('catalogSearchInput');
            renderCatalogGrid(searchInput ? searchInput.value : '');
        }
        if (e.target.id === 'modalAddToCartBtn') {
            const id = e.target.getAttribute('data-id');
            const qtyInput = document.getElementById('modalProductQty');
            updateCartItem(id, qtyInput ? qtyInput.value : 1);
            document.getElementById('productDetailModal').style.display = 'none';
        }
    });

    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('cart-item-qty-input')) {
            updateCartItem(e.target.getAttribute('data-id'), e.target.value);
        }
    });

    const closeBtn = document.getElementById('closeDetailModalBtn');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            document.getElementById('productDetailModal').style.display = 'none';
        });
    }

    const modalOverlay = document.getElementById('productDetailModal');
    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) e.currentTarget.style.display = 'none';
        });
    }

    const searchInput = document.getElementById('catalogSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            renderCatalogGrid(this.value);
        });
    }
})();
