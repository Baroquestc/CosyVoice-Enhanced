# spk2info_utils.py
import torch
import os
import torchaudio.compliance.kaldi as kaldi
import torchaudio
import librosa

# Define global sample rate variables
high_sr = 22050
lower_sr = 16000

"""
load spk2info from path

Args:
    path (str): Path to the spk2info file.
"""
def load_spk2info(path):
    if os.path.exists(path) and os.path.isfile(path):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        spk2info = torch.load(path, map_location=device)
        return spk2info
    else:
        print(f"Warning: Could not load spk2info file from {path}, creating a new one.")
        spk2info = {}
        # ensure parent dir exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save(spk2info, path)
        return spk2info

"""
upgrade spk2info to new format which is support cosyvoice2 also compatible with cosyvoice

Args:
    input_path (str): Path to the input spk2info file.
    output_path (str): Path to the output spk2info file.
"""
def upgrade_cosyvoice_spk2info(input_path, output_path):
    spk2info = load_spk2info(input_path)
    print(f"extracted spk2info has {len(spk2info)} voices from {input_path}")
    for key in spk2info.keys():
        embedding = spk2info[key]['embedding']
        # add "llm_embedding" and "flow_embedding" to spk2info
        spk2info[key]['llm_embedding'] = embedding
        spk2info[key]['flow_embedding'] = embedding
        print(f"upgrade spk2info voice {key}")
    torch.save(spk2info, output_path)
    print(f"saved upgraded spk2info to {output_path}")

"""
print spk2info

Args:
    path (str): Path to the spk2info file.
"""
def print_spk2info(path):
    spk2info = load_spk2info(path)
    print(f"there are {len(spk2info)} voices in spk2info:")
    for key in spk2info.keys():
        #list all keys in spk2info[key]
        print(f"voice {key} has {len(spk2info[key])} keys: {spk2info[key].keys()}")

"""
upgrade all cosyvoice spk2info
"""
def upgrade_all_cosyvoice_spk2info():
    path_list = [
        './pretrained_models/CosyVoice-300M/spk2info.pt',
        './pretrained_models/CosyVoice-300M-SFT/spk2info.pt',
        './pretrained_models/CosyVoice-300M-Instruct/spk2info.pt',
        './pretrained_models/CosyVoice-300M-ttsfrd/spk2info.pt',
    ]
    for path in path_list:
        #if file not exist, skip
        if not os.path.exists(path):
            print(f"skip upgrade {path} because it not exist")
            continue
        #if file exist, upgrade
        upgrade_cosyvoice_spk2info(path, path)
        print(f"upgrade {path} done")
        print_spk2info(path)



### extract spkinfo contribution utils code from cosyvoice frontend.py

def postprocess(speech, top_db=60, hop_length=220, win_length=440):
    max_val = 0.8
    speech, _ = librosa.effects.trim(
        speech, top_db=top_db,
        frame_length=win_length,
        hop_length=hop_length
    )
    if speech.abs().max() > max_val:
        speech = speech / speech.abs().max() * max_val 
    zeros = torch.zeros(1, int(high_sr * 0.2))  
    #print(speech, zeros) 
    speech = torch.concat([speech, zeros], dim=1) 
    return speech

def load_audio(file_path):
    target_wav, sample_rate = torchaudio.load(file_path)
    # if target_wav is stereo, calculate average of two channels
    if target_wav.shape[0] == 2:
        # calculate average of two channels
        target_wav = target_wav.mean(dim=0, keepdim=True)
    # postprocess wav file to remove silence and normalize volume
    target_wav = postprocess(target_wav)
    return target_wav, sample_rate

def extract_spkinfo(speaker_audio_path: str, prompt_text: str, cosyvoice):
    # TODO: use cosyvoice add_zero_shot_spk and save_spkinfo method

    target_wav, sample_rate = load_audio(speaker_audio_path)
    prompt_text_token, prompt_text_token_len = cosyvoice.frontend._extract_text_token(prompt_text)
    target_wav_high = torchaudio.transforms.Resample(sample_rate, high_sr)(target_wav)
    target_wav_high = postprocess(target_wav_high)
    target_wav_lower = torchaudio.transforms.Resample(high_sr, lower_sr)(target_wav_high)
  
    speech_feat, speech_feat_len = cosyvoice.frontend._extract_speech_feat(target_wav_high)
    speech_token, speech_token_len = cosyvoice.frontend._extract_speech_token(target_wav_lower)
    
    # Determine the cosyvoice version by checking sample rate
    resample_rate = cosyvoice.sample_rate
    
    if resample_rate == 24000:
        # cosyvoice2, force speech_feat % speech_token = 2
        token_len = min(int(speech_feat.shape[1] / 2), speech_token.shape[1])
        speech_feat, speech_feat_len[:] = speech_feat[:, :2 * token_len], 2 * token_len
        speech_token, speech_token_len[:] = speech_token[:, :token_len], token_len
    embedding = cosyvoice.frontend._extract_spk_embedding(target_wav_lower)

    spk_info = {'prompt_text': prompt_text_token, 'prompt_text_len': prompt_text_token_len,
                    'llm_prompt_speech_token': speech_token, 'llm_prompt_speech_token_len': speech_token_len,
                    'flow_prompt_speech_token': speech_token, 'flow_prompt_speech_token_len': speech_token_len,
                    'prompt_speech_feat': speech_feat, 'prompt_speech_feat_len': speech_feat_len,
                    'llm_embedding': embedding, 'flow_embedding': embedding, 'embedding': embedding}
    return spk_info

def append_voice_to_spk2info(spk2info_path: str, spk_id: str, spk_info: dict):
    spk2info = load_spk2info(spk2info_path)
    if spk_id not in spk2info:
        spk2info[spk_id] = spk_info
        torch.save(spk2info, spk2info_path)
        print(f"append voice {spk_id} to {spk2info_path}")
    else:
        print(f"voice {spk_id} already exists in {spk2info_path}, if you want to overwrite it, please delete it first")

def delete_voice_from_spk2info(spk2info_path: str, spk_id: str):
    spk2info = load_spk2info(spk2info_path)
    if spk_id in spk2info:
        del spk2info[spk_id]
        torch.save(spk2info, spk2info_path)
        print(f"delete voice {spk_id} from {spk2info_path}")
    else:
        print(f"voice {spk_id} not found in {spk2info_path}")
