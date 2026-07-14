import { createContext, useContext, useState, ReactNode } from 'react';

type Language = 'es' | 'en';

interface Translations {
  [key: string]: {
    [key: string]: string;
  };
}

const translations: Translations = {
  es: {
    // Header & Sidebar
    dashboard: 'Dashboard',
    search: 'Buscar',
    favorites: 'Favoritos',
    alerts: 'Alertas',
    aiAssistant: 'Asistente IA',
    searchPlaceholder: 'Buscar productos...',
    usaDefault: 'USA (por defecto)',
    newYork: 'New York, NY',
    losAngeles: 'Los Ángeles, CA',
    chicago: 'Chicago, IL',
    houston: 'Houston, TX',
    miami: 'Miami, FL',
    priceCompare: 'PriceCompare',
    
    // Dashboard
    dashboardTitle: 'Dashboard',
    dashboardSubtitle: 'Visión general del sistema de comparación de precios e Inteligencia Artificial',
    system: 'Sistema',
    active: 'Activo',
    connectedBackend: 'Conectado al backend local',
    statsFavorites: 'Favoritos',
    statsFavoritesDesc: 'Productos guardados en tu lista',
    statsTotalAlerts: 'Alertas Totales',
    statsTotalAlertsDesc: 'Monitoreando variaciones de precio',
    statsActiveAlerts: 'Alertas Activas',
    statsActiveAlertsDesc: 'Notificaciones de Telegram habilitadas',
    opportunitiesTitle: 'Oportunidades del Día (Mejores Descuentos)',
    opportunitiesSubtitle: 'Análisis de Promedio Histórico',
    noOpportunities: 'No se encontraron ofertas significativas todavía.',
    noOpportunitiesHint: 'Buscá y abrí productos nuevos para recopilar historial y detectar oportunidades.',
    savingPercent: '% de ahorro',
    viewOffer: 'Ver oferta',
    startSearchingTitle: 'Comenzá a buscar',
    startSearchingDesc1: 'Usá la barra de búsqueda en la parte superior para encontrar y comparar precios de productos en múltiples tiendas.',
    startSearchingDesc2: 'Al abrir el detalle de cualquier producto, la IA analizará el historial y te dará consejos de conveniencia instantáneos.',
    readyToUse: 'Listo para usar',

    // Search Results
    searchResultsTitle: 'Resultados de búsqueda',
    searchQueryLabel: 'Búsqueda',
    searchResultsCount: 'resultado',
    searchResultsCount_plural: 'resultados',
    noResultsWithQuery: 'No se encontraron productos con los criterios especificados.',
    noResultsWithoutQuery: 'Realiza una búsqueda para ver resultados.',

    // Favorites
    favoritesTitle: 'Favoritos',
    favoritesSubtitle: 'Gestiona tus productos favoritos',
    noFavoritesTitle: 'No tienes favoritos',
    noFavoritesDesc: 'Agrega productos a favoritos para guardarlos aquí',

    // Alerts
    alertsTitle: 'Alertas de precio',
    alertsSubtitle: 'Configura alertas para recibir notificaciones cuando los precios cambien',
    newAlert: 'Nueva alerta',
    createAlertTitle: 'Crear alerta de precio',
    productFieldLabel: 'Producto (Nombre)',
    productPlaceholder: 'Ej: iPhone 15 Pro',
    conditionFieldLabel: 'Condición',
    conditionBelow: 'Por debajo de',
    conditionAbove: 'Por encima de',
    conditionEquals: 'Igual a',
    targetPriceLabel: 'Precio objetivo',
    createAlertBtn: 'Crear alerta',
    cancelBtn: 'Cancelar',
    noAlertsTitle: 'No tienes alertas configuradas',
    noAlertsDesc: 'Crea alertas para recibir notificaciones cuando los precios cambien',
    createFirstAlertBtn: 'Crear primera alerta',
    productColumn: 'Producto',
    conditionColumn: 'Condición',
    statusColumn: 'Estado',
    actionsColumn: 'Acciones',
    conditionMetBadge: 'Condición Cumplida',
    activeBadge: 'Activa',
    pausedBadge: 'Pausada',
    testNotificationTitle: 'Probar notificación',
    pauseTitle: 'Pausar',
    activateTitle: 'Activar',
    deleteTitle: 'Eliminar',
    deleteConfirm: '¿Estás seguro de eliminar esta alerta?',
    telegramCredentialsError: 'Credenciales de Telegram no configuradas en .env (se necesitan VITE_TELEGRAM_BOT_TOKEN y VITE_TELEGRAM_CHAT_ID)',
    telegramSuccess: '¡Notificación enviada a Telegram con éxito! Revisa tu chat.',
    telegramError: 'Error de Telegram:',
    telegramNetworkError: 'Error de red al intentar conectarse con Telegram.',
    createAlertError: 'Error al crear la alerta',
    belowConditionText: 'Menor a',
    aboveConditionText: 'Mayor a',
    equalsConditionText: 'Igual a',

    // AI Assistant
    aiGreeting: '¡Hola! Soy tu asistente de compras inteligente. 🤖\n\n¿En qué te puedo ayudar hoy? Podés preguntarme sobre productos específicos, presupuestos, o cuándo conviene comprar.',
    aiProductContextIntro: 'Entendido. Vamos a hablar sobre',
    aiProductContextPrompt: '¿Qué te gustaría saber sobre este producto? (por ejemplo, si conviene comprarlo o si hay mejores opciones).',
    aiError: 'Disculpame, tuve un problema al procesar tu consulta. Por favor, intentá de nuevo en unos instantes.',
    aiClearChat: 'Chat reiniciado. ¿En qué te puedo ayudar hoy?',
    aiSuggestionsLabel: 'Preguntas sugeridas',
    aiSug1: '¿Qué celular me recomendás con buena cámara?',
    aiSug2: '¿Cómo sé si un producto está a buen precio?',
    aiSug3: '¿Qué es conveniente comprar hoy?',
    aiSug4: 'Dame consejos para ahorrar en mis compras online',
    aiTitle: 'Asistente de Compras IA',
    aiSubtitle: 'Respondido por ChatGPT (gpt-4o-mini)',
    aiClearBtn: 'Limpiar chat',
    aiProductContextBanner: 'Preguntando sobre:',
    aiThinking: 'Pensando',
    aiPlaceholderWithProduct: 'Preguntale a la IA sobre',
    aiPlaceholderWithoutProduct: 'Escribí tu consulta sobre ofertas, precios...',

    // Floating Chat
    floatingGreeting: '¡Hola! 🤖 Soy PriceBot, tu asistente de compras flotante. Preguntame lo que quieras sobre ofertas y precios.',
    floatingError: 'Ups, tuve un problema. Por favor, intentá de nuevo.',
    floatingTitle: 'Asistente PriceBot',
    floatingStatus: 'Online • GPT-4o-mini',
    floatingPlaceholder: 'Preguntale algo a la IA...',
    floatingTooltip: 'Chatear con IA'
  },
  en: {
    // Header & Sidebar
    dashboard: 'Dashboard',
    search: 'Search',
    favorites: 'Favorites',
    alerts: 'Alerts',
    aiAssistant: 'AI Assistant',
    searchPlaceholder: 'Search products...',
    usaDefault: 'USA (default)',
    newYork: 'New York, NY',
    losAngeles: 'Los Angeles, CA',
    chicago: 'Chicago, IL',
    houston: 'Houston, TX',
    miami: 'Miami, FL',
    priceCompare: 'PriceCompare',
    
    // Dashboard
    dashboardTitle: 'Dashboard',
    dashboardSubtitle: 'Overview of the price comparison and AI system',
    system: 'System',
    active: 'Active',
    connectedBackend: 'Connected to local backend',
    statsFavorites: 'Favorites',
    statsFavoritesDesc: 'Products saved to your list',
    statsTotalAlerts: 'Total Alerts',
    statsTotalAlertsDesc: 'Monitoring price variations',
    statsActiveAlerts: 'Active Alerts',
    statsActiveAlertsDesc: 'Telegram notifications enabled',
    opportunitiesTitle: 'Today\'s Opportunities (Best Discounts)',
    opportunitiesSubtitle: 'Historical Average Analysis',
    noOpportunities: 'No significant offers found yet.',
    noOpportunitiesHint: 'Search and open new products to collect history and detect opportunities.',
    savingPercent: '% savings',
    viewOffer: 'View offer',
    startSearchingTitle: 'Start searching',
    startSearchingDesc1: 'Use the search bar above to find and compare product prices across multiple stores.',
    startSearchingDesc2: 'When you open any product detail, the AI will analyze the history and give you instant convenience tips.',
    readyToUse: 'Ready to use',

    // Search Results
    searchResultsTitle: 'Search Results',
    searchQueryLabel: 'Search',
    searchResultsCount: 'result',
    searchResultsCount_plural: 'results',
    noResultsWithQuery: 'No products found with the specified criteria.',
    noResultsWithoutQuery: 'Perform a search to see results.',

    // Favorites
    favoritesTitle: 'Favorites',
    favoritesSubtitle: 'Manage your favorite products',
    noFavoritesTitle: 'You have no favorites',
    noFavoritesDesc: 'Add products to favorites to save them here',

    // Alerts
    alertsTitle: 'Price Alerts',
    alertsSubtitle: 'Configure alerts to receive notifications when prices change',
    newAlert: 'New Alert',
    createAlertTitle: 'Create Price Alert',
    productFieldLabel: 'Product (Name)',
    productPlaceholder: 'Ex: iPhone 15 Pro',
    conditionFieldLabel: 'Condition',
    conditionBelow: 'Below',
    conditionAbove: 'Above',
    conditionEquals: 'Equals',
    targetPriceLabel: 'Target Price',
    createAlertBtn: 'Create Alert',
    cancelBtn: 'Cancel',
    noAlertsTitle: 'You have no alerts configured',
    noAlertsDesc: 'Create alerts to receive notifications when prices change',
    createFirstAlertBtn: 'Create First Alert',
    productColumn: 'Product',
    conditionColumn: 'Condition',
    statusColumn: 'Status',
    actionsColumn: 'Actions',
    conditionMetBadge: 'Condition Met',
    activeBadge: 'Active',
    pausedBadge: 'Paused',
    testNotificationTitle: 'Test Notification',
    pauseTitle: 'Pause',
    activateTitle: 'Activate',
    deleteTitle: 'Delete',
    deleteConfirm: 'Are you sure you want to delete this alert?',
    telegramCredentialsError: 'Telegram credentials not configured in .env (VITE_TELEGRAM_BOT_TOKEN and VITE_TELEGRAM_CHAT_ID are required)',
    telegramSuccess: 'Notification sent to Telegram successfully! Check your chat.',
    telegramError: 'Telegram Error:',
    telegramNetworkError: 'Network error trying to connect to Telegram.',
    createAlertError: 'Error creating alert',
    belowConditionText: 'Below',
    aboveConditionText: 'Above',
    equalsConditionText: 'Equals',

    // AI Assistant
    aiGreeting: 'Hello! I\'m your smart shopping assistant. 🤖\n\nHow can I help you today? You can ask me about specific products, budgets, or when it\'s a good time to buy.',
    aiProductContextIntro: 'Got it. Let\'s talk about',
    aiProductContextPrompt: 'What would you like to know about this product? (e.g., if it\'s worth buying or if there are better options).',
    aiError: 'Sorry, I had a problem processing your query. Please try again in a few moments.',
    aiClearChat: 'Chat cleared. How can I help you today?',
    aiSuggestionsLabel: 'Suggested Questions',
    aiSug1: 'What phone do you recommend with a good camera?',
    aiSug2: 'How do I know if a product is at a good price?',
    aiSug3: 'What is worth buying today?',
    aiSug4: 'Give me tips to save on my online purchases',
    aiTitle: 'AI Shopping Assistant',
    aiSubtitle: 'Powered by ChatGPT (gpt-4o-mini)',
    aiClearBtn: 'Clear Chat',
    aiProductContextBanner: 'Asking about:',
    aiThinking: 'Thinking',
    aiPlaceholderWithProduct: 'Ask the AI about',
    aiPlaceholderWithoutProduct: 'Write your query about offers, prices...',

    // Floating Chat
    floatingGreeting: 'Hi! 🤖 I\'m PriceBot, your floating shopping assistant. Ask me anything about offers and prices.',
    floatingError: 'Oops, I had a problem. Please try again.',
    floatingTitle: 'PriceBot Assistant',
    floatingStatus: 'Online • GPT-4o-mini',
    floatingPlaceholder: 'Ask the AI something...',
    floatingTooltip: 'Chat with AI'
  }
};

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>(() => {
    const saved = localStorage.getItem('language');
    return (saved as Language) || 'es';
  });

  const t = (key: string): string => {
    return translations[language][key] || key;
  };

  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
}
