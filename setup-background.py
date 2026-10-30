from pathlib import Path
p=Path("android/app/src/main")
m=p/"AndroidManifest.xml"
s=m.read_text()
s=s.replace("<application",'<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />\n<uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK" />\n<application',1)
s=s.replace("</application>",'<service android:name=".DJPlaybackService" android:exported="false" android:foregroundServiceType="mediaPlayback" />\n</application>',1)
m.write_text(s)
j=p/"java/com/djsuarez/app"
j.mkdir(parents=True,exist_ok=True)
(j/"DJPlaybackService.java").write_text("""package com.djsuarez.app;
import android.app.*;
import android.content.*;
import android.content.pm.ServiceInfo;
import android.os.*;
public class DJPlaybackService extends Service {
 static final String CHANNEL="dj_playback";
 @Override public void onCreate(){super.onCreate();getSystemService(NotificationManager.class).createNotificationChannel(new NotificationChannel(CHANNEL,"DJ SUAREZ",NotificationManager.IMPORTANCE_LOW));}
 @Override public int onStartCommand(Intent intent,int flags,int id){
  if(intent!=null&&"STOP".equals(intent.getAction())){stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();return START_NOT_STICKY;}
  PendingIntent pi=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
  Notification n=new Notification.Builder(this,CHANNEL).setContentTitle("DJ SUAREZ").setContentText("Música en reproducción").setSmallIcon(android.R.drawable.ic_media_play).setContentIntent(pi).setOngoing(true).build();
  if(Build.VERSION.SDK_INT>=29)startForeground(1107,n,ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK);else startForeground(1107,n);
  return START_STICKY;
 }
 @Override public IBinder onBind(Intent intent){return null;}
}
""")
(j/"MainActivity.java").write_text("""package com.djsuarez.app;
import com.getcapacitor.BridgeActivity;
import android.content.*;
import android.webkit.*;
import android.os.*;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.database.Cursor;
import android.util.Base64;
import java.io.InputStream;
import java.util.ArrayList;
import org.json.JSONArray;
import org.json.JSONObject;
public class MainActivity extends BridgeActivity {
 private static final int DJ_PICK_FOLDER=5714;
 private final ArrayList<Uri> localUris=new ArrayList<>();
 private final ArrayList<String> localNames=new ArrayList<>();
 private String selectedFolderName="Música";
 private void report(String event,String data){
   runOnUiThread(()->getBridge().getWebView().evaluateJavascript(
     "window.DJNativeFolderEvent&&window.DJNativeFolderEvent("+JSONObject.quote(event)+","+data+")",null));
 }
 private void enumerate(Uri tree,String parent,String name,int depth)throws Exception{
   if(depth>12||localUris.size()>10000)return;
   Uri children=DocumentsContract.buildChildDocumentsUriUsingTree(tree,parent);
   try(Cursor cursor=getContentResolver().query(children,
      new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME,
        DocumentsContract.Document.COLUMN_MIME_TYPE},null,null,null)){
     if(cursor==null)return;
     while(cursor.moveToNext()){
       String id=cursor.getString(0),title=cursor.getString(1),mime=cursor.getString(2);
       if(DocumentsContract.Document.MIME_TYPE_DIR.equals(mime))enumerate(tree,id,title,depth+1);
       else if(title!=null&&title.toLowerCase(java.util.Locale.ROOT).matches(".*[.](mp3|m4a|aac|flac|wav|ogg|opus|wma|aiff|alac)$")){
         localUris.add(DocumentsContract.buildDocumentUriUsingTree(tree,id));localNames.add(title);
       }
     }
   }
 }
 public class FolderBridge {
   @JavascriptInterface public void chooseFolder(){runOnUiThread(()->{
     Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
     intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
     startActivityForResult(intent,DJ_PICK_FOLDER);
   });}
   @JavascriptInterface public String folderName(){return selectedFolderName;}
   @JavascriptInterface public int fileCount(){return localUris.size();}
   @JavascriptInterface public String fileName(int index){return index>=0&&index<localNames.size()?localNames.get(index):"";}
   @JavascriptInterface public long fileSize(int index){
     if(index<0||index>=localUris.size())return -1;
     try(Cursor c=getContentResolver().query(localUris.get(index),
       new String[]{DocumentsContract.Document.COLUMN_SIZE},null,null,null)){
       if(c!=null&&c.moveToFirst())return c.isNull(0)?-1:c.getLong(0);
     }catch(Exception ignored){}return -1;
   }
   @JavascriptInterface public String readChunk(int index,long offset,int length){
     if(index<0||index>=localUris.size()||offset<0||length<1||length>262144)return "";
     try(InputStream input=getContentResolver().openInputStream(localUris.get(index))){
       if(input==null)return "";
       long left=offset;
       while(left>0){long skipped=input.skip(left);if(skipped>0){left-=skipped;continue;}
         if(input.read()<0)return "";left--;}
       byte[] bytes=new byte[length];int size=0;
       while(size<length){int got=input.read(bytes,size,length-size);if(got<0)break;size+=got;}
       return Base64.encodeToString(bytes,0,size,Base64.NO_WRAP);
     }catch(Exception e){return "";}
   }
 }
 @Override protected void onActivityResult(int request,int result,Intent data){
   super.onActivityResult(request,result,data);
   if(request!=DJ_PICK_FOLDER)return;
   if(result!=RESULT_OK||data==null||data.getData()==null){
     report("cancel", "{}");return;
   }
   final Uri tree=data.getData();
   new Thread(()->{
     try{
       localUris.clear();localNames.clear();
       String id=DocumentsContract.getTreeDocumentId(tree);
       try(Cursor c=getContentResolver().query(
         DocumentsContract.buildDocumentUriUsingTree(tree,id),
         new String[]{DocumentsContract.Document.COLUMN_DISPLAY_NAME},null,null,null)){
           if(c!=null&&c.moveToFirst())selectedFolderName=c.getString(0);
       }
       enumerate(tree,id,selectedFolderName,0);
       report("ready",new JSONObject().put("count",localUris.size())
         .put("name",selectedFolderName).toString());
     }catch(Exception e){report("error",new JSONObject().put("message",e.toString()).toString());}
   }).start();
 }

 public class PlaybackBridge {
  @JavascriptInterface public void setPlaying(boolean playing){
   runOnUiThread(()->{
    Intent intent=new Intent(MainActivity.this,DJPlaybackService.class);
    if(playing){if(Build.VERSION.SDK_INT>=26)startForegroundService(intent);else startService(intent);}
    else stopService(intent);
   });
  }
 }
 @Override public void onCreate(Bundle state){
  super.onCreate(state);
  getBridge().getWebView().addJavascriptInterface(new PlaybackBridge(),"DJNativePlayback");
  getBridge().getWebView().addJavascriptInterface(new FolderBridge(),"DJNativeFolder");
 }
}
""")
