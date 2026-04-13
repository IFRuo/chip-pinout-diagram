import os
import yaml
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_file: str = 'config.yaml'):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"Error loading config file: {e}")
                return self._get_default_config()
        else:
            # 配置文件不存在，创建默认配置
            default_config = self._get_default_config()
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            '画板': {
                '画板宽度': 1600,
                '画板高度': 1024,
                '画板背景色': '#555555'
            },
            '图例参数': {
                '图例图层': 10,
                '图例起始X坐标': 20,
                '图例起始Y坐标': 20,
                '每列图例项数量': 10,
                '图例项纵间距': 2,
                '图例列间距': 4,
                '图例项圆角': 3,
                '图例项高度': 20,
                '图例项宽度': 100,
                '图例字体大小': 14
            },
            '芯片主体参数': {
                '芯片文本图层': 5,
                '芯片标题字体大小': 22,
                '芯片标题字体': 'Fantasy',
                '芯片信息字体大小': 12,
                '芯片信息字体': 'Cursive',
                '芯片主体图层': 3,
                '芯片主体圆角半径': 10,
                '芯片主体边框宽度': 5,
                '芯片主体颜色': '#000000'
            },
            '焊盘': {
                'PID焊盘': {
                    'PID_焊盘图层': 2,
                    'PID焊盘编号字体大小': 8,
                    'PID焊盘编号字体': 'Cursive',
                    'PID_焊盘编号字体颜色': '#000000',
                    'PID_焊盘圆角': 2,
                    'PID焊盘宽度': 20,
                    'PID焊盘高度': 10,
                    'PID_边线宽度': 1,
                    'PID_边线颜色': '#000000',
                    'PID_焊盘颜色': '#cccccc',
                    'PID引脚与标签间距': 2,
                    'PID标签间距': 2
                },
                'PID中心焊盘': {
                    'PID_中心焊盘图层': 1,
                    'PID_中心焊盘圆角': 2,
                    'PID_中心焊盘宽度': 100,
                    'PID_中心焊盘高度': 100,
                    'PID_中心焊边线宽度': 0,
                    'PID_中心焊边线颜色': '#ffffff',
                    'PID_中心焊焊盘颜色': '#cccccc',
                    'PID_中心焊盘X偏移': 0,
                    'PID_中心焊盘Y偏移': 0
                },
                'QFN焊盘': {
                    'QFN_焊盘图层': 2,
                    'QFN焊盘编号字体大小': 8,
                    'QFN焊盘编号字体': 'Cursive',
                    'QFN_焊盘编号字体颜色': '#000000',
                    'QFN_焊盘圆角': 2,
                    'QFN焊盘宽度': 20,
                    'QFN焊盘高度': 10,
                    'QFN_边线宽度': 1,
                    'QFN_边线颜色': '#000000',
                    'QFN_焊盘颜色': '#cccccc',
                    'QFN引脚与标签间距': 2,
                    'QFN标签间距': 2
                },
                'QFN中心焊盘': {
                    'QFN_中心焊盘图层': 1,
                    'QFN_中心焊盘圆角': 2,
                    'QFN_中心焊盘宽度': 100,
                    'QFN_中心焊盘高度': 100,
                    'QFN_中心焊边线宽度': 0,
                    'QFN_中心焊边线颜色': '#ffffff',
                    'QFN_中心焊焊盘颜色': '#cccccc',
                    'QFN_中心焊盘X偏移': 0,
                    'QFN_中心焊盘Y偏移': 0
                },
                'QFP焊盘': {
                    'QFP_焊盘图层': 2,
                    'QFP焊盘编号字体大小': 8,
                    'QFP焊盘编号字体': 'Cursive',
                    'QFP_焊盘编号字体颜色': '#000000',
                    'QFP_焊盘圆角': 2,
                    'QFP焊盘宽度': 20,
                    'QFP焊盘高度': 10,
                    'QFP_边线宽度': 1,
                    'QFP_边线颜色': '#000000',
                    'QFP_焊盘颜色': '#cccccc',
                    'QFP引脚与标签间距': 2,
                    'QFP标签间距': 2
                },
                'QFP中心焊盘': {
                    'QFP_中心焊盘图层': 1,
                    'QFP_中心焊盘圆角': 2,
                    'QFP_中心焊盘宽度': 100,
                    'QFP_中心焊盘高度': 100,
                    'QFP_中心焊边线宽度': 0,
                    'QFP_中心焊边线颜色': '#ffffff',
                    'QFP_中心焊焊盘颜色': '#cccccc',
                    'QFP_中心焊盘X偏移': 0,
                    'QFP_中心焊盘Y偏移': 0
                }
            },
            '标签参数': {
                '标签图层': 4,
                '标签宽度比文本宽多少': 5,
                '标签高度': 15,
                '标签间距': 20
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config(self.config)
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config
