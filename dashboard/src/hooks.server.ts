import { error } from '@sveltejs/kit';
import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
    const headers = event.request.headers;
    const userEmail = headers.get('x-forwarded-email') || 
                      headers.get('x-auth-request-email') ||
                      headers.get('x-auth-request-user') ||
                      headers.get('x-forwarded-user') ||
                      headers.get('x-auth-request-preferred-username');

    // Debugging header propagation (Disable on production once verified)
    /*
    if (process.env.NODE_ENV === 'production') {
        const headerNames = Array.from(headers.keys()).join(', ');
        console.log(`[AuthDebug] Path: ${event.url.pathname}, Email: ${userEmail}, Headers: ${headerNames}`);
        if (!userEmail) {
            console.log('[AuthDebug] All Headers:', JSON.stringify(Object.fromEntries(headers.entries())));
        }
    }
    */

    // Health check bypass
    if (event.url.pathname === '/healthz' || event.url.pathname === '/api/healthz' || event.url.pathname.startsWith('/oauth2/')) {
        return resolve(event);
    }

    if (!userEmail) {
        if (process.env.NODE_ENV === 'production') {
            console.error(`[Auth] Redirecting to login: ${event.url.pathname}`);
            // Redirect to oauth2-proxy start endpoint
            return new Response(null, {
                status: 302,
                headers: {
                    'Location': '/oauth2/start?rd=' + encodeURIComponent(event.url.pathname + event.url.search)
                }
            });
        }
        // Dev mode mock
        event.locals.userEmail = 'dev@example.com';
    } else {
        // Whitelist check
        const allowedEmails = (process.env.ALLOWED_EMAILS || 'pascalm3@gmail.com').split(',').map(e => e.trim()).filter(e => e);
        if (allowedEmails.length > 0 && !allowedEmails.includes(userEmail)) {
            // Optional: Backup check via IAM if not in whitelist
            const { checkUserPermission } = await import('./lib/gcp/auth');
            const hasPermission = await checkUserPermission(userEmail);
            if (!hasPermission) {
                console.warn(`[Auth] Access Denied: ${userEmail}`);
                throw error(403, `Access Denied: ${userEmail} is not authorized.`);
            }
        }
        event.locals.userEmail = userEmail;
    }

    return resolve(event);
};
