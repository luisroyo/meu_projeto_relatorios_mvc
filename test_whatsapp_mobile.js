#!/usr/bin/env python3
"""
Script para testar a funcionalidade de WhatsApp mobile
"""

// Função para detectar dispositivos mobile
function isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// Função para testar envio de WhatsApp
function testWhatsAppSend(text) {
    console.log("🧪 Testando envio de WhatsApp...");
    console.log("Dispositivo mobile:", isMobile());
    console.log("Texto a enviar:", text);
    
    const textoCodificado = encodeURIComponent(text);
    
    if (isMobile()) {
        console.log("📱 Dispositivo mobile detectado");
        console.log("App URL:", `whatsapp://send?text=${textoCodificado}`);
        console.log("Web URL:", `https://wa.me/?text=${textoCodificado}`);
        
        // Tentar app primeiro
        const appWindow = window.open(`whatsapp://send?text=${textoCodificado}`, '_blank');
        
        // Fallback para web após 1 segundo
        setTimeout(() => {
            if (appWindow && appWindow.closed) {
                console.log("⚠️ App não abriu, tentando web...");
                window.open(`https://wa.me/?text=${textoCodificado}`, '_blank');
            } else {
                console.log("✅ App aberto com sucesso");
            }
        }, 1000);
        
    } else {
        console.log("💻 Dispositivo desktop detectado");
        console.log("Web URL:", `https://wa.me/?text=${textoCodificado}`);
        window.open(`https://wa.me/?text=${textoCodificado}`, '_blank');
    }
}

// Teste automático
if (typeof window !== 'undefined') {
    console.log("🚀 Iniciando teste de WhatsApp mobile...");
    console.log("User Agent:", navigator.userAgent);
    
    // Teste com texto de exemplo
    const testText = "Teste de envio via WhatsApp - Sistema de Rondas";
    testWhatsAppSend(testText);
    
    // Expor função para testes manuais
    window.testWhatsAppSend = testWhatsAppSend;
    window.isMobile = isMobile;
    
    console.log("✅ Funções expostas: window.testWhatsAppSend() e window.isMobile()");
} 