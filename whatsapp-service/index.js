require('dotenv').config();
const { default: makeWASocket, DisconnectReason, useMultiFileAuthState } = require('@whiskeysockets/baileys');
const { usePostgresAuthState } = require('./db-auth-state');
const { Boom } = require('@hapi/boom');
const qrcode = require('qrcode');
const axios = require('axios');
const express = require('express');
const cors = require('cors');
const pino = require('pino');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.WHATSAPP_PORT || 3001;
const API_URL = process.env.PYTHON_API_URL || 'http://localhost:5000/api/whatsapp/webhook';

let sock;
let currentQR = null;
let connectionStatus = 'initializing';
let globalClearSession = null; // Será definido em connectToWhatsApp
let isConnecting = false; // Guard contra reconexões simultâneas

// Buffer simples de mensagens por grupo (Map: jid -> array de msgs)
// Guarda as últimas 500 mensagens por grupo em memória
const messageBuffer = new Map();
const MAX_BUFFER_PER_GROUP = 500;

function bufferMessage(jid, msgPayload) {
    if (!messageBuffer.has(jid)) {
        messageBuffer.set(jid, []);
    }
    const arr = messageBuffer.get(jid);
    arr.push(msgPayload);
    // Manter apenas as últimas MAX_BUFFER_PER_GROUP mensagens
    if (arr.length > MAX_BUFFER_PER_GROUP) {
        arr.shift();
    }
}

// Converte timestamp do Baileys (pode ser protobuf Long {low,high,unsigned} ou número) para Unix timestamp
function normalizeTimestamp(ts) {
    if (ts === null || ts === undefined) return Math.floor(Date.now() / 1000);
    if (typeof ts === 'number') return ts;
    if (typeof ts === 'object' && ts.low !== undefined) return ts.low;
    if (typeof ts === 'string') return parseInt(ts, 10) || Math.floor(Date.now() / 1000);
    return Math.floor(Date.now() / 1000);
}

async function connectToWhatsApp() {
    // Guard: evita múltiplas conexões simultâneas
    if (isConnecting) {
        console.log('[Guard] Já existe uma conexão em andamento, ignorando...');
        return;
    }
    isConnecting = true;

    try {
        // Usa Postgres em produção (Render/Neon), arquivo local em dev
        let authState, saveCreds, clearSession;
        if (process.env.DATABASE_URL) {
            console.log('[Auth] Usando sessão em Postgres (produção)');
            const dbAuth = await usePostgresAuthState();
            authState = dbAuth.state;
            saveCreds = dbAuth.saveCreds;
            clearSession = dbAuth.clearSession;
        } else {
            console.log('[Auth] Usando sessão em arquivo (desenvolvimento local)');
            const fileAuth = await useMultiFileAuthState('auth_info_baileys');
            authState = fileAuth.state;
            saveCreds = fileAuth.saveCreds;
            clearSession = async () => {
                const fs = require('fs');
                const path = require('path');
                const dir = 'auth_info_baileys';
                if (fs.existsSync(dir)) {
                    fs.readdirSync(dir).forEach(f => fs.unlinkSync(path.join(dir, f)));
                }
            };
        }

        // Guarda clearSession globalmente para usar no logout
        globalClearSession = clearSession;
        const logger = pino({ level: 'silent' });

        sock = makeWASocket({
            auth: authState,
            logger,
            browser: ['GestaoSeguranca', 'Desktop', '10.0'],
            syncFullHistory: true,
        });

        sock.ev.on('creds.update', saveCreds);

        sock.ev.on('connection.update', (update) => {
            const { connection, lastDisconnect, qr } = update;

            if (qr) {
                console.log('\n[!] Novo QR Code gerado. Escaneie com seu WhatsApp.\n');
                qrcode.toDataURL(qr, (err, url) => {
                    if (!err) currentQR = url;
                });
                connectionStatus = 'qr_ready';
            }

            if (connection === 'close') {
                currentQR = null;
                connectionStatus = 'disconnected';
                isConnecting = false; // Libera o guard

                const error = lastDisconnect?.error;
                const statusCode = error?.output?.statusCode;
                const isLoggedOut = statusCode === DisconnectReason.loggedOut;
                const isConflict = statusCode === 440;

                console.log(`[Conexão] Fechada. Status: ${statusCode}, LoggedOut: ${isLoggedOut}, Conflict: ${isConflict}`);

                if (isLoggedOut) {
                    console.log('[Conexão] Deslogado. Necessário escanear novo QR Code.');
                } else if (isConflict) {
                    console.log('[Conexão] Conflito detectado. Aguardando 10s antes de reconectar...');
                    connectionStatus = 'reconnecting';
                    setTimeout(() => connectToWhatsApp(), 10000);
                } else {
                    console.log('[Conexão] Reconectando em 3s...');
                    connectionStatus = 'reconnecting';
                    setTimeout(() => connectToWhatsApp(), 3000);
                }
            } else if (connection === 'open') {
                console.log('✅ WhatsApp Conectado com Sucesso!');
                currentQR = null;
                connectionStatus = 'connected';
                isConnecting = false;
            }
        });

        // Escutar por novas mensagens e também mensagens históricas (type='append')
        sock.ev.on('messages.upsert', async ({ messages, type }) => {
            for (const m of messages) {
                if (!m.message) continue;

                const remoteJid = m.key.remoteJid;

                // Focar só em grupos de residenciais
                if (!remoteJid || !remoteJid.endsWith('@g.us')) continue;

                // Extrair texto da mensagem
                const textMessage = m.message.conversation || m.message.extendedTextMessage?.text;
                if (!textMessage) continue;

                const participantJid = m.key.participant || remoteJid;
                const pushName = m.pushName || '';

                const payload = {
                    message_id: m.key.id,
                    group_id: remoteJid,
                    participant_id: participantJid,
                    push_name: pushName,
                    content: textMessage,
                    timestamp: normalizeTimestamp(m.messageTimestamp)
                };

                // Sempre adicionar ao buffer local (funciona para histórico e tempo real)
                bufferMessage(remoteJid, payload);

                // Enviar via Webhook para o backend Python (tanto tempo real quanto histórico)
                try {
                    await axios.post(API_URL, payload);
                    if (type === 'notify') {
                        console.log(`[Webhook RT] "${textMessage.substring(0, 40)}..." -> ${remoteJid}`);
                    }
                } catch (error) {
                    // Não logar erros de sincronia histórica para não poluir o console
                    if (type === 'notify') {
                        console.error(`[Webhook Erro] ${error.message}`);
                    }
                }
            }
        });

        // Captura mensagens históricas sincronizadas pelo WhatsApp ao conectar
        sock.ev.on('messaging-history.set', async ({ messages: histMessages }) => {
            console.log(`[History Sync] Recebidas ${histMessages.length} mensagens históricas`);
            let saved = 0;
            for (const m of histMessages) {
                if (!m.message) continue;
                const remoteJid = m.key.remoteJid;
                if (!remoteJid || !remoteJid.endsWith('@g.us')) continue;

                const textMessage = m.message.conversation || m.message.extendedTextMessage?.text;
                if (!textMessage) continue;

                const participantJid = m.key.participant || remoteJid;
                const pushName = m.pushName || '';

                const payload = {
                    message_id: m.key.id,
                    group_id: remoteJid,
                    participant_id: participantJid,
                    push_name: pushName,
                    content: textMessage,
                    timestamp: normalizeTimestamp(m.messageTimestamp)
                };

                bufferMessage(remoteJid, payload);

                try {
                    await axios.post(API_URL, payload);
                    saved++;
                } catch (error) {
                    // Silencia erros de webhook para histórico
                }
            }
            console.log(`[History Sync] ${saved} mensagens de grupo salvas via webhook`);
        });
    } catch (err) {
        console.error('[connectToWhatsApp] Erro fatal:', err);
        isConnecting = false;
    }
}

// ============================================
// API Endpoints Internos do Serviço Node
// ============================================

// Página visual para escanear o QR Code
app.get('/', (req, res) => {
    res.send(`<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp - QR Code</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #0a1628; color: #fff;
               display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .card { background: #1a2942; border-radius: 16px; padding: 40px; text-align: center;
                box-shadow: 0 8px 32px rgba(0,0,0,0.4); max-width: 420px; width: 90%; }
        h1 { font-size: 1.4rem; margin-bottom: 8px; }
        .status { font-size: 0.9rem; margin-bottom: 20px; padding: 6px 16px; border-radius: 20px;
                  display: inline-block; }
        .status.connected { background: #22c55e33; color: #22c55e; }
        .status.qr_ready { background: #3b82f633; color: #3b82f6; }
        .status.disconnected { background: #ef444433; color: #ef4444; }
        .status.initializing, .status.reconnecting { background: #eab30833; color: #eab308; }
        #qr-img { border-radius: 12px; background: #fff; padding: 12px; max-width: 280px; }
        .msg { color: #94a3b8; margin-top: 12px; font-size: 0.85rem; }
        .ok { font-size: 3rem; margin: 20px 0; }
        .btn { padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer;
               font-size: 0.9rem; margin: 4px; color: #fff; }
        .btn-resync { background: #f59e0b; }
        .btn-resync:hover { background: #d97706; }
        .btn-danger { background: #ef4444; }
        .btn-danger:hover { background: #dc2626; }
    </style>
</head>
<body>
    <div class="card">
        <h1>📱 WhatsApp Service</h1>
        <div id="content">Carregando...</div>
    </div>
    <script>
        async function refresh() {
            try {
                const r = await fetch('/api/whatsapp/status');
                const d = await r.json();
                const el = document.getElementById('content');
                if (d.status === 'connected') {
                    el.innerHTML = '<div class="status connected">✅ Conectado</div>' +
                        '<div class="ok">🟢</div><p class="msg">WhatsApp conectado e funcionando!</p>' +
                        '<button class="btn btn-resync" onclick="resync()">🔄 Forçar Re-Sync (puxar histórico)</button>';
                } else if (d.status === 'qr_ready' && d.qr) {
                    el.innerHTML = '<div class="status qr_ready">📷 Aguardando scan</div>' +
                        '<br><img id="qr-img" src="' + d.qr + '" alt="QR Code">' +
                        '<p class="msg">Abra o WhatsApp → Dispositivos Conectados → Escanear</p>';
                } else {
                    el.innerHTML = '<div class="status ' + d.status + '">' + d.status + '</div>' +
                        '<p class="msg">Aguardando conexão...</p>';
                }
            } catch(e) { console.error(e); }
        }
        async function resync() {
            if (!confirm('Isso vai desconectar o WhatsApp e gerar um novo QR Code para sincronizar o histórico. Continuar?')) return;
            try {
                const r = await fetch('/api/whatsapp/resync', { method: 'POST' });
                const d = await r.json();
                alert(d.message);
                refresh();
            } catch(e) { alert('Erro: ' + e.message); }
        }
        refresh();
        setInterval(refresh, 3000);
    </script>
</body>
</html>`);
});

app.get('/api/whatsapp/status', (req, res) => {
    res.json({
        status: connectionStatus,
        qr: currentQR
    });
});

app.post('/api/whatsapp/logout', async (req, res) => {
    try {
        if (sock) {
            await sock.logout();
            res.json({ success: true, message: 'Deslogado com sucesso' });
        } else {
            res.json({ success: false, message: 'Não está conectado' });
        }
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// Endpoint para forçar re-sync: limpa sessão e reconecta para puxar histórico
app.post('/api/whatsapp/resync', async (req, res) => {
    try {
        console.log('[Resync] Iniciando re-sincronização forçada...');
        // 1. Desconecta o socket atual
        if (sock) {
            sock.end(undefined);
        }
        // 2. Limpa a sessão no banco
        if (globalClearSession) {
            await globalClearSession();
            console.log('[Resync] Sessão limpa do banco.');
        }
        // 3. Limpa buffers
        messageBuffer.clear();
        // 4. Reconecta (vai gerar novo QR Code e sincronizar histórico)
        connectionStatus = 'initializing';
        currentQR = null;
        setTimeout(() => connectToWhatsApp(), 1000);
        res.json({ success: true, message: 'Re-sync iniciado! Escaneie o novo QR Code para sincronizar o histórico.' });
    } catch (error) {
        console.error('[Resync] Erro:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Endpoint para buscar mensagens do buffer local (histórico acumulado desde o início do serviço)
app.get('/api/whatsapp/messages/:jid', (req, res) => {
    const jid = decodeURIComponent(req.params.jid);
    const count = parseInt(req.query.count) || 100;

    if (!sock || connectionStatus !== 'connected') {
        return res.status(400).json({ error: 'WhatsApp não está conectado' });
    }

    const messages = messageBuffer.get(jid) || [];
    // Retorna as últimas `count` mensagens
    const slice = messages.slice(-count);

    res.json({ success: true, count: slice.length, messages: slice });
});

// Obtém todos os grupos em que o bot participa
app.get('/api/whatsapp/groups', async (req, res) => {
    if (!sock || connectionStatus !== 'connected') {
        return res.status(400).json({ error: 'WhatsApp não está conectado' });
    }

    try {
        const groups = await sock.groupFetchAllParticipating();
        const groupList = Object.values(groups).map(g => ({
            id: g.id,
            subject: g.subject,
            participantsCount: g.participants.length
        }));

        res.json(groupList);
    } catch (error) {
        console.error('Erro ao buscar grupos:', error);
        res.status(500).json({ error: 'Erro ao buscar grupos' });
    }
});

// ============================================
// Inicialização
// ============================================
app.listen(PORT, () => {
    console.log(`🚀 Serviço Node.js WhatsApp rodando na porta ${PORT}`);
    connectToWhatsApp();
});
