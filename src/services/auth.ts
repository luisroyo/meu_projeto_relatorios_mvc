import { apiFetch } from './api';

export async function login(email: string, password: string) {
    return apiFetch('/api/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
    });
} 