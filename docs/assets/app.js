// CNP Precios - JavaScript Application
class CNPApp {
    constructor() {
        this.productos = [];
        this.productosFiltrados = [];
        this.resumen = {};
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
                searchInput.value = '';
                this.handleSearch('');
                this.toggleClearButton('');
            });
        }

        // Filtros
        const filterTrend = document.getElementById('filter-trend');
        const sortBy = document.getElementById('sort-by');
        
        if (filterTrend) {
            filterTrend.addEventListener('change', () => this.applyFilters());
        }
        
        if (sortBy) {
            sortBy.addEventListener('change', () => this.applyFilters());
        }

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
            this.updateElement('precio-promedio', this.formatPrice(stats.promedio));
        }
    }

    calculateQuickStats() {
        const stats = {
            subida: 0,
            bajada: 0,
            estable: 0,
            promedio: 0
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
        });

        stats.promedio = this.productos.reduce((sum, p) => sum + p.precio_actual, 0) / this.productos.length;

        return stats;
    }

    renderProducts() {
        const container = document.getElementById('products-grid');
        if (!container) return;

        // Actualizar contador
        this.updateElement('results-count', 
            `Mostrando ${this.productosFiltrados.length} de ${this.productos.length} productos`);

        if (this.productosFiltrados.length === 0) {
            this.showNoResults();
            return;
        }

        this.hideNoResults();

        const html = this.productosFiltrados.map(producto => `
            <div class="product-card" onclick="goToProduct('${encodeURIComponent(producto.nombre)}')">
                <div class="product-header">
                    <div class="product-name">${this.escapeHtml(producto.nombre)}</div>
                    <div class="product-price">${this.formatPrice(producto.precio_actual)}</div>
                </div>
                <div class="product-footer">
                    <span class="product-date">${this.formatDate(producto.ultima_fecha)}</span>
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

        // Aplicar filtro de tendencia
        const filterTrend = document.getElementById('filter-trend');
        if (filterTrend && filterTrend.value) {
            filtered = filtered.filter(producto => 
                producto.tendencia_tipo === filterTrend.value
            );
        }

        // Aplicar ordenamiento
        const sortBy = document.getElementById('sort-by');
        if (sortBy) {
            switch (sortBy.value) {
                case 'precio':
                    filtered.sort((a, b) => a.precio_actual - b.precio_actual);
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

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showError(message) {
        console.error(message);
        // Aquí podrías mostrar una notificación de error al usuario
    }
}

// Funciones globales
function goToProduct(productName) {
    window.location.href = `producto.html?producto=${encodeURIComponent(productName)}`;
}

// Página de producto
async function loadProductPage(productName) {
    try {
        // Cargar datos del producto
        const productosResponse = await fetch('data/productos.json');
        const productos = await productosResponse.json();
        
        const producto = productos.find(p => p.nombre === productName);
        
        if (!producto) {
            window.location.href = 'index.html';
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

async function loadProductChart(productName) {
    try {
        // Buscar archivo histórico
        const indexResponse = await fetch('data/historicos_index.json');
        const index = await indexResponse.json();
        
        const productIndex = index.find(item => item.producto === productName);
        
        if (!productIndex) {
            showChartError();
            return;
        }

        // Cargar datos históricos
        const historicoResponse = await fetch(`data/historicos/${productIndex.archivo}`);
        const historico = await historicoResponse.json();
        
        if (historico.length < 2) {
            showChartError();
            return;
        }

        // Crear gráfico
        createPriceChart(historico);
        
    } catch (error) {
        console.error('Error cargando gráfico:', error);
        showChartError();
    }
}

function createPriceChart(data) {
    const ctx = document.getElementById('price-chart');
    if (!ctx) return;

    // Ocultar loading
    const loading = document.getElementById('chart-loading');
    if (loading) loading.style.display = 'none';

    // Preparar datos
    const labels = data.map(item => {
        const date = new Date(item.fecha);
        return date.toLocaleDateString('es-CR', { 
            day: 'numeric', 
            month: 'short' 
        });
    });
    
    const prices = data.map(item => item.precio);

    // Crear gráfico
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Precio (₡)',
                data: prices,
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
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
                            return '₡ ' + context.parsed.y.toLocaleString('es-CR');
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

// Funciones de utilidad
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