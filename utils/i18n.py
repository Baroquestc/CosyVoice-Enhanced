from typing import List
import json
import logging
from pathlib import Path
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = Path(ROOT_DIR) / "config"

class I18n:
    """Internationalization manager for multi-language support"""
    
    def __init__(self):
        self.current_lang = "en"
        self.translations = {}
        self.load_translations()
    
    def load_translations(self):
        """Load translation files"""
        config_dir = CONFIG_DIR
        config_dir.mkdir(exist_ok=True)
        
        # Default translations
        default_translations = {
            "en": {
                "title": "🎵 CosyVoice TTS Studio",
                "subtitle": "Advanced Text-to-Speech with Voice Cloning & Natural Language Control",
                "current_model": "Current Model",
                "model_management": "Model Management",
                "available_models": "Available Models",
                "load_model": "Load Model",
                "unload_model": "Unload Model",
                "model_status": "Model Status",
                "loaded": "Loaded",
                "not_loaded": "Not Loaded",
                "text_input": "Text to Synthesize",
                "inference_mode": "Inference Mode",
                "operation_steps": "Operation Steps",
                "pretrained_voice": "Pretrained Voice",
                "voice_cloning_3s": "3s Voice Cloning",
                "cross_lingual": "Cross-lingual Cloning",
                "natural_control": "Natural Language Control",
                "select_voice": "Select Voice",
                "streaming": "Streaming Mode",
                "speed_control": "Speed Control",
                "random_seed": "Random Seed",
                "generate_seed": "Generate Random Seed",
                "prompt_audio_file": "Prompt Audio File",
                "record_prompt": "Record Prompt Audio",
                "prompt_text": "Prompt Text",
                "instruct_text": "Instruction Text",
                "auto_transcribe": "Auto-transcribe prompt audio",
                "transcription_status": "Transcription Status",
                "generate_audio": "🎵 Generate Audio",
                "generated_audio": "Generated Audio",
                "settings": "Settings",
                "language": "Language",
                "api_settings": "API Settings",
                "transcription_url": "Transcription API URL",
                "api_key": "API Key",
                "save_settings": "Save Settings",
                "loading": "Loading...",
                "error": "Error",
                "success": "Success",
                "warning": "Warning",
                "info": "Info",
                # New keys for default text
                "default_tts_text": "I am the new generative speech model from Tongyi Lab, providing comfortable and natural speech synthesis capabilities.",
                "audio_configuration": "Audio Configuration",
                # Placeholders
                "placeholder_tts_text": "Enter the text you want to synthesize...",
                "placeholder_prompt_text": "Enter prompt text (should match prompt audio content)...",
                "placeholder_instruct_text": "Enter instruction text for natural language control...",
                "placeholder_api_key": "Enter your API key",
                "placeholder_api_url": "Enter transcription API URL",
                # Mode names for radio buttons
                "mode_pretrained_voice": "Pretrained Voice",
                "mode_voice_cloning": "3s Voice Cloning",
                "mode_cross_lingual": "Cross-lingual Cloning",
                "mode_natural_control": "Natural Language Control",
                # Operation steps
                "steps_pretrained_voice": "1. Select pretrained voice\n2. Click generate button",
                "steps_voice_cloning": "1. Upload prompt audio (max 30s)\n2. Enter prompt text\n3. Click generate button",
                "steps_cross_lingual": "1. Upload prompt audio\n2. Ensure synthesis text is different language\n3. Click generate button",
                "steps_natural_control": "1. Select pretrained voice\n2. Enter instruction text\n3. Click generate button",
                # Transcription messages
                "transcription_success": "Auto-transcribed: {text}...",
                "transcription_failed": "Transcription failed. Please check API settings or enter text manually.",
                "api_not_configured": "API key not configured. Please set API key in settings.",
                # Voice management tab
                "tts_tab": "Speech Synthesis",
                "voice_management_tab": "Voice Management",
                "register_voice": "Register Voice",
                "voice_name": "Voice Name",
                "voice_upload": "Upload Voice Sample",
                "register_button": "Register Voice",
                "voice_list": "Registered Voices",
                "delete_voice": "Delete",
                "system_voice": "System Voice",
                "custom_voice": "Custom Voice",
                "voice_registered": "Voice successfully registered",
                "voice_deleted": "Voice successfully deleted",
                "voice_exists": "Voice already exists. Please delete it first or use a different name.",
                "voice_protected": "Cannot delete system voice",
                "no_audio": "Please upload an audio file",
                "no_voice_name": "Please enter a voice name",
                "no_model_loaded": "Please load a model first",
                "placeholder_voice_name": "Enter voice name...",
                "voice_management": "Voice Management",
                "refresh": "Refresh Voices",
                "status": "Status",
                # Voice management disabled messages
                "voice_management_disabled": "Voice Management Disabled",
                "voice_management_disabled_message": "Voice management is disabled when running in fixed model mode."
            },
            "zh": {
                "title": "🎵 CosyVoice 语音合成工作室",
                "subtitle": "先进的文本转语音技术，支持声音克隆和自然语言控制",
                "current_model": "当前模型",
                "model_management": "模型管理",
                "available_models": "可用模型",
                "load_model": "加载模型",
                "unload_model": "卸载模型",
                "model_status": "模型状态",
                "loaded": "已加载",
                "not_loaded": "未加载",
                "text_input": "输入合成文本",
                "inference_mode": "推理模式",
                "operation_steps": "操作步骤",
                "pretrained_voice": "预训练音色",
                "voice_cloning_3s": "3秒极速复刻",
                "cross_lingual": "跨语种复刻",
                "natural_control": "自然语言控制",
                "select_voice": "选择音色",
                "streaming": "流式模式",
                "speed_control": "速度控制",
                "random_seed": "随机种子",
                "generate_seed": "生成随机种子",
                "prompt_audio_file": "提示音频文件",
                "record_prompt": "录制提示音频",
                "prompt_text": "提示文本",
                "instruct_text": "指令文本",
                "auto_transcribe": "自动转录提示音频",
                "transcription_status": "转录状态",
                "generate_audio": "🎵 生成音频",
                "generated_audio": "生成的音频",
                "settings": "设置",
                "language": "语言",
                "api_settings": "API设置",
                "transcription_url": "转录API地址",
                "api_key": "API密钥",
                "save_settings": "保存设置",
                "loading": "加载中...",
                "error": "错误",
                "success": "成功",
                "warning": "警告",
                "info": "信息",
                # New keys for default text
                "default_tts_text": "我是来自通义实验室的新一代生成式语音大模型，提供舒适自然的语音合成能力。",
                "audio_configuration": "音频配置",
                # Placeholders
                "placeholder_tts_text": "请输入您想要合成的文本...",
                "placeholder_prompt_text": "请输入提示文本（应与提示音频内容匹配）...",
                "placeholder_instruct_text": "请输入自然语言控制指令...",
                "placeholder_api_key": "请输入您的API密钥",
                "placeholder_api_url": "请输入转录API地址",
                # Mode names for radio buttons
                "mode_pretrained_voice": "预训练音色",
                "mode_voice_cloning": "3秒极速复刻",
                "mode_cross_lingual": "跨语种复刻",
                "mode_natural_control": "自然语言控制",
                # Operation steps
                "steps_pretrained_voice": "1. 选择预训练音色\n2. 点击生成按钮",
                "steps_voice_cloning": "1. 上传提示音频（最长30秒）\n2. 输入提示文本\n3. 点击生成按钮",
                "steps_cross_lingual": "1. 上传提示音频\n2. 确保合成文本为不同语言\n3. 点击生成按钮",
                "steps_natural_control": "1. 选择预训练音色\n2. 输入指令文本\n3. 点击生成按钮",
                # Transcription messages
                "transcription_success": "自动转录: {text}...",
                "transcription_failed": "转录失败。请检查API设置或手动输入文本。",
                "api_not_configured": "API密钥未配置。请在设置中设置API密钥。",
                # Voice management tab
                "tts_tab": "语音合成",
                "voice_management_tab": "音色管理",
                "register_voice": "注册音色",
                "voice_name": "音色名称",
                "voice_upload": "上传音色样本",
                "register_button": "注册音色",
                "voice_list": "已注册音色",
                "delete_voice": "删除",
                "system_voice": "系统音色",
                "custom_voice": "自定义音色",
                "voice_registered": "音色注册成功",
                "voice_deleted": "音色删除成功",
                "voice_exists": "音色已存在。请先删除它或使用不同的名称。",
                "voice_protected": "无法删除系统音色",
                "no_audio": "请上传音频文件",
                "no_voice_name": "请输入音色名称",
                "no_model_loaded": "请先加载模型",
                "placeholder_voice_name": "输入音色名称...",
                "voice_management": "音色管理",
                "refresh": "刷新音色",
                "status": "状态",
                # Voice management disabled messages
                "voice_management_disabled": "音色管理已禁用",
                "voice_management_disabled_message": "在固定模型模式下运行时，音色管理已禁用。"
            }
        }
        
        # Process each language
        for lang, default_trans in default_translations.items():
            lang_file = config_dir / f"{lang}.json"
            
            # Load existing translations or create new file
            if lang_file.exists():
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        existing_trans = json.load(f)
                    
                    # Check for missing keys and update if needed
                    updated = False
                    for key, value in default_trans.items():
                        if key not in existing_trans:
                            existing_trans[key] = value
                            updated = True
                    
                    # Save the updated translations if any keys were added
                    if updated:
                        print(f"Updating translation file {lang_file} with new keys")
                        with open(lang_file, 'w', encoding='utf-8') as f:
                            json.dump(existing_trans, f, ensure_ascii=False, indent=2)
                    
                    # Store the translations
                    self.translations[lang] = existing_trans
                    
                except Exception as e:
                    logging.error(f"Failed to process translation {lang_file}: {e}")
                    # If there's an error, use the default translations
                    self.translations[lang] = default_trans
            else:
                # Create new translation file
                print(f"Creating new translation file {lang_file}")
                with open(lang_file, 'w', encoding='utf-8') as f:
                    json.dump(default_trans, f, ensure_ascii=False, indent=2)
                self.translations[lang] = default_trans
    
    def get_text(self, key: str) -> str:
        """Get translated text"""
        return self.translations.get(self.current_lang, {}).get(key, key)
    
    def set_language(self, lang: str):
        """Set current language"""
        if lang in self.translations:
            self.current_lang = lang
    
    def get_available_languages(self) -> List[str]:
        """Get list of available languages"""
        return list(self.translations.keys())