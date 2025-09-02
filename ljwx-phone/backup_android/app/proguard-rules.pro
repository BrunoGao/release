# Flutter wrapper
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.** { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }

# Keep your application classes that will be used in Flutter
-keep class com.example.ljwx_health.** { *; }

# Keep Bluetooth related classes
-keep class com.polidea.** { *; }
-keep class com.polidea.rxandroidble2.** { *; }

# Keep Gson classes
-keep class * extends com.google.gson.TypeAdapter
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonSerializer
-keep class * implements com.google.gson.JsonDeserializer 