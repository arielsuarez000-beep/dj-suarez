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
public class MainActivity extends BridgeActivity {
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
 }
}
""")
