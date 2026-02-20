/**
 * Baileys Auth State using PostgreSQL (Neon)
 * Replaces useMultiFileAuthState for production deployments where disk is ephemeral.
 *
 * Requires a table in your Postgres DB:
 *   CREATE TABLE IF NOT EXISTS whatsapp_session (
 *     key TEXT PRIMARY KEY,
 *     value TEXT NOT NULL
 *   );
 */

const { initAuthCreds, BufferJSON } = require('@whiskeysockets/baileys');
const { Pool } = require('pg');

let pool;

function getPool() {
    if (!pool) {
        const connectionString = process.env.DATABASE_URL;
        if (!connectionString) {
            throw new Error('DATABASE_URL environment variable is not set');
        }
        pool = new Pool({
            connectionString,
            ssl: { rejectUnauthorized: false } // Necessário para Neon
        });
    }
    return pool;
}

async function ensureTable() {
    const db = getPool();
    await db.query(`
        CREATE TABLE IF NOT EXISTS whatsapp_session (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    `);
}

async function usePostgresAuthState() {
    await ensureTable();
    const db = getPool();

    const writeData = async (key, data) => {
        const value = JSON.stringify(data, BufferJSON.replacer);
        await db.query(
            `INSERT INTO whatsapp_session (key, value) VALUES ($1, $2)
             ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value`,
            [key, value]
        );
    };

    const readData = async (key) => {
        const res = await db.query('SELECT value FROM whatsapp_session WHERE key = $1', [key]);
        if (res.rows.length === 0) return null;
        return JSON.parse(res.rows[0].value, BufferJSON.reviver);
    };

    const removeData = async (key) => {
        await db.query('DELETE FROM whatsapp_session WHERE key = $1', [key]);
    };

    const creds = (await readData('creds')) || initAuthCreds();

    return {
        state: {
            creds,
            keys: {
                get: async (type, ids) => {
                    const data = {};
                    for (const id of ids) {
                        const value = await readData(`${type}-${id}`);
                        data[id] = value;
                    }
                    return data;
                },
                set: async (data) => {
                    for (const [category, entries] of Object.entries(data)) {
                        for (const [id, value] of Object.entries(entries)) {
                            if (value) {
                                await writeData(`${category}-${id}`, value);
                            } else {
                                await removeData(`${category}-${id}`);
                            }
                        }
                    }
                }
            }
        },
        saveCreds: async () => {
            await writeData('creds', creds);
        },
        clearSession: async () => {
            await db.query('DELETE FROM whatsapp_session');
            console.log('[Auth] Sessão apagada do banco de dados.');
        }
    };
}

module.exports = { usePostgresAuthState };
