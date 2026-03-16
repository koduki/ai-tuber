import { error } from '@sveltejs/kit';
import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
    const userEmail = event.request.headers.get('x-forwarded-email') || 
                      event.request.headers.get('x-auth-request-email');

    // Health check bypass
    if (event.url.pathname === '/healthz' || event.url.pathname === '/api/healthz') {
        return resolve(event);
    }

    if (!userEmail) {
        if (process.env.NODE_ENV === 'production') {
            console.error('Unauthorized access attempt: missing auth headers');
            throw error(401, 'Unauthorized: Missing auth headers from proxy');
        }
        // Dev mode mock
        event.locals.userEmail = 'dev@example.com';
    } else {
        // Whitelist check
        const allowedEmails = (process.env.ALLOWED_EMAILS || '').split(',').map(e => e.trim()).filter(e => e);
        if (allowedEmails.length > 0 && !allowedEmails.includes(userEmail)) {
            console.warn(`Access Denied: ${userEmail} is not in whilte list.`);
            throw error(403, `Access Denied: ${userEmail} is not authorized.`);
        }
        event.locals.userEmail = userEmail;
    }

    return resolve(event);
};
