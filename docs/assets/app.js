// CNP Precios - JavaScript Application
class CNPApp {
    constructor() {
        this.productos = [];
        this.productosFiltrados = [];
        this.resumen = {};
        this.activeCardFilter = '';
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadData();
        this.renderHomePage();
    }

    setupEventListeners() {
        // Búsqueda
        const searchInput = document.getElementById('search-input');
        const clearSearch = document.getElementById('clear-search');
        
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
                this.toggleClearButton(e.target.value);
            });
        }
        
        if (clearSearch) {
            clearSearch.addEventListener('click', () => {
                if (searchInput) searchInput.value = '';
                this.handleSearch('');
                this.toggleClearButton('');
            });
        }

        // Filtros
        const filterTrend = document.getElementById('filter-trend');
        const sortBy = document.getElementById('sort-by');
        
        if (filterTrend) {
            filterTrend.addEventListener('change', () => {
                this.activeCardFilter = filterTrend.value;
                this.applyFilters();
            });
        }
        
        if (sortBy) {
            sortBy.addEventListener('change', () => this.applyFilters());
        }

        // Tarjetas interactivas de estadísticas (Filtros rápidos)
        const setupCardClick = (cardId, filterValue) => {
            const card = document.getElementById(cardId);
            if (card && filterTrend) {
                card.addEventListener('click', () => {
                    if (filterTrend.value === filterValue) {
                        filterTrend.value = ''; // Desactivar filtro
                    } else {
                        filterTrend.value = filterValue;
                    }
                    this.applyFilters();
                });
            }
        };

        setupCardClick('card-subida', 'subida');
        setupCardClick('card-bajada', 'bajada');
        setupCardClick('card-estable', 'estable');
        setupCardClick('card-oferta', 'oferta');

        // Botón producto aleatorio
        const randomBtn = document.getElementById('random-product');
        if (randomBtn) {
            randomBtn.addEventListener('click', () => this.goToRandomProduct());
        }
    }

    toggleClearButton(value) {
        const clearButton = document.getElementById('clear-search');
        if (clearButton) {
            clearButton.style.display = value ? 'block' : 'none';
        }
    }

    async loadData() {
        try {
            // Cargar resumen
            const resumenResponse = await fetch('data/resumen.json');
            this.resumen = await resumenResponse.json();

            // Cargar productos
            const productosResponse = await fetch('data/productos.json');
            this.productos = await productosResponse.json();
            this.productosFiltrados = [...this.productos];

            console.log('Datos cargados:', {
                productos: this.productos.length,
                resumen: this.resumen
            });

        } catch (error) {
            console.error('Error cargando datos:', error);
            this.showError('Error cargando datos. Intenta recargar la página.');
        }
    }

    renderHomePage() {
        this.updateStats();
        this.renderProducts();
    }

    updateStats() {
        // Estadísticas del header
        this.updateElement('total-productos', this.resumen.total_productos || 0);
        this.updateElement('ultima-actualizacion', this.formatDate(this.resumen.ultima_actualizacion));

        // Estadísticas rápidas
        if (this.productos.length > 0) {
            const stats = this.calculateQuickStats();
            this.updateElement('productos-subida', stats.subida);
            this.updateElement('productos-bajada', stats.bajada);
            this.updateElement('productos-estable', stats.estable);
            this.updateElement('productos-oferta', stats.oferta);
        }
    }

    calculateQuickStats() {
        const stats = {
            subida: 0,
            bajada: 0,
            estable: 0,
            oferta: 0
        };

        this.productos.forEach(producto => {
            switch (producto.tendencia_tipo) {
                case 'subida':
                    stats.subida++;
                    break;
                case 'bajada':
                    stats.bajada++;
                    break;
                default:
                    stats.estable++;
            }
            if (producto.estado_temporada === 'temporada_baja') {
                stats.oferta++;
            }
        });

        return stats;
    }

    getSeasonBadge(estado) {
        if (estado === 'temporada_baja') {
            return `<span class="badge badge-success"><i class="fas fa-seedling"></i> Oferta de Cosecha</span>`;
        } else if (estado === 'temporada_alta') {
            return `<span class="badge badge-danger"><i class="fas fa-exclamation-triangle"></i> Escasez / Pico</span>`;
        }
        return `<span class="badge badge-normal"><i class="fas fa-check-circle"></i> Temporada Normal</span>`;
    }

    renderProducts() {
        const container = document.getElementById('products-grid');
        if (!container) return;

        const filterTrend = document.getElementById('filter-trend');
        const selectedFilterText = filterTrend && filterTrend.selectedIndex > 0 ? 
            ` (${filterTrend.options[filterTrend.selectedIndex].text})` : '';

        // Actualizar contador
        this.updateElement('results-count', 
            `Mostrando ${this.productosFiltrados.length} de ${this.productos.length} productos${selectedFilterText}`);

        // Resaltar tarjeta de filtro activa
        ['card-subida', 'card-bajada', 'card-estable', 'card-oferta'].forEach(id => {
            const card = document.getElementById(id);
            if (card) card.classList.remove('active-filter-card');
        });

        if (filterTrend && filterTrend.value) {
            const activeCardMap = {
                'subida': 'card-subida',
                'bajada': 'card-bajada',
                'estable': 'card-estable',
                'oferta': 'card-oferta'
            };
            const activeId = activeCardMap[filterTrend.value];
            if (activeId) {
                const activeCard = document.getElementById(activeId);
                if (activeCard) activeCard.classList.add('active-filter-card');
            }
        }

        if (this.productosFiltrados.length === 0) {
            this.showNoResults();
            return;
        }

        this.hideNoResults();

        const html = this.productosFiltrados.map(producto => `
            <div class="product-card" onclick="goToProduct('${encodeURIComponent(producto.nombre)}')">
                <div class="product-card-header">
                    <div class="product-name">${this.escapeHtml(producto.nombre)}</div>
                    <div class="product-price">${this.formatPrice(producto.precio_actual)}</div>
                </div>
                <div class="product-badges">
                    ${this.getSeasonBadge(producto.estado_temporada)}
                </div>
                <div class="product-info-details">
                    <div class="info-row">
                        <span><i class="fas fa-arrows-alt-v"></i> Histórico:</span>
                        <strong>${this.formatPrice(producto.precio_minimo)} - ${this.formatPrice(producto.precio_maximo)}</strong>
                    </div>
                    ${producto.meses_baratos && producto.meses_baratos.length ? `
                    <div class="info-row">
                        <span><i class="fas fa-calendar-alt"></i> Meses Baratos:</span>
                        <strong class="text-success">${producto.meses_baratos.join(', ')}</strong>
                    </div>` : ''}
                </div>
                <div class="product-footer">
                    <span class="product-date"><i class="far fa-clock"></i> ${this.formatDate(producto.ultima_fecha)}</span>
                    <span class="product-trend trend-${producto.tendencia_tipo}">
                        ${this.formatTrend(producto.tendencia_porcentaje)}
                    </span>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    handleSearch(term) {
        const searchTerm = term.toLowerCase().trim();
        this.applyFilters(searchTerm);
    }

    applyFilters(searchTerm = null) {
        let filtered = [...this.productos];

        // Aplicar búsqueda
        if (searchTerm === null) {
            const searchInput = document.getElementById('search-input');
            searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
        }

        if (searchTerm) {
            filtered = filtered.filter(producto => 
                producto.nombre.toLowerCase().includes(searchTerm)
            );
        }

        // Aplicar filtro de tendencia/temporada
        const filterTrend = document.getElementById('filter-trend');
        if (filterTrend && filterTrend.value) {
            const val = filterTrend.value;
            if (val === 'subida' || val === 'bajada' || val === 'estable') {
                filtered = filtered.filter(p => p.tendencia_tipo === val);
            } else if (val === 'oferta') {
                filtered = filtered.filter(p => p.estado_temporada === 'temporada_baja');
            } else if (val === 'escasez') {
                filtered = filtered.filter(p => p.estado_temporada === 'temporada_alta');
            }
        }

        // Aplicar ordenamiento
        const sortBy = document.getElementById('sort-by');
        if (sortBy) {
            switch (sortBy.value) {
                case 'precio_asc':
                    filtered.sort((a, b) => a.precio_actual - b.precio_actual);
                    break;
                case 'precio_desc':
                    filtered.sort((a, b) => b.precio_actual - a.precio_actual);
                    break;
                case 'tendencia':
                    filtered.sort((a, b) => b.tendencia_porcentaje - a.tendencia_porcentaje);
                    break;
                default: // nombre
                    filtered.sort((a, b) => a.nombre.localeCompare(b.nombre));
            }
        }

        this.productosFiltrados = filtered;
        this.renderProducts();
    }

    showNoResults() {
        const container = document.getElementById('products-grid');
        const noResults = document.getElementById('no-results');
        
        if (container) container.style.display = 'none';
        if (noResults) noResults.style.display = 'block';
    }

    hideNoResults() {
        const container = document.getElementById('products-grid');
        const noResults = document.getElementById('no-results');
        
        if (container) container.style.display = 'grid';
        if (noResults) noResults.style.display = 'none';
    }

    goToRandomProduct() {
        if (this.productos.length > 0) {
            const randomIndex = Math.floor(Math.random() * this.productos.length);
            const randomProduct = this.productos[randomIndex];
            goToProduct(randomProduct.nombre);
        }
    }

    updateElement(id, text) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = text;
        }
    }

    escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;')
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;')
                  .replace(/"/g, '&quot;')
                  .replace(/'/g, '&#039;');
    }

    formatPrice(price) {
        if (typeof price !== 'number') return '₡ -';
        return `₡ ${price.toLocaleString('es-CR', { 
            minimumFractionDigits: 0,
            maximumFractionDigits: 0 
        })}`;
    }

    formatDate(dateString) {
        if (!dateString) return '-';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('es-CR', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
            });
        } catch {
            return '-';
        }
    }

    formatTrend(percentage) {
        if (typeof percentage !== 'number') return '';
        
        const sign = percentage > 0 ? '+' : '';
        return `${sign}${percentage.toFixed(1)}%`;
    }
}

// Navegación a la página de producto
function goToProduct(productName) {
    window.location.href = `producto.html?producto=${productName}`;
}

async function loadProductPage(productName) {
    try {
        // Cargar productos para info básica
        const productosResponse = await fetch('data/productos.json');
        const productos = await productosResponse.json();
        
        const producto = productos.find(p => p.nombre === productName);
        
        if (!producto) {
            document.getElementById('product-name').textContent = 'Producto no encontrado';
            return;
        }

        // Actualizar información básica
        updateProductInfo(producto);
        
        // Cargar y mostrar gráfico
        await loadProductChart(productName);
        
    } catch (error) {
        console.error('Error cargando página de producto:', error);
        document.getElementById('product-name').textContent = 'Error cargando producto';
    }
}

function updateProductInfo(producto) {
    // Actualizar elementos del DOM
    document.getElementById('product-name').textContent = producto.nombre;
    document.getElementById('product-breadcrumb').textContent = producto.nombre;
    document.getElementById('current-price').textContent = formatPrice(producto.precio_actual);
    document.getElementById('trend-value').textContent = formatTrend(producto.tendencia_porcentaje);
    document.getElementById('price-range').textContent = 
        `${formatPrice(producto.precio_minimo)} / ${formatPrice(producto.precio_maximo)}`;
    document.getElementById('avg-price').textContent = formatPrice(producto.precio_promedio);
    document.getElementById('last-update').textContent = 
        `Última actualización: ${formatDate(producto.ultima_fecha)}`;
    
    // Estadísticas detalladas
    document.getElementById('total-records').textContent = producto.total_registros;
    document.getElementById('min-price-ever').textContent = formatPrice(producto.precio_minimo);
    document.getElementById('max-price-ever').textContent = formatPrice(producto.precio_maximo);
    document.getElementById('avg-price-historical').textContent = formatPrice(producto.precio_promedio);
    
    // Actualizar icono de tendencia
    const trendIcon = document.getElementById('trend-icon');
    if (trendIcon) {
        trendIcon.className = 'fas fa-chart-line';
        if (producto.tendencia_tipo === 'subida') {
            trendIcon.className = 'fas fa-chart-line text-danger';
        } else if (producto.tendencia_tipo === 'bajada') {
            trendIcon.className = 'fas fa-chart-line-down text-success';
        }
    }
}

let currentChartInstance = null;
let fullHistoricalData = [];

async function loadProductChart(productName) {
    try {
        // Buscar archivo histórico
        const indexResponse = await fetch('data/historicos_index.json');
        const index = await indexResponse.json();
        
        let archivoPath = null;
        if (Array.isArray(index)) {
            const item = index.find(i => i.producto === productName || i.nombre === productName);
            if (item) archivoPath = item.archivo;
        } else if (index && typeof index === 'object') {
            archivoPath = index[productName];
        }
        
        if (!archivoPath) {
            // Intentar slug por defecto
            const slug = productName.trim().replace(/\s+/g, '_');
            archivoPath = `data/historicos/${slug}.json`;
        }

        if (!archivoPath.startsWith('data/')) {
            archivoPath = `data/historicos/${archivoPath}`;
        }

        // Cargar datos históricos
        const historicoResponse = await fetch(archivoPath);
        if (!historicoResponse.ok) {
            showChartError();
            return;
        }
        fullHistoricalData = await historicoResponse.json();
        
        if (!fullHistoricalData || fullHistoricalData.length < 2) {
            showChartError();
            return;
        }

        // Configurar listener para el dropdown de período
        const periodSelect = document.getElementById('chart-period');
        if (periodSelect) {
            periodSelect.onchange = function() {
                updateChartPeriod(this.value);
            };
            // Cargar con el período por defecto seleccionado
            updateChartPeriod(periodSelect.value || '90');
        } else {
            createPriceChart(fullHistoricalData);
        }
        
    } catch (error) {
        console.error('Error cargando gráfico:', error);
        showChartError();
    }
}

function updateChartPeriod(periodValue) {
    if (!fullHistoricalData || fullHistoricalData.length === 0) return;

    let filtered = [...fullHistoricalData];
    if (periodValue !== 'all') {
        const days = parseInt(periodValue, 10);
        if (!isNaN(days) && days > 0) {
            const lastDate = new Date(fullHistoricalData[fullHistoricalData.length - 1].fecha);
            const cutoffTime = lastDate.getTime() - (days * 24 * 60 * 60 * 1000);
            filtered = fullHistoricalData.filter(item => new Date(item.fecha).getTime() >= cutoffTime);
        }
    }

    if (filtered.length === 0) {
        filtered = fullHistoricalData; // Fallback
    }

    createPriceChart(filtered);
}

function createPriceChart(data) {
    const ctx = document.getElementById('price-chart');
    if (!ctx) return;

    // Destruir instancia anterior si existe
    if (currentChartInstance) {
        currentChartInstance.destroy();
        currentChartInstance = null;
    }

    // Ocultar loading y error
    const loading = document.getElementById('chart-loading');
    const error = document.getElementById('chart-error');
    if (loading) loading.style.display = 'none';
    if (error) error.style.display = 'none';

    // Formatear etiquetas asegurando que el año sea visible (ej: '23 oct 2025')
    const labels = data.map(item => {
        const date = new Date(item.fecha);
        return date.toLocaleDateString('es-CR', { 
            day: 'numeric', 
            month: 'short',
            year: 'numeric'
        });
    });
    
    const prices = data.map(item => item.precio);

    // Crear gráfico nuevo
    currentChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Precio (₡)',
                data: prices,
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.15)',
                borderWidth: 2,
                pointRadius: data.length > 60 ? 1 : 3,
                pointHoverRadius: 5,
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return '₡ ' + value.toLocaleString('es-CR');
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Precio: ₡ ' + context.parsed.y.toLocaleString('es-CR');
                        }
                    }
                }
            }
        }
    });
}

function showChartError() {
    const loading = document.getElementById('chart-loading');
    const error = document.getElementById('chart-error');
    
    if (loading) loading.style.display = 'none';
    if (error) error.style.display = 'flex';
}

function formatPrice(price) {
    if (typeof price !== 'number') return '₡ -';
    return `₡ ${price.toLocaleString('es-CR', { 
        minimumFractionDigits: 0,
        maximumFractionDigits: 0 
    })}`;
}

function formatDate(dateString) {
    if (!dateString) return '-';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-CR', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });
    } catch {
        return '-';
    }
}

function formatTrend(percentage) {
    if (typeof percentage !== 'number') return '';
    
    const sign = percentage > 0 ? '+' : '';
    return `${sign}${percentage.toFixed(1)}%`;
}

// Inicializar aplicación cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    // Solo inicializar en la página principal
    if (document.getElementById('products-grid') && !document.getElementById('price-chart')) {
        new CNPApp();
    }
});