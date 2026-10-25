import { GoogleAuth } from '@codetrix-studio/capacitor-google-auth';
// Inicializar antes del primer signIn; evita usar el cliente Android sin preparar.
GoogleAuth.initialize();
window.DJSuarezGoogleAuth = GoogleAuth;

import { Filesystem, Directory } from '@capacitor/filesystem';
import { Share } from '@capacitor/share';
window.DJSuarezSaveRecording = async (blob, filename) => {
  const reader = new FileReader();
  const data = await new Promise((resolve, reject) => {
    reader.onload = () => resolve(String(reader.result).split(',')[1]);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
  const saved = await Filesystem.writeFile({path:filename,data,directory:Directory.Documents,recursive:true});
  try { await Share.share({title:'Mezcla DJ SUAREZ',url:saved.uri,dialogTitle:'Guardar o compartir mezcla'}); }
  catch (err) { if (!String(err?.message||'').toLowerCase().includes('cancel')) throw err; }
  return saved.uri;
};
