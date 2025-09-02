import 'dart:io';
import 'package:flutter/foundation.dart';
import '../global.dart' as global; //引入全局变量

/// MAC地址工具类 #MAC地址工具类
class MacAddressUtil {
  static final MacAddressUtil i = MacAddressUtil._();
  MacAddressUtil._();
  
  /// 保存MAC地址到文件 #保存MAC地址
  void saveLastConnectedMAC(String mac) {
    if (mac.isEmpty || mac.contains('XX:') || mac.contains('xx:')) return;
    
    try {
      final file = File('${global.bleLogFile}.mac');
      file.writeAsStringSync(mac);
      debugPrint('已保存MAC地址到文件: $mac');
    } catch (e) {
      debugPrint('保存MAC地址时出错: $e');
    }
  }
  
  /// 加载MAC地址从文件 #加载MAC地址
  String loadLastConnectedMAC() {
    try {
      String savedMAC = '';
      
      // 尝试从文件中读取
      final file = File('${global.bleLogFile}.mac');
      if (file.existsSync()) {
        savedMAC = file.readAsStringSync().trim();
        if (savedMAC.isNotEmpty) {
          debugPrint('从文件加载MAC地址: $savedMAC');
          return savedMAC;
        }
      }
    } catch (e) {
      debugPrint('加载MAC地址时出错: $e');
    }
    
    return '';
  }
  
  /// 检查MAC地址是否不完整 #检查不完整MAC地址
  bool isMacAddressIncomplete(String address) {
    // 检查是否MAC地址格式，但只有部分字段有效
    RegExp macPattern = RegExp(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$');
    if (!macPattern.hasMatch(address)) return false;
    
    // 检测是否有XX占位符
    return address.contains('XX:') || address.contains('xx:');
  }
  
  /// 从日志提取完整MAC地址 #提取完整MAC地址
  String findFullMacAddress(String partialMac) {
    try {
      // 获取最后两个字段作为匹配依据
      List<String> macParts = partialMac.split(':');
      if (macParts.length != 6) return '';
      
      String lastTwoParts = '${macParts[4]}:${macParts[5]}';
      debugPrint('尝试使用MAC地址后缀匹配: $lastTwoParts');
      
      // 从日志信息中提取成功连接的MAC地址
      String logPattern = r'D/BluetoothGatt\(\s*\d+\): onClientConnectionState\(\) - .* connected=true device=([0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})';
      RegExp logRegex = RegExp(logPattern);
      
      try {
        // 尝试读取日志文件
        String logContent = '';
        try {
          logContent = File(global.bleLogFile).readAsStringSync();
        } catch (e) {
          debugPrint('读取日志文件失败: $e');
        }
        
        // 在日志中查找匹配的MAC地址
        Iterable<Match> matches = logRegex.allMatches(logContent);
        for (Match match in matches) {
          String foundMac = match.group(1) ?? '';
          if (foundMac.isNotEmpty && foundMac.endsWith(lastTwoParts)) {
            debugPrint('在日志中找到匹配的完整MAC地址: $foundMac');
            return foundMac;
          }
        }
      } catch (e) {
        debugPrint('查找日志中的MAC地址时出错: $e');
      }
      
      return '';
    } catch (e) {
      debugPrint('查找完整MAC地址时出错: $e');
      return '';
    }
  }
} 