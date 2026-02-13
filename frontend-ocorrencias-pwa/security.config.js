// Configurações de Segurança para Produção
module.exports = {
  // Configurações de ambiente
  environment: {
    NODE_ENV: 'production',
    REACT_APP_API_BASE_URL: 'https://processador-relatorios-ia.onrender.com',
    GENERATE_SOURCEMAP: false,
    INLINE_RUNTIME_CHUNK: false
  },

  // Headers de segurança
  securityHeaders: {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
    'Content-Security-Policy': "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval'; script-src 'self' https: 'unsafe-inline' 'unsafe-eval'; style-src 'self' https: 'unsafe-inline'; img-src 'self' https: data:; font-src 'self' https: data:; connect-src 'self' https:; frame-src 'none'; object-src 'none';"
  },

  // Configurações de cache
  cacheConfig: {
    staticAssets: 'public, max-age=31536000, immutable',
    htmlFiles: 'public, max-age=0, must-revalidate'
  },

  // Configurações de CORS
  corsConfig: {
    origin: ['https://*.onrender.com', 'https://*.vercel.app'],
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    credentials: true
  },

  // Configurações de rate limiting
  rateLimit: {
    windowMs: 15 * 60 * 1000, // 15 minutos
    max: 100 // limite por IP
  }
};
