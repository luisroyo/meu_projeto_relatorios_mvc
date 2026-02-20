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

async function connectToWhatsApp() {
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
        printQRInTerminal: true,
        logger,
        browser: ['GestaoSeguranca', 'Chrome', '10.0'],
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
            const shouldReconnect = (lastDisconnect?.error instanceof Boom)?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('Conexão fechada devido a ', lastDisconnect?.error, ', reconectando:', shouldReconnect);
            
            if (shouldReconnect) {
                connectionStatus = 'reconnecting';
                connectToWhatsApp();
            } else {
                console.log('Você foi deslogado. Apague a pasta auth_info_baileys para gerar um novo QR Code.');
            }
        } else if (connection === 'open') {
            console.log('✅ WhatsApp Conectado com Sucesso!');
            currentQR = null;
            connectionStatus = 'connected';
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
                timestamp: m.messageTimestamp
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
}

// ============================================
// API Endpoints Internos do Serviço Node
// ============================================

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
