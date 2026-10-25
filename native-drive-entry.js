import { GoogleAuth } from '@codetrix-studio/capacitor-google-auth';
// Inicializar antes del primer signIn; evita usar el cliente Android sin preparar.
GoogleAuth.initialize();
window.DJSuarezGoogleAuth = GoogleAuth;
