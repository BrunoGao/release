package com.example.ljwx_health_new

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import android.bluetooth.*
import android.util.Log

class MainActivity : FlutterActivity() {
    private val CHANNEL = "com.ljwx.health/native_events"
    private var methodChannel: MethodChannel? = null
    
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        
        methodChannel = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL)
        methodChannel?.setMethodCallHandler { call, result ->
            when (call.method) {
                "flutterReady" -> {
                    Log.d("MainActivity", "Flutter准备接收原生事件")
                    result.success(true)
                }
                else -> result.notImplemented()
            }
        }
        
        Log.d("MainActivity", "MethodChannel已设置，等待FlutterBluePlus事件")
    }
}
